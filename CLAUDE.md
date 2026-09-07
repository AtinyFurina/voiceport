# VoicePort（语音输入前端）- 项目记忆

## 硬约束（不可违背，最高优先级）

- **不要任何 Web GUI**：界面必须是**原生桌面 GUI**（PySide6/Qt 原生控件），禁止浏览器、pywebview、任何 HTML/CSS 渲染的界面。这条是用户明确钦定的。
- **交付 = 一个完整可运行的 exe**：服务端集成在主 exe 内（后台线程运行），**不要单独的 server exe**。
- **日志写文件**：`~/.passport/server.log`，不用 console 窗口。
- 不替换微软输入法、不污染 Win+V 剪贴板历史、不做完整输入法、不做应用选择器。

## 架构

```
设备(ESP32-C3 瘦终端) ──Wi-Fi WebSocket──▶ PC 主 exe（服务端后台线程）
  服务端: aiohttp(HTTP API + WS) → controller 状态机 → STT/LLM → SendInput 注入
```

- 服务端逻辑（已完成，28 pytest 通过）：`controller.py`、`stt.py`、`llm.py`、`editor.py`、`injector.py`、`history.py`、`provision.py`、`mdns_adv.py`、`ws_server.py`。
- 设备固件：`firmware/`（骨架 + 设计文档，等设备到货 + ESP-IDF 编译）。

## 设置页需求（GUI 内）

1. **服务控制**：启动、关闭、后台运行（托盘）、开机启动（注册表 Run 键）。
2. **偏好管理**：查看/管理 LLM 偏好总结。
3. **历史记录**：分**修改记录**和**输入记录**两类，分开显示。
4. **API 配置**：STT（讯飞/硅基流动）+ LLM（DeepSeek）密钥表单，存 `~/.passport/config.json`。

## 三键语义（设备端）

| 物理键 | 功能 |
|---|---|
| OK | 输入键：长按录音 / draft 短按注入 / injected 短按回车发送 |
| UP | 修改键：draft 长按语音修改 |
| DOWN | 撤回键：draft 丢弃草稿 / injected 删注入文本 / 长按重选服务端 |

## 关键事实（BSP 引脚/API 见 docs/notes.md）

- ESP32-C3 + ES8311 + ST7789 240x320 + 三键 ADC 分压。
- STT 默认讯飞（备选硅基流动 SenseVoice）；LLM = DeepSeek 官方 API。
- 注入主用 SendInput Unicode；TSF 仅作最后兜底（spike 已验证编译+IPC，瞬态激活切回是大工程）。
