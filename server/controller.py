"""会话状态机：每个 device_id 一个 Session，处理消息并编排 STT/LLM/注入。"""
import asyncio
import json

from config import config
from editor import Editor
from history import History
from injector import get_foreground_window, get_injector, get_window_title
from llm import get_llm
from stt import get_stt


class Session:
    def __init__(self, device_id: str, send, history: History):
        self.device_id = device_id
        self.send = send
        self.history = history
        self.state = "idle"
        self.draft = ""
        self.injected_text = ""
        self.focus_hwnd = None
        self.focus_title = ""
        self.audio = bytearray()
        self.rec_intent = None  # "input" | "modify"
        self.send_count = 0
        self.stt = get_stt()
        self.editor = Editor(get_llm())
        self.injector = get_injector()

    async def reply_status(self, state: str, msg: str = "") -> None:
        await self.send(json.dumps({"type": "status", "state": state, "msg": msg}))

    async def reply_text(self, text: str, phase: str) -> None:
        await self.send(json.dumps({"type": "show_text", "text": text, "phase": phase}))

    async def handle(self, msg: dict) -> None:
        t = msg.get("type")
        if t == "audio_start":
            self.audio.clear()
            self.state = "rec_modify" if self.rec_intent == "modify" else "rec"
            await self.reply_status(self.state)
        elif t == "audio_end":
            await self._on_audio_end()
        elif t == "key":
            await self._on_key(msg.get("key"))

    async def on_audio(self, chunk: bytes) -> None:
        self.audio.extend(chunk)

    async def _on_audio_end(self) -> None:
        pcm = bytes(self.audio)
        self.audio.clear()
        if not pcm:
            await self.reply_status("idle")
            return
        await self.reply_status("thinking")
        try:
            text = await asyncio.to_thread(self.stt.transcribe, pcm)
        except Exception as exc:  # noqa: BLE001
            await self.reply_status("error", f"stt: {exc}")
            return

        if self.rec_intent == "modify" and self.draft:
            before = self.draft
            instruction = text
            try:
                after = await asyncio.to_thread(self.editor.apply_edit, before, instruction)
            except Exception as exc:  # noqa: BLE001
                await self.reply_status("error", f"edit: {exc}")
                return
            self.history.add_edit(self.device_id, before, instruction, after)
            self.draft = after
        else:
            self.draft = text

        self.rec_intent = None
        self.state = "draft"
        await self.reply_text(self.draft, "draft")
        await self.reply_status("draft")

    async def _on_key(self, key: str | None) -> None:
        if key in ("input_long", "modify_long"):
            self.rec_intent = "input" if key == "input_long" else "modify"
        elif key == "input_short":
            if self.state == "draft":
                await self._inject()
            elif self.state == "injected":
                await self._send_enter()
            else:
                await self.reply_status("idle")
        elif key == "undo":
            await self._undo()

    async def _inject(self) -> None:
        text = self.draft
        try:
            await asyncio.to_thread(self._do_inject, text)
        except Exception as exc:  # noqa: BLE001
            await self.reply_status("error", f"inject: {exc}")
            return
        self.state = "injected"
        await self.reply_text(text, "injected")
        await self.reply_status("injected")

    def _do_inject(self, text: str) -> None:
        self.focus_hwnd = get_foreground_window()
        self.focus_title = get_window_title(self.focus_hwnd)
        self.injector.type_text(text)
        self.injected_text = text

    async def _send_enter(self) -> None:
        await asyncio.to_thread(self.injector.press_enter)
        self.state = "sent"
        self.history.add(self.device_id, self.draft, self.injected_text, self.focus_title)
        await self.reply_text(self.injected_text, "sent")
        await self.reply_status("sent")
        self.draft = ""
        self.injected_text = ""
        self.focus_hwnd = None
        self.focus_title = ""
        self.state = "idle"

        # 每 N 条触发一次偏好总结（后台，不阻塞交互）
        self.send_count += 1
        if self.send_count >= config.preference_batch:
            self.send_count = 0
            asyncio.create_task(self._summarize_preferences())

    async def _summarize_preferences(self) -> None:
        try:
            await asyncio.to_thread(self.history.summarize_preferences, self.device_id)
        except Exception as exc:  # noqa: BLE001
            await self.reply_status("error", f"preference: {exc}")

    async def _undo(self) -> None:
        if self.state == "draft":
            self.draft = ""
            await self.reply_status("idle")
            self.state = "idle"
        elif self.state == "injected":
            ok = await asyncio.to_thread(self._do_undo)
            if not ok:
                await self.reply_status("error", "focus changed")
                return
            self.draft = self.injected_text
            self.injected_text = ""
            self.state = "draft"
            await self.reply_text(self.draft, "draft")
            await self.reply_status("draft")

    def _do_undo(self) -> bool:
        if self.focus_hwnd is not None and get_foreground_window() != self.focus_hwnd:
            return False
        self.injector.undo(len(self.injected_text))
        return True
