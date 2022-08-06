// Copyright (c) 2022, Adam Simpkins
#include "Keypad.h"

#include <esp_check.h>

#include <cinttypes>

namespace {
const char *LogTag = "mantyl.keypad";
}

namespace mantyl {

esp_err_t Keypad::init() {
  auto rc = sx1509_.init();
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to initialize SX1509");

  rc = sx1509_.configure_keypad(rows_, columns_);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure SX1509 keypad");

  initialized_ = true;
  return ESP_OK;
}

uint8_t Keypad::gen_key_index(uint16_t value) {
  // The value read from the SX1509 consists of two uint8_t values,
  // representing which column and row generated the key press event.
  // These unfortunately are not indices, but bitmasks with one bit per
  // column/row.  The column/row generating the event will be 0 and all other
  // columns/rows will be 1.  e.g., 11011111 -> row/column 5

  // TODO: can probably use clz
  return 0;
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

#if 0
  uint8_t first_key = 0;
  uint64_t pressed = 0;
  if (peeked_key_) {
    pressed |= (1 << peeked_key_);
  }

  while (true) {
    const auto read_result = sx1509_.read_keypad();
    if (read_result.has_error()) {
      pressed = 0;
      peeked_key_ = 0;
      // TODO: report all keys unpressed, mark keypad uninitialized
      return; // DISCONNECTED;
    }

    const auto key = read_result.value();
    if (key == 0) {
      // No keys are currently pressed.
      // End of the scan loop.
      peeked_key_ = 0;
      break;
    }
    if (key <= first_key) {
      peeked_key_ = key;
      break;
    }
  }
#else
  const auto int_value = sx1509_.read_int();
  if (int_value == 1) {
    ++noint_count_;
    if (noint_count_ % 30 == 0) {
      ESP_LOGI(LogTag, "no int");
    }
    vTaskDelay(1);
    return;
  }
  ESP_LOGI(LogTag, "int!!");
  const auto read_result = sx1509_.read_keypad();
  if (read_result.has_error()) {
    if (read_result.error() != last_err_) {
      ESP_LOGE(LogTag,
               "keypad read error: %s",
               esp_err_to_name(read_result.error()));
    }
    last_err_ = read_result.error();
    return;
  }
  last_err_ = ESP_OK;

  const auto key = read_result.value();
  bool bad = false;
  if ((key != 0) && ((key & 0xff) == 0 || ((key & 0xff00) == 0))) {
    // wtf?  the sx1509 sometimes returns results with a column but not a row
    // set, and vice versa.
    bad = true;
  }
#if 0
  if (key == last_key_) {
    ++same_count_;
    noint_count_ = 0;
    return;
  }

  ++counter_;
  printf("%" PRIu64 " %d (%" PRIu64 ") %c key after %" PRIu64 ": (%#x %#x) %02x %02x\n",
         counter_,
         int_value,
         noint_count_,
         bad ? 'X' : ' ',
         same_count_,
         key,
         last_key_,
         ((key >> 8) & 0xff),
         (key & 0xff));
  last_key_ = key;
  same_count_ = 0;
  noint_count_ = 0;
#else
  ++counter_;
  printf("%" PRIu64 " (%" PRIu64 ") %c key %02x\n",
         counter_,
         noint_count_,
         bad ? 'X' : ' ',
         key);
  noint_count_ = 0;
#endif
#endif
}

} // namespace mantyl
