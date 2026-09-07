# 当前要做的事

## 已完成（本轮）

- [x] PySide6 原生 GUI（`gui.py`）：侧边导航 + 4 页面，暗色现代样式（QSS）。
- [x] 设置页：服务控制（启动/关闭/后台托盘/开机启动）、API 配置、历史记录（输入+修改分开）、偏好管理。
- [x] history.py：新增「修改记录」表（edits）+ recent_edits 查询；recent 支持查全部。
- [x] controller.py：修改流程补记 edits。
- [x] 服务控制：开机启动（HKCU Run 键）、托盘（QSystemTrayIcon）、启动服务端（后台线程）。
- [x] 日志写文件（~/.passport/server.log）。
- [x] 打包 `passport.exe`（49MB，windowed 单 exe，原生 GUI + 服务端集成）。
- [x] 删除废弃 Web/Tkinter/pywebview 入口（webui.py/main.py/main_gui.py/config_gui.py）。
- [x] 28 pytest 通过 + 打包 exe 运行验证通过。

## 剩余（等设备/后续）

- [ ] 固件 `.bin` 编译（等 AI Passport 到货 + ESP-IDF 环境）。
- [ ] 真实设备端到端验收（配网 → 语音 → 注入 → 微信/DSH）。
- [ ] 真实 API key 配置后联调 STT/LLM。

## 注意

- 打包前先 `taskkill /IM passport.exe /F` + `taskkill /IM python.exe /F` 清残留，否则 dist 文件被占用报 PermissionError。
- 每次改动跑 `pytest -q`（28 通过）。
- 硬约束见 CLAUDE.md：**不要 Web GUI**、单 exe、日志写文件。
