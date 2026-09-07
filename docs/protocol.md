# 通信协议规范

## 1. 拓扑

```
设备(ESP32-C3) ──BLE 配网──▶ PC(服务端)
设备(ESP32-C3) ──Wi-Fi WebSocket──▶ PC(服务端，作 server)
设备(ESP32-C3) ◀──mDNS 发现── PC(服务端，广播 _passport._tcp)
```

- 设备作 WebSocket 客户端，主动连 `ws://<pc_ip>:<port>`。
- BLE 只用于首次配网/重新绑定，数据走 WebSocket。

## 2. BLE 配网 GATT（自定义简化版）

设备无 Wi-Fi 凭证或重新绑定时，广播配网服务。PC 用 `bleak` 写入特征值：

| 特征 | 方向 | 说明 |
|---|---|---|
| `ssid` | PC→设备 | UTF-8 Wi-Fi SSID |
| `password` | PC→设备 | UTF-8 密码 |
| `pc_ip` | PC→设备 | UTF-8 服务端局域网 IP |
| `pc_port` | PC→设备 | uint16，默认 8765 |
| `server_id` | PC→设备 | UTF-8 服务端 UUID |
| `status` | 设备→PC | 0=配网中 / 1=已连网 / 2=失败 |

配网 = 绑定（写入 server_id）。多电脑同时配网时设备只接受第一个 BLE 连接并锁定。

## 3. mDNS 服务发现

服务端广播 `_passport._tcp.local`，TXT 记录：`server_id`、`host`、`port`。

设备 mDNS 扫描用于：服务端列表展示 + IP 变更后按 server_id 重寻址。

## 4. WebSocket 消息

帧类型：JSON 文本帧（控制）+ 二进制帧（音频 PCM）。

### 4.1 设备 → 服务端

| type | payload |
|---|---|
| `hello` | `{"ver":"1.0","device_id":"<uuid>"}` |
| `audio_start` | `{}` |
| `audio_end` | `{}` |
| `key` | `{"key":"input_short\|input_long\|modify_long\|undo\|up\|down\|ok\|cancel"}` |
| `ping` | `{}` |

- 二进制帧：PCM 分片，16kHz / 16bit / mono / little-endian，约 640B~1KB。
- 录音流程：`audio_start` → 二进制 PCM 流 → `audio_end`（触发 STT）。

### 4.2 服务端 → 设备

| type | payload |
|---|---|
| `welcome` | `{"server_id":"<uuid>","host":"<hostname>"}` |
| `show_text` | `{"text":"...","phase":"draft\|injected\|sent"}` |
| `status` | `{"state":"idle\|rec\|rec_modify\|thinking\|draft\|injected\|sent\|choosing\|error\|provisioning\|disconnected","msg":"..."}` |
| `pong` | `{}` |

## 5. 交互状态机

```
开机 → 有凭证且有上次绑定 → 自动连上次（成功 → idle）
        ├─ 失败 → choosing（列表 = mDNS 在线 ∪ NVS 历史，上次连接优先）
        └─ 长按撤回键 → choosing
无凭证 → provisioning → 连网 → 绑定 → idle

idle
 ├─ 长按输入键 → rec → 松手 audio_end → thinking → draft
 ├─ draft 长按修改键 → rec_modify → STT 指令 + LLM 改稿 → draft（可多轮）
 ├─ draft 短按输入键 → 注入草稿 → injected
 ├─ injected 短按输入键 → 回车发送 → sent → idle
 ├─ injected 短按撤回键 → 删刚注入文本 → draft
 └─ draft 短按撤回键 → 丢弃草稿 → idle
```

- 录音上限 15s；<300ms 短按防误触。
- 撤回键在 idle 态无操作。
