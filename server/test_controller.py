"""controller.py 状态机测试：mock STT/LLM/注入/焦点，不真实调用。"""
import asyncio
import json

import controller
import history as history_mod


class FakeStt:
    def __init__(self, text="识别文本"):
        self.text = text

    def transcribe(self, pcm):
        return self.text


class FakeLlm:
    def chat(self, messages):
        return ""


class FakeEditor:
    def __init__(self):
        self.calls = []

    def apply_edit(self, draft, instruction):
        self.calls.append((draft, instruction))
        return draft + "（已改）"


class FakeInjector:
    def __init__(self):
        self.typed = []
        self.enters = 0
        self.undos = []

    def type_text(self, t):
        self.typed.append(t)

    def press_enter(self):
        self.enters += 1

    def undo(self, n):
        self.undos.append(n)


class Collect:
    def __init__(self):
        self.sent = []

    async def send(self, data):
        self.sent.append(json.loads(data))


def _setup(monkeypatch, tmp_path, stt_text="识别文本"):
    stt = FakeStt(stt_text)
    inj = FakeInjector()
    editor = FakeEditor()
    monkeypatch.setattr(controller, "get_stt", lambda: stt)
    monkeypatch.setattr(controller, "get_llm", lambda: FakeLlm())
    monkeypatch.setattr(controller, "Editor", lambda llm: editor)
    monkeypatch.setattr(controller, "get_injector", lambda: inj)
    monkeypatch.setattr(controller, "get_foreground_window", lambda: 123)
    monkeypatch.setattr(controller, "get_window_title", lambda hwnd: "测试窗口")

    coll = Collect()
    hist = history_mod.History(str(tmp_path / "db.sqlite"))
    sess = controller.Session("dev1", coll.send, hist)
    return sess, coll, hist, stt, inj, editor


async def _do_input(sess):
    await sess.handle({"type": "key", "key": "input_long"})
    await sess.handle({"type": "audio_start"})
    await sess.on_audio(b"\x00\x00" * 100)
    await sess.handle({"type": "audio_end"})


def _run(coro):
    asyncio.run(coro)


def test_input_flow(monkeypatch, tmp_path):
    sess, *_ = _setup(monkeypatch, tmp_path)

    async def drive():
        await _do_input(sess)
        assert sess.state == "draft"
        assert sess.draft == "识别文本"

    _run(drive())


def test_modify_flow(monkeypatch, tmp_path):
    sess, _, _, _, _, editor = _setup(monkeypatch, tmp_path)

    async def drive():
        await _do_input(sess)
        assert sess.draft == "识别文本"
        await sess.handle({"type": "key", "key": "modify_long"})
        await sess.handle({"type": "audio_start"})
        await sess.on_audio(b"\x00\x00" * 50)
        await sess.handle({"type": "audio_end"})
        assert sess.draft == "识别文本（已改）"
        assert editor.calls == [("识别文本", "识别文本")]

    _run(drive())


def test_inject_and_send(monkeypatch, tmp_path):
    sess, _, hist, _, inj, _ = _setup(monkeypatch, tmp_path)

    async def drive():
        await _do_input(sess)
        await sess.handle({"type": "key", "key": "input_short"})
        assert sess.state == "injected"
        assert inj.typed == ["识别文本"]

        await sess.handle({"type": "key", "key": "input_short"})
        assert inj.enters == 1
        assert sess.state == "idle"
        rows = hist.recent("dev1")
        assert len(rows) == 1
        assert rows[0][0] == "识别文本"  # draft_text
        assert rows[0][2] == "测试窗口"  # window_title

    _run(drive())


def test_undo_draft(monkeypatch, tmp_path):
    sess, *_ = _setup(monkeypatch, tmp_path)

    async def drive():
        await _do_input(sess)
        assert sess.state == "draft"
        await sess.handle({"type": "key", "key": "undo"})
        assert sess.state == "idle"
        assert sess.draft == ""

    _run(drive())


def test_undo_injected(monkeypatch, tmp_path):
    sess, _, _, _, inj, _ = _setup(monkeypatch, tmp_path)

    async def drive():
        await _do_input(sess)
        await sess.handle({"type": "key", "key": "input_short"})
        assert sess.state == "injected"
        await sess.handle({"type": "key", "key": "undo"})
        assert sess.state == "draft"
        assert inj.undos == [4]  # len("识别文本") == 4
        assert sess.draft == "识别文本"

    _run(drive())
