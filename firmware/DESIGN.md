# 固件设计文档（firmware/）

> 代码骨架已写，本文档锁定剩余两块的实现方案：wifi_prov（配网 + 服务发现）与 display（UI）。
> 所有 ESP-IDF/NimBLE/LVGL API 待真实环境编译验证。

## 1. 架构概览

```
app_main.c（主循环 + 录音状态机）
  ├─ buttons.c   三键长短按（BSP bsp_button + iot_button 事件）
  ├─ audio.c     ES8311 录音（BSP bsp_audio，16k/16bit/mono 流式）
  ├─ protocol.c  JSON 组包（cJSON）
  ├─ ws_client.c WebSocket（esp_websocket_client，ws:// 明文）
  ├─ display.c   LVGL UI（BSP bsp_lvgl_init）
  └─ wifi_prov.c BLE 配网 + NVS 凭证 + mDNS 服务发现
```

## 2. wifi_prov.c 实现方案（关键）

### 2.1 流程

```
开机 → NVS 读凭证(ssid/password/server_id/pc_ip/pc_port)
  ├─ 有凭证 → 连 Wi-Fi → 重连 ws://pc_ip:pc_port（或 mDNS 按 server_id 重寻址）
  └─ 无凭证 → BLE GATT 配网模式（等待 PC provision.py 写特征值）
              → 收到凭证 → 存 NVS → 连 Wi-Fi → 连服务端
```

### 2.2 BLE GATT（自定义简化版，与 PC 端 provision.py 一致）

- 服务 UUID：`a3f0a5b1-0000-4a5b-9c1d-2e3f4a5b6c7d`
- 特征值：`-0001` ssid、`-0002` password、`-0003` pc_ip、`-0004` pc_port(uint16 LE)、`-0005` server_id、`-0006` status(读，0/1/2)
- 用 NimBLE（`CONFIG_BT_NIMBLE_ENABLED=y`），实现 GATT server。
- 设备只接受第一个 BLE 连接并锁定（防多电脑抢连）。
- 全部写完后：连 Wi-Fi → status 写 1（已连网）→ 停止广播，进入主流程。

### 2.3 NVS 键

| 键 | 值 |
|---|---|
| `wifi_ssid` / `wifi_pass` | Wi-Fi 凭证 |
| `server_id` / `pc_ip` / `pc_port` | 服务端绑定信息（上次连接优先） |
| `device_id` | 设备 UUID（首次生成） |

### 2.4 服务发现（重连兜底）

- 优先连 NVS 里的 `pc_ip:pc_port`。
- 失败 → mDNS 查询 `_passport._tcp.local`（TXT: server_id/host/port），按 `server_id` 匹配后重连。

## 3. display.c UI 设计

- 深色底、大字体草稿、状态色：idle 灰 / rec 红 / thinking 黄 / draft 蓝 / injected 绿 / sent 绿闪 / error 红 / choosing 蓝。
- **主视图**：顶部状态栏（状态 + Wi-Fi 图标），主体显示当前草稿/已输入文本（可滚动）。
- **服务端选择视图**（choosing 态）：列表显示「mDNS 在线 ∪ NVS 历史」，UP/DOWN 移动、OK 确认、撤回键取消。
- LVGL 单缓冲/局部刷新（C3 内存 ~400KB，避免全屏双缓冲）。

## 4. 待实现清单

- [ ] `wifi_prov.c`：NimBLE GATT server（自定义 6 特征值）+ NVS + Wi-Fi 连接 + mDNS 发现。
- [ ] `display.c`：LVGL 主视图 + 服务端选择视图（替换占位）。
- [ ] `app_main.c`：device_id 从 NVS 读/生成；choosing 态的服务端列表交互。
- [ ] 按键录音的松手检测已用 `bsp_button_read_mv()` 轮询（阈值 2500mV），需真机标定。
- [ ] 全部编译验证（ESP-IDF 5.x + 官方 ai-passport BSP）。
