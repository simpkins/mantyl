// Copyright (c) 2022, Adam Simpkins
#include "Keypad.h"

#include <esp_check.h>

#include <cinttypes>

namespace {
const char *LogTag = "mantyl.keypad";
}

namespace mantyl {

esp_err_t Keypad::init_common() {
  if (rows_ > kMaxRows || columns_ > kMaxCols) {
    ESP_LOGE(
        LogTag, "too many keypad rows/columns for %s SX1509", name_.c_str());
    return ESP_ERR_INVALID_ARG;
  }

  auto rc = sx1509_.init();
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "failed to initialize %s SX1509", name_.c_str());

  return ESP_OK;
}

esp_err_t Keypad::init() {
  auto rc = init_common();
  if (rc != ESP_OK) {
    return rc;
  }

  rc = sx1509_.configure_keypad(rows_, columns_);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "failed to configure %s SX1509 keypad", name_.c_str());

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

bool Keypad::is_interrupt_asserted() {
  const auto int_value = sx1509_.read_interrupt();
  return (int_value == 0);
}

std::chrono::milliseconds Keypad::tick(std::chrono::steady_clock::time_point now) {
  if (!initialized_) {
    // Periodically try to re-initialize the keypad.  The right keypad can be
    // unplugged, and we want to recognize it again if it is plugged back in.
    const auto time_since_last_init = now - last_scan_detected_;
    if (time_since_last_init < kReinitTimeout) {
      return kReinitTimeout -
             std::chrono::duration_cast<std::chrono::milliseconds>(
                 time_since_last_init);
    } else {
      ESP_LOGI(LogTag, "attempting to reinit %s keypad", name_.c_str());
      const auto init_rc = init();
      if (init_rc != ESP_OK) {
        // Reinit failed
        last_scan_detected_ = now;
        return kReinitTimeout;
      }
    }
  }

  const auto int_value = sx1509_.read_interrupt();
  if (int_value == 1) {
    // No scan key currently detected
    //
    // The SX1509 unfortunately does not notify us when no keys are pressed,
    // so we have to rely on a timeout when it has been more than 1 key scan
    // period without an interrupt active.
    if (num_pressed_ == 0) {
      // When nothing is pressed we can wait forever;
      // we will be woken up by the interrupt instead.
      return std::chrono::minutes(60);
    }
    const auto time_since_last_press = now - last_scan_detected_;
    if (time_since_last_press > kReleaseTimeout) {
      all_released();
      return std::chrono::minutes(60);
    }
    return kReleaseTimeout -
           std::chrono::duration_cast<std::chrono::milliseconds>(
               time_since_last_press);
  } else {
    last_scan_detected_ = now;
    return on_interrupt();
  }
}

std::chrono::milliseconds Keypad::on_interrupt() {
  const auto read_result = sx1509_.read_keypad();
  if (read_result.has_error()) {
    ESP_LOGE(LogTag,
             "%s keypad read error: %s",
             name_.c_str(),
             esp_err_to_name(read_result.error()));
    // Mark all keys unpressed
    all_released();
    // Indicate that we need to be reinitialized
    initialized_ = false;
    return kReinitTimeout;
  }

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
             "read bad row data from %s keypad: %#x",
             name_.c_str(),
             key_data);
    return kReleaseTimeout;
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

  ESP_LOGD(LogTag, "%s: row %d cols %02x\n", name_.c_str(), row, cols);
  return kReleaseTimeout;
}

void Keypad::all_released() {
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

  // Record presses and releases based on the changes to cols
  for (uint8_t col = 0; col < kMaxCols; ++col) {
    const auto old_pressed = (old_value >> col) & 0x1;
    const auto new_pressed = (cols >> col) & 0x1;
    if (old_pressed != new_pressed) {
      if (new_pressed) {
        ++num_pressed_;
        ESP_LOGI(LogTag, "%s press: %d, %d", name_.c_str(), row, col);
      } else {
        --num_pressed_;
        ESP_LOGI(LogTag, "%s release: %d, %d", name_.c_str(), row, col);
      }
    }
  }

  if (callback_) {
    callback_();
  }
}

} // namespace mantyl
