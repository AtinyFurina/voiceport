// 固件入口：初始化 + 主循环编排 + 录音状态机。待 ESP-IDF 编译验证。
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "nvs_flash.h"

#include "audio.h"
#include "buttons.h"
#include "display.h"
#include "protocol.h"
#include "wifi_prov.h"
#include "ws_client.h"

static const char *TAG = "app";

// 按键回调运行于 iot_button 定时器任务，只置标志，主循环处理。
static volatile int s_ev = -1;

static void on_key(key_ev_t ev, void *user) {
    (void)user;
    s_ev = (int)ev;
}

static void send_text(char *json) {
    if (json) {
        if (ws_client_connected()) ws_client_send_text(json);
        free(json);
    }
}

// 录音循环：流式上行 PCM，直到松手或 15s 超时。
static void do_recording(int is_modify) {
    send_text(protocol_key(is_modify ? "modify_long" : "input_long"));
    send_text(protocol_audio_start());

    uint8_t buf[APP_AUDIO_CHUNK];
    const uint32_t max_ms = 15000;
    for (uint32_t elapsed = 0; elapsed < max_ms; elapsed += 20) {
        int n = app_audio_read(buf, sizeof(buf));
        if (n > 0 && ws_client_connected()) {
            ws_client_send_binary(buf, (size_t)n);
        }
        vTaskDelay(pdMS_TO_TICKS(20));
        if (!app_buttons_rec_held()) break;  // 松手
    }
    send_text(protocol_audio_end());
}

void app_main(void) {
    ESP_ERROR_CHECK(nvs_flash_init());

    app_buttons_init(on_key, NULL);
    if (app_audio_init() != ESP_OK) ESP_LOGE(TAG, "audio init failed");
    app_display_init();

    char *uri = wifi_prov_ensure_connected();
    if (!uri) {
        ESP_LOGE(TAG, "wifi provisioning failed");
        return;
    }
    ESP_LOGI(TAG, "connecting ws: %s", uri);
    ws_client_start(uri, NULL, NULL);
    free(uri);

    // TODO: device_id 从 NVS 读取或首次生成 UUID
    send_text(protocol_hello("passport-0001"));
    app_display_status("idle");

    for (;;) {
        int ev = s_ev;
        s_ev = -1;
        switch (ev) {
            case KEY_EV_INPUT_PRESS:
                app_display_status("rec");
                do_recording(0);
                app_display_status("thinking");
                break;
            case KEY_EV_INPUT_SHORT:
                send_text(protocol_key("input_short"));
                break;
            case KEY_EV_MODIFY_PRESS:
                app_display_status("rec_modify");
                do_recording(1);
                app_display_status("thinking");
                break;
            case KEY_EV_UNDO:
                send_text(protocol_key("undo"));
                break;
            case KEY_EV_RECHOOSE:
                app_display_status("choosing");
                // TODO: 服务端选择列表（mDNS 扫描 + NVS 历史 + UP/DOWN/OK 选择）
                break;
            default:
                break;
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
