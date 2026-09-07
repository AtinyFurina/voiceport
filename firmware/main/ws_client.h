// WebSocket 客户端封装（esp_websocket_client）。待 ESP-IDF 编译验证。
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"

// 收到服务端文本帧（JSON）时回调。
typedef void (*ws_text_cb_t)(const char *json_text, void *user);

// 连接服务端（ws://pc_ip:port）。断线自动重连由 esp_websocket_client 配置。
esp_err_t ws_client_start(const char *uri, ws_text_cb_t on_text, void *user);

esp_err_t ws_client_send_text(const char *json_text);
esp_err_t ws_client_send_binary(const uint8_t *data, size_t len);
bool ws_client_connected(void);
