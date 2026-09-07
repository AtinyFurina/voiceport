# 项目笔记 / 决策记录

## 硬件事实（FoloToy AI Passport，来自官方 BSP）

### 屏幕（ST7789P3 240x320，4-line SPI，SPI2_HOST）
- MOSI=9, SCLK=8, CS=1, DC=20, RST=-1（软复位）, BL=21（背光 LEDC）
- 出厂需反色（INVON），SPI mode 0

### 按键（3 键共用 ADC 引脚 GPIO0 = ADC1_CH0，分压区分）
| 键 | 分压 | 电压 | 窗口 mV |
|---|---|---|---|
| UP(上) | 0Ω | 0mV | 0~150 |
| DOWN(下) | 1k | ~300mV | 150~447 |
| OK(确定) | 2.2k | ~595mV | 447~1900 |
| 松开 | — | 3300mV | — |

- ⚠ 不能用内部上拉（45k 精度差，三档会重叠）

### I2C（ES8311 + CW2017 共用）
- SDA=10, SCL=7；ES8311 地址 0x18，CW2017 地址 0x63

### 音频（ES8311，I2S 全双工）
- MCLK=6, BCLK=5, WS=3, DOUT=2（播放）, DIN=4（录音）, PA_CTRL=-1

### BSP API
- `bsp_audio_init()` / `bsp_audio_set_format(hz,bits,ch)` / `bsp_audio_read/write(pcm,bytes)` / `bsp_audio_set_volume(%)`
- `bsp_button_init(cb,user)`；事件 PRESS/CLICK/DOUBLE/LONG；键 UP/DOWN/OK
- `bsp_display_init()` / `bsp_display_panel()` / `bsp_display_backlight(%)` / `bsp_lvgl_init()` / `bsp_lvgl_lock/unlock()`
- 音频坑：`esp_codec_dev_open()` 已打开时不会重配采样率，改格式必须先 close

## TSF spike 结论（A8）

- imekit 是**完整输入法框架**，README 明言 "not a text insertion library"。
- Windows backend = TSF（ITfInsertAtSelection），在 `InputMethodEvent::Activate` 时 commit。
- 用 imekit 注入 = 注册输入法 + 激活 + commit + 切回微软输入法（瞬态激活切换）。
- 编译前提：Rust msvc toolchain 需 VS Build Tools（提供 link.exe + Windows SDK）。

## A8 spike 实测结果（已验证）

- ✅ imekit v0.1.1 编译成功（Rust 1.98.1 + VS Build Tools 17.14.39，MSVC）。
- ✅ `InputMethod::new()` TSF 初始化成功，进入事件循环不报错。
- ✅ IPC 链路打通：本地 TCP 8799 收到文本 `"测试注入文本"`。
- ⚠️ 未验证：「激活时 commit」需人工把系统输入法切到 tsf-injector 后测。
- ⚠️ 未做：注册为系统输入法 + 程序化激活/切回微软输入法（imekit 只提供被激活后 commit，不提供激活/切回）。
- 🔑 Windows 坑：`TcpListener::set_nonblocking(true)` 会传染给 accept 出的 stream（read 报 os error 10035），需 `stream.set_nonblocking(false)` 恢复。

## 进度

- Phase A 服务端 A1-A7 完成，25 个 pytest 通过。
- A8 TSF spike 代码已写（tsf-injector/），等 VS Build Tools 编译。
- Phase B 固件：BSP 引脚/API 已调研，待装 ESP-IDF + 真实设备。

## 三键映射（本项目约定）

| 物理键 | 功能 |
|---|---|
| OK(确定) | 输入键：长按录音 / draft 短按注入 / injected 短按回车发送 |
| UP(上) | 修改键：draft 长按语音修改 |
| DOWN(下) | 撤回键：draft 丢弃草稿 / injected 删注入文本 / 长按重选服务端 |
