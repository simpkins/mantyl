// Copyright (c) 2022, Adam Simpkins
#include "Keyboard.h"

#include "App.h"
#include "keyboard/KeymapDB.h"
#include "keyboard/Keypad.h"
#include "mantyl_usb/hid.h"

#include <esp_log.h>

namespace {
const char *LogTag = "mantyl.keyboard";

void left_gpio_intr_handler(void*) {
  mantyl::App::get()->left_keypad_interrupt();
}

void right_gpio_intr_handler(void*) {
  mantyl::App::get()->right_keypad_interrupt();
}
} // namespace

namespace mantyl {

Keyboard::Keyboard(I2cMaster &i2c_left,
                   I2cMaster &i2c_right,
                   const KeymapDB &keymap_db)
    : keymap_db_{&keymap_db},
      left_{"left", i2c_left, 0x3e, GPIO_NUM_33, /*rows=*/7, /*cols=*/8},
      right_{"right", i2c_right, 0x3f, GPIO_NUM_11, /*rows=*/6, /*cols=*/8} {
  left_.set_callbacks(
      [this](uint8_t row, uint8_t col) { on_key_press(true, row, col); },
      [this](uint8_t row, uint8_t col) { on_key_release(true, row, col); });
  right_.set_callbacks(
      [this](uint8_t row, uint8_t col) { on_key_press(false, row, col); },
      [this](uint8_t row, uint8_t col) { on_key_release(false, row, col); });
}

esp_err_t Keyboard::early_init() {
  ESP_LOGV(LogTag, "attempting left SX1509 init:");
  auto rc = left_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized left key matrix");
  } else {
    ESP_LOGE(LogTag,
             "failed to initialize left key matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  ESP_LOGV(LogTag, "attempting right SX1509 init:");
  rc = right_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized right key matrix");
  } else {
    // Maybe the right key matrix is not connected.
    ESP_LOGE(LogTag,
             "failed to initialize right key matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  return ESP_OK;
}

bool Keyboard::should_boot_in_debug_mode() {
  return left_.is_interrupt_asserted();
}

esp_err_t Keyboard::kbd_task_init() {
  ESP_ERROR_CHECK(gpio_isr_handler_add(
      left_.interrupt_pin(), left_gpio_intr_handler, nullptr));
  ESP_ERROR_CHECK(gpio_isr_handler_add(
      right_.interrupt_pin(), right_gpio_intr_handler, nullptr));
  return ESP_OK;
}

std::chrono::milliseconds
Keyboard::tick(std::chrono::steady_clock::time_point now) {
  if (need_to_send_report_) {
    // If we still needed to send a report to indicate the state from a
    // previous tick, attempt to do so now.
    send_hid_report();
  }

  const auto left_timeout = left_.tick(now);
  const auto right_timeout = right_.tick(now);

  if (need_to_send_report_) {
    // If we failed to send a keyboard report, and still need to attempt to
    // send one, ask to be called back very soon.
    return std::chrono::milliseconds(1);
  }
  return std::min(left_timeout, right_timeout);
}

void Keyboard::generate_report(std::array<uint8_t, 6> &keycodes,
                               uint8_t &modifiers) {
  size_t keycode_idx = 0;

  for (bool is_left : {true, false}) {
    auto pressed = is_left ? left_.get_pressed() : right_.get_pressed();
    for (uint8_t row = 0; row < Keypad::kMaxRows; ++row) {
      const auto row_bits = pressed[row];
      if (!row_bits) {
        continue;
      }
      for (uint8_t col = 0; col < Keypad::kMaxCols; ++col) {
        const auto is_pressed = (row_bits >> col) & 0x1;
        if (is_pressed) {
          const auto info = keymap_db_->get_key(is_left, row, col);
          if (info.key == static_cast<uint8_t>(hid::Key::None) ||
              info.key == KeySpecial) {
            continue;
          }
          if (keycode_idx < keycodes.size()) {
            keycodes[keycode_idx] = info.key;
          }
          ++keycode_idx;
          modifiers |= info.modifiers;
        }
      }
    }
  }

  // If more keys are pressed then can be stored in keycodes, set all entries
  // to the ErrorRollOver code (0x01), defined in the HID Usage Tables 1.12
  if (keycode_idx > keycodes.size()) {
    for (size_t n = 0; n < keycodes.size(); ++n) {
      keycodes[n] = 0x01;
    }
  }
}

void Keyboard::on_key_press(bool is_left, uint8_t row, uint8_t col) {
  on_key_change(is_left, row, col, true);
}

void Keyboard::on_key_release(bool is_left, uint8_t row, uint8_t col) {
  on_key_change(is_left, row, col, false);
}

void Keyboard::on_key_change(bool is_left, uint8_t row, uint8_t col, bool press) {
  // Row 6 on the left keypad contains the directional
  // switch controlling the UI
  if (row == 6) {
    const auto action = static_cast<SpecialAction>(
        static_cast<uint8_t>(SpecialAction::UiLeft) + col);
    App::get()->on_special_action(action, press);
    return;
  }

  const auto info = keymap_db_->get_key(is_left, row, col);
  if (info.key == KeySpecial) {
    const auto action = static_cast<SpecialAction>(info.modifiers);
    App::get()->on_special_action(action, press);
    return;
  }

  // A normal key press or release
  send_hid_report();
}

void Keyboard::send_hid_report() {
  std::array<uint8_t, 6> keycodes = {};
  uint8_t modifiers = 0;
  generate_report(keycodes, modifiers);

  // TODO: re-enable this logic with my own custom USB stack
#if 0
  // Note: this code is buggy and racy.  The TinyUSB APIs on FreeRTOS seem to
  // have some designed-in concurrency problems.  The HID APIs do not
  // perform locking, and are not safe to call anywhere other than the TinyUSB
  // task.  Unfortunately, on FreeRTOS the tud_task() call blocks forever
  // waiting for events, and never returns, making it difficult to do any
  // user-defined work on this task.
  //
  // This code follows the behavior of the examples from TinyUSB and the
  // ESP-IDF, but is racy and can crash.  In particular, the TinyUSB task can
  // change the USB state between our call to tud_hid_ready() and the call to
  // tud_hid_keyboard_report().  If we end up calling tud_hid_keyboard_report()
  // when the device is not actually mounted, this will result in a crash.
  //
  // https://github.com/espressif/esp-idf/issues/9691
  need_to_send_report_ = true;
  if (tud_hid_ready()) {
    if (tud_hid_keyboard_report(
            OldUsbDevice::getKeyboardHidReportID(), modifiers, keycodes.data())) {
      need_to_send_report_ = false;
    } else {
      // tud_hid_keyboard_report() is asynchronous, and the send does not
      // complete immediately.  We can fail here if a previous send is still in
      // progress and we cannot claim the endpoint.
      //
      // Mark that we are out of sync and need to attempt to send another report
      // soon.
      ESP_LOGD(LogTag, "failed to send keyboard HID report");
    }
  }
#endif
}

} // namespace mantyl
