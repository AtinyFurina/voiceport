// 按键状态机：把 BSP 三键事件映射为语音输入前端的语义。
//
// 物理键（见 docs/notes.md）：
//   OK  = 输入键（长按录音 / 短按注入或回车发送）
//   UP  = 修改键（长按语音修改）
//   DOWN= 撤回键（短按撤回 / 长按重选服务端）
//
// 关键：BSP 只给 LONG_PRESS_START（长按开始），没有松手事件。
// 录音的「松手停止」由 app 主循环轮询 bsp_button_read_mv() 检测松开态实现。
#pragma once

#include <stdbool.h>
#include <stdint.h>

// 我们自己的按键语义事件（跨模块使用）
typedef enum {
    KEY_EV_INPUT_PRESS,   // 输入键按下（开始录音）
    KEY_EV_INPUT_SHORT,   // 输入键短按（注入/回车，由服务端按状态机判定）
    KEY_EV_MODIFY_PRESS,  // 修改键按下（开始修改录音）
    KEY_EV_UNDO,          // 撤回键短按
    KEY_EV_RECHOOSE,      // 撤回键长按（重选服务端）
} key_ev_t;

typedef void (*key_ev_cb_t)(key_ev_t ev, void *user);

// 初始化按键，回调运行于 iot_button 定时器任务（勿阻塞）。
void app_buttons_init(key_ev_cb_t cb, void *user);

// 供主循环轮询：当前是否有录音键按住（OK 或 UP 仍按住）。用于录音松手检测。
// 返回 true = 仍按住；false = 已松开。
bool app_buttons_rec_held(void);
