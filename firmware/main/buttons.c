// 按键状态机实现。基于官方 BSP 的 bsp_button（espressif__button 组件）。
#include "buttons.h"

#include "bsp_button.h"
#include "bsp_pins.h"
#include "esp_log.h"

static const char *TAG = "app_btn";

static key_ev_cb_t s_cb;
static void *s_user;
static volatile bool s_rec_held;  // 录音键（OK/UP）当前是否按住

static void on_bsp_event(bsp_btn_t btn, bsp_btn_ev_t ev, void *user) {
    (void)user;
    if (!s_cb) return;

    switch (btn) {
        case BSP_BTN_OK:
            if (ev == BSP_BTN_LONG) {
                s_rec_held = true;
                s_cb(KEY_EV_INPUT_PRESS, s_user);   // 输入键长按 → 开始录音
            } else if (ev == BSP_BTN_CLICK) {
                s_cb(KEY_EV_INPUT_SHORT, s_user);   // 输入键短按
            }
            break;
        case BSP_BTN_UP:
            if (ev == BSP_BTN_LONG) {
                s_rec_held = true;
                s_cb(KEY_EV_MODIFY_PRESS, s_user);  // 修改键长按 → 开始修改录音
            }
            break;
        case BSP_BTN_DOWN:
            if (ev == BSP_BTN_LONG) {
                s_cb(KEY_EV_RECHOOSE, s_user);      // 撤回键长按 → 重选服务端
            } else if (ev == BSP_BTN_CLICK) {
                s_cb(KEY_EV_UNDO, s_user);          // 撤回键短按
            }
            break;
    }
}

void app_buttons_init(key_ev_cb_t cb, void *user) {
    s_cb = cb;
    s_user = user;
    s_rec_held = false;
    ESP_ERROR_CHECK(bsp_button_init(on_bsp_event, NULL));
    ESP_LOGI(TAG, "buttons ready");
}

bool app_buttons_rec_held(void) {
    // 松开态电压约 3300mV，按住 OK(≈595mV)/UP(≈0mV) 远低于此。
    // 阈值 2500mV 作为「已松开」分界。
    int mv = bsp_button_read_mv();
    if (mv < 0) {
        // 读失败保守视为未按住（避免卡死在录音态）
        s_rec_held = false;
        return false;
    }
    bool held = mv < 2500;
    if (!held) s_rec_held = false;
    return held;
}
