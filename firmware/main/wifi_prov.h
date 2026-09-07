// BLE 配网占位头。待 ESP-IDF 编译验证（ble provisioning + NVS 凭证 + server_id 绑定）。
#pragma once

#include "esp_err.h"

// 检查 NVS 是否有 Wi-Fi 凭证；有则连网并返回连接后的服务端 URI（malloc，调用方 free）。
// 无凭证则进入 BLE 配网模式（阻塞直到配网完成），返回 NULL 表示失败。
char *wifi_prov_ensure_connected(void);
