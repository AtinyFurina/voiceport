// 屏显（LVGL）占位头。待 ESP-IDF + BSP 编译验证后实现主视图/服务端选择视图。
#pragma once

#include "esp_err.h"

// 初始化显示 + LVGL。
esp_err_t app_display_init(void);

// 更新状态显示（idle/rec/rec_modify/thinking/draft/injected/sent/choosing/error/...）。
void app_display_status(const char *state);

// 显示当前草稿/已输入文本。
void app_display_text(const char *text);

// 显示服务端选择列表（数组，len 个，selected 高亮）。
void app_display_server_list(const char **names, int len, int selected);
