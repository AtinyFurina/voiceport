# VoicePort 语音输入前端

把 FoloToy **AI Passport** 硬件改造成**语音输入前端**：按住说话 → STT 转文字 → 屏幕显示草稿 → 可语音修改 → 文本注入电脑当前输入框 → 再按一次回车发送。

- 不替换微软输入法、不污染 Win+V 剪贴板历史、不做完整输入法。
- 设备只负责「听、显、按键」，智能全在 PC 端。

## 功能

- 原生桌面 GUI（PySide6，暗色主题）：服务控制 / API 配置 / 历史记录（输入+修改）/ 偏好管理。
- 三键交互：输入键（长按录音/短按注入/再短按回车）、修改键（语音改稿）、撤回键。
- 服务端集成在单 exe 内（后台线程），日志写文件。
- 多设备：BLE 配网 + Wi-Fi WebSocket + mDNS 服务发现 + 服务端列表选择。
- 历史记录 + LLM（DeepSeek）偏好总结。

## 架构

```
设备(ESP32-C3 瘦终端) ──Wi-Fi WebSocket──▶ PC 服务端（后台线程）
  服务端: aiohttp(WS) → controller 状态机 → STT → LLM → 文本注入
```

- `server/`：PC 服务端 + GUI（Python 3.11+）。
- `firmware/`：ESP-IDF 固件（ESP32-C3 瘦终端）。
- `tsf-injector/`：TSF 注入服务（Rust/imekit，可选兜底）。

## 平台

- **Windows**：注入用 SendInput Unicode；打包 `VoicePort.exe`（PyInstaller onefile）。
- **macOS**：注入用 Quartz CGEvent Unicode；开机自启动用 LaunchAgent。

## 构建

```bash
cd server
pip install -r requirements.txt
python app.py            # 开发运行
python gen_icon.py       # 生成图标（需 Edge）
pyinstaller --onefile --windowed --name VoicePort --icon icon.ico --add-data "icon.png;." app.py
```

## 配置密钥

在 GUI 的「API 配置」页填写，保存到 `~/.passport/config.json`。STT 用讯飞（备选硅基流动 SenseVoice），LLM 用 DeepSeek 官方 API。

## 安装

- Windows：`winget install VoicePort`（或直接下载 release 的 `VoicePort.exe`）。
- 也可源码运行：`pip install -r requirements.txt && python app.py`。

## License

MIT
