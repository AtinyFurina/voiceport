"""文本注入抽象 + Backend A（SendInput Unicode / macOS CGEvent）。

- 只做文本注入：不碰剪贴板、不碰输入法。
- 回车/撤回等单键统一注入，两个平台共用语义。
- 焦点辅助函数供 controller 做注入前记录/撤回前校验。
"""
import ctypes
import platform
from abc import ABC, abstractmethod

from config import config

# --- Win32 结构体 ---
PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL),
    ]


class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_ushort),
    ]


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL),
    ]


class _InputUnion(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("u", _InputUnion)]


INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_RETURN = 0x0D
VK_BACK = 0x08


class Injector(ABC):
    @abstractmethod
    def type_text(self, text: str) -> None: ...

    @abstractmethod
    def press_enter(self) -> None: ...

    @abstractmethod
    def undo(self, count: int) -> None: ...


class SendInputInjector(Injector):
    """Backend A：SendInput + KEYEVENTF_UNICODE 逐 UTF-16 码元注入。"""

    @staticmethod
    def _utf16_units(text: str) -> list[int]:
        """把文本拆成 UTF-16 码元（emoji/生僻字会拆成代理对两个码元）。"""
        encoded = text.encode("utf-16-le")
        return [int.from_bytes(encoded[i : i + 2], "little") for i in range(0, len(encoded), 2)]

    def _send_key(self, vk: int = 0, scan: int = 0, flags: int = 0) -> None:
        extra = ctypes.c_ulong(0)
        ki = KeyBdInput(vk, scan, flags, 0, ctypes.pointer(extra))
        inp = Input(INPUT_KEYBOARD, _InputUnion(ki=ki))
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    def _unicode_char(self, code: int) -> None:
        self._send_key(scan=code, flags=KEYEVENTF_UNICODE)
        self._send_key(scan=code, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)

    def _key(self, vk: int) -> None:
        self._send_key(vk=vk)
        self._send_key(vk=vk, flags=KEYEVENTF_KEYUP)

    def type_text(self, text: str) -> None:
        for unit in self._utf16_units(text):
            if unit == 0x0A:  # LF -> 换行
                self.press_enter()
            else:
                self._unicode_char(unit)

    def press_enter(self) -> None:
        self._key(VK_RETURN)

    def undo(self, count: int) -> None:
        for _ in range(count):
            self._key(VK_BACK)


class MacInjector(Injector):
    """macOS 注入：Quartz CGEvent Unicode。需 pyobjc-framework-Quartz + 辅助功能权限。"""

    _RETURN_KEY = 36
    _BACKSPACE_KEY = 51

    def __init__(self):
        try:
            import Quartz  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("需要 pyobjc-framework-Quartz") from exc
        self._Q = __import__("Quartz")

    def _post_unicode(self, text: str, keydown: bool) -> None:
        Q = self._Q
        event = Q.CGEventCreateKeyboardEvent(None, 0, keydown)
        Q.CGEventKeyboardSetUnicodeString(event, len(text), text)
        Q.CGEventPost(Q.kCGHIDEventTap, event)

    def _press_key(self, keycode: int) -> None:
        Q = self._Q
        for down in (True, False):
            event = Q.CGEventCreateKeyboardEvent(None, keycode, down)
            Q.CGEventPost(Q.kCGHIDEventTap, event)

    def type_text(self, text: str) -> None:
        for ch in text:
            if ch == "\n":
                self.press_enter()
            else:
                self._post_unicode(ch, True)
                self._post_unicode(ch, False)

    def press_enter(self) -> None:
        self._press_key(self._RETURN_KEY)

    def undo(self, count: int) -> None:
        for _ in range(count):
            self._press_key(self._BACKSPACE_KEY)


def get_foreground_window() -> int:
    if platform.system() == "Windows":
        return int(ctypes.windll.user32.GetForegroundWindow())
    return 0


def get_window_title(hwnd: int) -> str:
    if platform.system() != "Windows" or not hwnd:
        return ""
    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def get_injector() -> Injector:
    if config.inject_backend == "tsf" and platform.system() == "Windows":
        from injectors.tsf import TsfInjector  # 延迟导入，A8 实现

        return TsfInjector()
    if platform.system() == "Darwin":
        return MacInjector()
    return SendInputInjector()
