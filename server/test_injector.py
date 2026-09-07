"""injector.py 单元测试：验证逻辑，不触发真实 SendInput。"""
import injector


def test_utf16_units_plain():
    assert injector.SendInputInjector._utf16_units("abc") == [0x61, 0x62, 0x63]


def test_utf16_units_surrogate():
    # 😀 = U+1F600 -> 代理对 D83D DE00
    assert injector.SendInputInjector._utf16_units("a😀") == [0x61, 0xD83D, 0xDE00]


def test_type_text_newline_uses_enter(monkeypatch):
    inj = injector.SendInputInjector()
    calls = []
    monkeypatch.setattr(inj, "_unicode_char", lambda c: calls.append(("char", c)))
    monkeypatch.setattr(inj, "press_enter", lambda: calls.append(("enter",)))
    inj.type_text("ab\ncd")
    assert calls == [
        ("char", 0x61),
        ("char", 0x62),
        ("enter",),
        ("char", 0x63),
        ("char", 0x64),
    ]


def test_press_enter(monkeypatch):
    inj = injector.SendInputInjector()
    calls = []
    monkeypatch.setattr(inj, "_key", lambda vk: calls.append(vk))
    inj.press_enter()
    assert calls == [injector.VK_RETURN]


def test_undo_count(monkeypatch):
    inj = injector.SendInputInjector()
    calls = []
    monkeypatch.setattr(inj, "_key", lambda vk: calls.append(vk))
    inj.undo(3)
    assert calls == [injector.VK_BACK, injector.VK_BACK, injector.VK_BACK]
