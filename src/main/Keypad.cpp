// Copyright (c) 2022, Adam Simpkins
#include "Keypad.h"

#include <esp_check.h>

#include <cinttypes>

namespace {
const char *LogTag = "mantyl.keypad";
}

namespace mantyl {

esp_err_t Keypad::init() {
  if (rows_ > kMaxRows || columns_ > kMaxCols) {
    ESP_LOGE(LogTag, "too many keypad rows/columns for SX1509");
    return ESP_ERR_INVALID_ARG;
  }

  auto rc = sx1509_.init();
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to initialize SX1509");

  rc = sx1509_.configure_keypad(rows_, columns_);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure SX1509 keypad");

  initialized_ = true;
  return ESP_OK;
}

int8_t Keypad::get_row(uint16_t value) {
  const auto row_bits = (value & 0xff);
  // TODO: We can probably use clz to make this faster.

  for (uint8_t row_idx = 0; row_idx < 8; ++row_idx) {
    if (row_bits == (1 << row_idx)) {
      return row_idx;
    }
  }

  return -1;
}

void Keypad::scan() {
  if (!initialized_) {
    // TODO: Periodically try to re-initialize the keypad.
    // The right keypad can be unplugged, and we want to recognize it again if
    // it is plugged back in.

    // make sure we yield to the idle thread to avoid watchdog failures
    vTaskDelay(1);
    return; // DISCONNECTED;
  }

  const auto int_value = sx1509_.read_interrupt();
  if (int_value == 1) {
    ++noint_count_;
    if (noint_count_ == 4) {
      ESP_LOGI(LogTag, "no int timeout");
      on_timeout();
    }
    vTaskDelay(1);
    return;
  }
  on_interrupt();
}

void Keypad::on_interrupt() {
  const auto read_result = sx1509_.read_keypad();
  if (read_result.has_error()) {
    // TODO:
    // - mark all keys unpressed
    // - indicate that the device is uninitialized and needs to be reset
    // - install timer to periodically attempt to re-initialize
    if (read_result.error() != last_err_) {
      ESP_LOGE(LogTag,
               "keypad read error: %s",
               esp_err_to_name(read_result.error()));
    }
    last_err_ = read_result.error();
    return;
  }
  last_err_ = ESP_OK;

  const auto key_data = read_result.value();
  const auto row = get_row(key_data);
  if (row < 0 || row >= rows_) {
    // The row should only be 0 if we performed a read when the interrupt pin
    // was not actually active.
    //
    // We don't expect to read a row value greater than rows_ unless we
    // configured the chip incorrectly.  (Although technically the chip doesn't
    // support fewer than 2 rows, so if rows_ is 1 it would still attempt to
    // scan 2 rows.)
    ESP_LOGE(LogTag,
             "read bad row data from keypad %#04x: %#x",
             sx1509_.address(),
             key_data);
    return;
  }

  const auto cols = (key_data >> 8);

  // Clear all pressed keys between this row and the last row we have seen.
  while (true) {
    ++last_row_seen_;
    if (last_row_seen_ >= rows_) {
      last_row_seen_ = 0;
    }
    if (last_row_seen_ == row) {
      break;
    }
    update_row(last_row_seen_, 0);
  }

  // Now update this row
  update_row(row, cols);

  ++counter_;
  ESP_LOGD(LogTag,
           "%" PRIu64 " (%" PRIu64 ") row %d cols %02x\n",
           counter_,
           noint_count_,
           row,
           cols);
  noint_count_ = 0;
}

void Keypad::on_timeout() {
  // The SX1509 unfortunately does not notify us when no keys are pressed,
  // so we have to rely on a timeout when it has been more than 1 key scan
  // period without an interrupt active.
  for (uint8_t row = 0; row < rows_; ++row) {
    update_row(row, 0);
  }
}

void Keypad::update_row(uint8_t row, uint8_t cols) {
  const auto old_value = pressed_keys_[row];
  pressed_keys_[row] = cols;
  if (old_value == cols) {
    return;
  }

  // TODO: record presses and releases based on the changes to cols
  for (uint8_t col = 0; col < kMaxCols; ++col) {
    const auto old_pressed = (old_value >> col) & 0x1;
    const auto new_pressed = (cols >> col) & 0x1;
    if (old_pressed != new_pressed) {
      if (new_pressed) {
        printf("press: %d, %d\n", row, col);
      } else {
        printf("release: %d, %d\n", row, col);
      }
    }
  }
}

} // namespace mantyl
