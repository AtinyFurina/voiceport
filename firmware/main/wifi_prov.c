// BLE 配网占位实现。待 ESP-IDF 编译验证（wifi_provisioning BLE + NVS + mDNS 发现）。
#include "wifi_prov.h"

#include "esp_log.h"

static const char *TAG = "wifi_prov";

char *wifi_prov_ensure_connected(void) {
    // TODO: NVS 读凭证 → 连网 → mDNS 发现服务端(server_id/host/port) → 返回 ws:// URI。
    ESP_LOGW(TAG, "wifi_prov 未实现（待 ESP-IDF 验证后补齐）");
    return NULL;
}
