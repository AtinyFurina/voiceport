idf_component_register(
    SRCS
        "app_main.c"
        "buttons.c"
        "audio.c"
        "ws_client.c"
        "protocol.c"
        "display.c"
        "wifi_prov.c"
    INCLUDE_DIRS "."
    REQUIRES
        nvs_flash
        esp_wifi
        esp_netif
        esp_websocket_client
        esp-tls
        mdns
        cjson
        json
)

# BSP 组件（官方 ai-passport components/bsp）
# 以 managed_components 或 EXTRA_COMPONENT_DIRS 引入
