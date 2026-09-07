// WebSocket 客户端实现（esp_websocket_client）。待 ESP-IDF 编译验证。
#include "ws_client.h"

#include <string.h>
#include "esp_log.h"
#include "esp_websocket_client.h"

static const char *TAG = "ws";

static esp_websocket_client_handle_t s_client;
static ws_text_cb_t s_on_text;
static void *s_user;

static void ws_event_handler(void *arg, esp_event_base_t base, int32_t id, void *data) {
    (void)arg; (void)base;
    esp_websocket_event_data_t *ev = (esp_websocket_event_data_t *)data;
    switch (id) {
        case WEBSOCKET_EVENT_CONNECTED:
            ESP_LOGI(TAG, "connected");
            break;
        case WEBSOCKET_EVENT_DISCONNECTED:
            ESP_LOGW(TAG, "disconnected");
            break;
        case WEBSOCKET_EVENT_DATA:
            if (ev->op_code == 0x01 /* text */ && s_on_text) {
                s_on_text((const char *)ev->data_ptr, s_user);
            }
            break;
        default:
            break;
    }
}

esp_err_t ws_client_start(const char *uri, ws_text_cb_t on_text, void *user) {
    s_on_text = on_text;
    s_user = user;

    esp_websocket_client_config_t cfg = {
        .uri = uri,
        .reconnect_timeout_ms = 3000,
        .network_timeout_ms = 5000,
    };
    s_client = esp_websocket_client_init(&cfg);
    if (!s_client) return ESP_FAIL;

    esp_websocket_register_events(s_client, WEBSOCKET_EVENT_ANY, ws_event_handler, NULL);
    return esp_websocket_client_start(s_client);
}

esp_err_t ws_client_send_text(const char *json_text) {
    if (!s_client) return ESP_ERR_INVALID_STATE;
    int n = esp_websocket_client_send_text(s_client, json_text, strlen(json_text), portMAX_DELAY);
    return n > 0 ? ESP_OK : ESP_FAIL;
}

esp_err_t ws_client_send_binary(const uint8_t *data, size_t len) {
    if (!s_client) return ESP_ERR_INVALID_STATE;
    int n = esp_websocket_client_send_bin(s_client, (const char *)data, len, portMAX_DELAY);
    return n > 0 ? ESP_OK : ESP_FAIL;
}

bool ws_client_connected(void) {
    return s_client && esp_websocket_client_is_connected(s_client);
}
