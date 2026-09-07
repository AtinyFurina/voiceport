// 控制帧组包实现。待 ESP-IDF 编译验证（cJSON API 与头文件名按实际版本核对）。
#include "protocol.h"

#include <stdlib.h>
#include "cJSON.h"

static char *dump(cJSON *obj) {
    char *s = cJSON_PrintUnformatted(obj);
    cJSON_Delete(obj);
    return s;
}

char *protocol_hello(const char *device_id) {
    cJSON *o = cJSON_CreateObject();
    cJSON_AddStringToObject(o, "type", "hello");
    cJSON_AddStringToObject(o, "ver", "1.0");
    cJSON_AddStringToObject(o, "device_id", device_id);
    return dump(o);
}

char *protocol_key(const char *key) {
    cJSON *o = cJSON_CreateObject();
    cJSON_AddStringToObject(o, "type", "key");
    cJSON_AddStringToObject(o, "key", key);
    return dump(o);
}

char *protocol_audio_start(void) {
    cJSON *o = cJSON_CreateObject();
    cJSON_AddStringToObject(o, "type", "audio_start");
    return dump(o);
}

char *protocol_audio_end(void) {
    cJSON *o = cJSON_CreateObject();
    cJSON_AddStringToObject(o, "type", "audio_end");
    return dump(o);
}

char *protocol_ping(void) {
    cJSON *o = cJSON_CreateObject();
    cJSON_AddStringToObject(o, "type", "ping");
    return dump(o);
}
