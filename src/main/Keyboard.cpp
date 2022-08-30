// Copyright (c) 2022, Adam Simpkins
#include "Keyboard.h"

#include "Keypad.h"

#include <class/hid/hid.h>
#include <class/hid/hid_device.h>
#include <esp_log.h>
#include <tinyusb.h>

namespace {
const char *LogTag = "mantyl.keyboard";
}

namespace mantyl {

Keyboard::Keyboard(Keypad *left, Keypad *right) : left_{left}, right_{right} {
  left_->set_callback([this]() {
    send_report();
  });
  right_->set_callback([this]() {
    send_report();
  });
}

void Keyboard::send_report() {
  std::array<uint8_t, 6> keycodes = {};
  size_t keycode_idx = 0;
  uint8_t modifiers = 0;

  auto left_pressed = left_->get_pressed();
  for (uint8_t row = 0; row < Keypad::kMaxRows; ++row) {
    const auto row_bits = left_pressed[row];
    if (!row_bits) {
      continue;
    }
    for (uint8_t col = 0; col < Keypad::kMaxCols; ++col) {
      const auto is_pressed = (row_bits >> col) & 0x1;
      if (is_pressed) {
        const auto keycode = lookup_keycode(true, row, col);
        if (keycode != HID_KEY_NONE && keycode_idx < keycodes.size()) {
          keycodes[keycode_idx] = keycode;
          ++keycode_idx;
        }
      }
    }
  }

  // TODO: this tud_mounted() check seems racy, since we are running
  // on a different task than the main USB task.
  if (tud_mounted()) {
    // TODO: use UsbDevice::kbd_report_id_
    if (!tud_hid_keyboard_report(1, modifiers, keycodes.data())) {
      // TODO: tud_hid_keyboard_report() is asynchronous, and the send does not
      // complete immediately.  We can fail here if a previous send is still in
      // progress and we cannot claim the endpoint.
      //
      // In this case, we need to trigger the send attempt again later.
      ESP_LOGW(LogTag, "failed to send keyboard HID report");
    }
  }
}

uint8_t Keyboard::lookup_keycode(bool left, uint8_t row, uint8_t col) const {
  static std::array<uint8_t, 64> left_keymap{
      // Row 0
      HID_KEY_F1,
      HID_KEY_F2,
      HID_KEY_F3,
      HID_KEY_F4,
      HID_KEY_F5,
      HID_KEY_F6,
      HID_KEY_ALT_LEFT,
      HID_KEY_NONE,

      // Row 1
      HID_KEY_APPLICATION,
      HID_KEY_1,
      HID_KEY_2,
      HID_KEY_3,
      HID_KEY_4,
      HID_KEY_5,
      HID_KEY_ESCAPE,
      HID_KEY_ARROW_LEFT,

      // Row 2
      HID_KEY_PAUSE,
      HID_KEY_Q,
      HID_KEY_W,
      HID_KEY_E,
      HID_KEY_R,
      HID_KEY_T,
      HID_KEY_SCROLL_LOCK,
      HID_KEY_BACKSPACE,

      // Row 3
      HID_KEY_CONTROL_LEFT,
      HID_KEY_A,
      HID_KEY_S,
      HID_KEY_D,
      HID_KEY_F,
      HID_KEY_G,
      HID_KEY_NONE,
      HID_KEY_NONE, // Not connected

      // Row 4
      HID_KEY_SHIFT_LEFT,
      HID_KEY_Z,
      HID_KEY_X,
      HID_KEY_C,
      HID_KEY_V,
      HID_KEY_B,
      HID_KEY_PAGE_UP,
      HID_KEY_NONE, // Not connected

      // Row 5
      HID_KEY_NONE,
      HID_KEY_HOME,
      HID_KEY_BACKSLASH,
      HID_KEY_BRACKET_LEFT,
      HID_KEY_MINUS,
      HID_KEY_ENTER,
      HID_KEY_GUI_LEFT,
      HID_KEY_ARROW_UP,

      // Row 6
      HID_KEY_NONE, // Display left
      HID_KEY_NONE, // Display right
      HID_KEY_NONE, // Display up
      HID_KEY_NONE, // Display down
      HID_KEY_NONE, // Display press in
      HID_KEY_NONE, // NC
      HID_KEY_NONE, // NC
      HID_KEY_NONE, // NC

      // Row 7
      HID_KEY_NONE, // NC
      HID_KEY_NONE, // NC
      HID_KEY_NONE, // NC
      HID_KEY_NONE, // NC
      HID_KEY_NONE, // NC
      HID_KEY_NONE, // NC
      HID_KEY_NONE, // NC
      HID_KEY_NONE, // NC
  };

  unsigned int idx = (row * 8) + col;
  if (idx >= left_keymap.size()) {
      ESP_LOGE(LogTag, "keycode index %u OOB", idx);
  }
  return left_keymap[idx];
}

} // namespace mantyl
