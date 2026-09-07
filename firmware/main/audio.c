// 录音实现：基于官方 BSP 的 bsp_audio。
#include "audio.h"

#include "bsp_audio.h"
#include "esp_log.h"

static const char *TAG = "app_audio";

esp_err_t app_audio_init(void) {
    esp_err_t e = bsp_audio_init();
    if (e != ESP_OK) return e;
    e = bsp_audio_set_format(APP_AUDIO_HZ, APP_AUDIO_BITS, APP_AUDIO_CH);
    if (e != ESP_OK) {
        ESP_LOGE(TAG, "set format failed: %s", esp_err_to_name(e));
        return e;
    }
    ESP_LOGI(TAG, "audio ready (%uHz/%ubit/%uch)", APP_AUDIO_HZ, APP_AUDIO_BITS, APP_AUDIO_CH);
    return ESP_OK;
}

int app_audio_read(uint8_t *buf, size_t max_bytes) {
    esp_err_t e = bsp_audio_read(buf, max_bytes);
    if (e != ESP_OK) return 0;
    return (int)max_bytes;
}
