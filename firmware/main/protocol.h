// 控制帧 JSON 组包（cJSON）。返回 malloc 的字符串，调用方 free。
#pragma once

char *protocol_hello(const char *device_id);
char *protocol_key(const char *key);
char *protocol_audio_start(void);
char *protocol_audio_end(void);
char *protocol_ping(void);
