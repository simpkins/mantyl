// Copyright (c) 2022, Adam Simpkins
#include "KeymapDB.h"

#include <class/hid/hid.h>

namespace mantyl {

KeymapDB::KeymapDB()
    : builtin_("default",
               {{
                   // Left Row 0
                   {HID_KEY_F1, 0},
                   {HID_KEY_F2, 0},
                   {HID_KEY_F3, 0},
                   {HID_KEY_F4, 0},
                   {HID_KEY_F5, 0},
                   {HID_KEY_F6, 0},
                   {HID_KEY_ALT_LEFT, 0},
                   {HID_KEY_NONE, 0},

                   // Left Row 1
                   {HID_KEY_APPLICATION, 0},
                   {HID_KEY_1, 0},
                   {HID_KEY_2, 0},
                   {HID_KEY_3, 0},
                   {HID_KEY_4, 0},
                   {HID_KEY_5, 0},
                   {HID_KEY_ESCAPE, 0},
                   {HID_KEY_ARROW_LEFT, 0},

                   // Left Row 2
                   {HID_KEY_PAUSE, 0},
                   {HID_KEY_Q, 0},
                   {HID_KEY_W, 0},
                   {HID_KEY_E, 0},
                   {HID_KEY_R, 0},
                   {HID_KEY_T, 0},
                   {HID_KEY_SCROLL_LOCK, 0},
                   {HID_KEY_BACKSPACE, 0},

                   // Left Row 3
                   {HID_KEY_CONTROL_LEFT, 0},
                   {HID_KEY_A, 0},
                   {HID_KEY_S, 0},
                   {HID_KEY_D, 0},
                   {HID_KEY_F, 0},
                   {HID_KEY_G, 0},
                   {HID_KEY_NONE, 0},
                   {HID_KEY_NONE, 0}, // Not connected

                   // Left Row 4
                   {HID_KEY_SHIFT_LEFT, 0},
                   {HID_KEY_Z, 0},
                   {HID_KEY_X, 0},
                   {HID_KEY_C, 0},
                   {HID_KEY_V, 0},
                   {HID_KEY_B, 0},
                   {HID_KEY_PAGE_UP, 0},
                   {HID_KEY_NONE, 0}, // Not connected

                   // Left Row 5
                   {HID_KEY_NONE, 0},
                   {HID_KEY_HOME, 0},
                   {HID_KEY_BACKSLASH, 0},
                   {HID_KEY_BRACKET_LEFT, 0},
                   {HID_KEY_MINUS, 0},
                   {HID_KEY_ENTER, 0},
                   {HID_KEY_GUI_LEFT, 0},
                   {HID_KEY_ARROW_UP, 0},

                   // Right Row 0
                   {HID_KEY_F12, 0},
                   {HID_KEY_F11, 0},
                   {HID_KEY_F10, 0},
                   {HID_KEY_F9, 0},
                   {HID_KEY_F8, 0},
                   {HID_KEY_F7, 0},
                   {HID_KEY_ALT_RIGHT, 0}, // thumb top center
                   {HID_KEY_INSERT, 0},    // thumb top left

                   // Right Row 1
                   {HID_KEY_GRAVE, 0},
                   {HID_KEY_0, 0},
                   {HID_KEY_9, 0},
                   {HID_KEY_8, 0},
                   {HID_KEY_7, 0},
                   {HID_KEY_6, 0},
                   {HID_KEY_NONE, 0},        // thumb center
                   {HID_KEY_ARROW_RIGHT, 0}, // thumb center left

                   // Right Row 2
                   {HID_KEY_SYSREQ_ATTENTION, 0},
                   {HID_KEY_P, 0},
                   {HID_KEY_O, 0},
                   {HID_KEY_I, 0},
                   {HID_KEY_U, 0},
                   {HID_KEY_Y, 0},
                   {HID_KEY_NUM_LOCK, 0},
                   {HID_KEY_DELETE, 0}, // thumb top right

                   // Right Row 3
                   {HID_KEY_CONTROL_RIGHT, 0},
                   {HID_KEY_SEMICOLON, 0},
                   {HID_KEY_L, 0},
                   {HID_KEY_K, 0},
                   {HID_KEY_J, 0},
                   {HID_KEY_H, 0},
                   {HID_KEY_NONE, 0},
                   {HID_KEY_NONE, 0}, // Not connected

                   // Right Row 4
                   {HID_KEY_SHIFT_RIGHT, 0},
                   {HID_KEY_APOSTROPHE, 0},
                   {HID_KEY_PERIOD, 0},
                   {HID_KEY_COMMA, 0},
                   {HID_KEY_M, 0},
                   {HID_KEY_N, 0},
                   {HID_KEY_PAGE_DOWN, 0},
                   {HID_KEY_NONE, 0}, // Not connected

                   // Right Row 5
                   {HID_KEY_NONE, 0},
                   {HID_KEY_END, 0},
                   {HID_KEY_SLASH, 0},
                   {HID_KEY_BRACKET_RIGHT, 0},
                   {HID_KEY_EQUAL, 0},
                   {HID_KEY_SPACE, 0},     // thumb bottom right
                   {HID_KEY_TAB, 0},       // thumb bottom middle
                   {HID_KEY_ARROW_DOWN, 0} // thumb bottom left
               }}) {}

} // namespace mantyl
