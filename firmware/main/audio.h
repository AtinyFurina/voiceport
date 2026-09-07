// 录音封装：ES8311 16kHz/16bit/mono 流式读取。
#pragma once

#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"

#define APP_AUDIO_HZ    16000
#define APP_AUDIO_BITS  16
#define APP_AUDIO_CH    1
#define APP_AUDIO_CHUNK 640  // 约 20ms @16kHz/16bit/mono（32B/ms）

// 初始化 codec + I2S 并配置录音格式。
esp_err_t app_audio_init(void);

// 读一块 PCM；返回实际读取字节数，<=0 表示无数据/失败。
int app_audio_read(uint8_t *buf, size_t max_bytes);
