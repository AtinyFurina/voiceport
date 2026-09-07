"""ws_server + controller 集成测试：aiohttp HTTP API + WebSocket 全链路。"""
import asyncio
import json

import aiohttp
from aiohttp import web

import controller
import history as history_mod
import ws_server


class FakeStt:
    def transcribe(self, pcm):
        return "识别文本"


class FakeLlm:
    def chat(self, messages):
        return ""


class FakeEditor:
    def apply_edit(self, draft, instruction):
        return draft


class FakeInjector:
    def __init__(self):
        self.typed = []

    def type_text(self, t):
        self.typed.append(t)

    def press_enter(self):
        pass

    def undo(self, n):
        pass


def test_http_api_and_ws_flow(monkeypatch, tmp_path):
    monkeypatch.setattr(controller, "get_stt", lambda: FakeStt())
    monkeypatch.setattr(controller, "get_llm", lambda: FakeLlm())
    monkeypatch.setattr(controller, "Editor", lambda llm: FakeEditor())
    monkeypatch.setattr(controller, "get_injector", lambda: FakeInjector())
    monkeypatch.setattr(controller, "get_foreground_window", lambda: 1)
    monkeypatch.setattr(controller, "get_window_title", lambda hwnd: "窗口")

    ws_server.history = history_mod.History(str(tmp_path / "db.sqlite"))

    async def scenario():
        app = web.Application()
        app.router.add_get("/ws", ws_server.ws_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]

        async with aiohttp.ClientSession() as client:
            # WebSocket 全链路
            async with client.ws_connect(f"ws://127.0.0.1:{port}/ws") as ws:
                await ws.send_str(json.dumps({"type": "hello", "device_id": "d1"}))
                welcome = json.loads((await ws.receive()).data)
                assert welcome["type"] == "welcome"

                await ws.send_str(json.dumps({"type": "key", "key": "input_long"}))
                await ws.send_str(json.dumps({"type": "audio_start"}))
                await ws.send_bytes(b"\x00\x00" * 100)
                await ws.send_str(json.dumps({"type": "audio_end"}))

                while True:
                    m = json.loads((await ws.receive()).data)
                    if m["type"] == "show_text":
                        assert m["text"] == "识别文本"
                        assert m["phase"] == "draft"
                        break

        await runner.cleanup()

    asyncio.run(scenario())
