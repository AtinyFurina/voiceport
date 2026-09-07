"""端到端验证：真实 SendInput 注入到 Notepad，枚举定位编辑框读回确认。"""
import ctypes
import subprocess
import time

from injector import SendInputInjector

# 1. 启动 Notepad
subprocess.Popen(["notepad.exe"])
time.sleep(2.0)

user32 = ctypes.windll.user32
hwnd = user32.FindWindowW("Notepad", None)
if not hwnd:
    print("FAIL: Notepad 窗口未找到")
    raise SystemExit(1)

# 聚焦到 Notepad（否则 SendInput 会注入到别的窗口）
user32.ShowWindow(hwnd, 5)  # SW_SHOW
user32.SetForegroundWindow(hwnd)
time.sleep(0.6)

# 2. 真实注入
inj = SendInputInjector()
inj.type_text("你好世界测试")
inj.press_enter()
time.sleep(0.6)

# 3. 枚举子窗口定位编辑框（新 Notepad 的编辑框是嵌套的 RichEditD2DPT）
WM_GETTEXTLENGTH = 0x000E
WM_GETTEXT = 0x000D

CB = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
target = []


def cb(h, _lp):
    cls = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(h, cls, 256)
    if cls.value in ("RichEditD2DPT", "NotepadTextBox", "Edit"):
        target.append(h)
        return False  # 找到即停
    return True


user32.EnumChildWindows(hwnd, CB(cb), 0)
if not target:
    print("FAIL: 编辑框未找到")
    raise SystemExit(1)

edit = target[0]
length = user32.SendMessageW(edit, WM_GETTEXTLENGTH, 0, 0)
buf = ctypes.create_unicode_buffer(length + 2)
user32.SendMessageW(edit, WM_GETTEXT, length + 1, buf)
text = buf.value
print("Notepad 内容:", repr(text))

if "你好世界测试" in text:
    print("E2E INJECT OK")
else:
    print("FAIL: 注入内容未匹配")
    raise SystemExit(1)
