// 屏显（LVGL）占位实现。待 ESP-IDF + BSP 编译验证。
#include "display.h"

#include "bsp_display.h"
#include "esp_log.h"

static const char *TAG = "app_disp";

esp_err_t app_display_init(void) {
    esp_err_t e = bsp_display_init();
    if (e != ESP_OK) return e;
    // 待接入 bsp_lvgl_init() 与主视图/选择视图 UI（深色底、大字体草稿、状态色）。
    ESP_LOGI(TAG, "display ready (LVGL UI 待实现)");
    return ESP_OK;
}

void app_display_status(const char *state) { (void)state; }

void app_display_text(const char *text) { (void)text; }

void app_display_server_list(const char **names, int len, int selected) {
    (void)names; (void)len; (void)selected;
}
