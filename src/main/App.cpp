// Copyright (c) 2022, Adam Simpkins
#include "App.h"

#include <driver/i2c.h>
#include <esp_check.h>
#include <esp_chip_info.h>
#include <esp_flash.h>
#include <esp_log.h>
#include <cstdio>

using namespace std::chrono_literals;

namespace {
const char *LogTag = "mantyl.app";
}

namespace mantyl {

App* App::singleton_;

App::App() {
  singleton_ = this;
}

App::~App() {
  singleton_ = nullptr;
}

void App::on_gpio_interrupt(NotifyBits bits) {
  BaseType_t high_task_wakeup = pdFALSE;
  xTaskNotifyFromISR(task_handle_, bits, eSetBits, &high_task_wakeup);

  if (high_task_wakeup == pdTRUE) {
    portYIELD_FROM_ISR();
  }
}

void App::notify_new_log_message() {
  if (task_handle_) {
    xTaskNotify(task_handle_, NotifyBits::LogMessage, eSetBits);
  } else {
    // TODO: delete this eventually once done debugging the initialization
    // code.  This isn't really safe.
    ui_.display_log_messages();
  }
}

esp_err_t App::init() {
  auto rc = i2c_left_.init(I2cClockSpeed);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to initialize left I2C bus");

  rc = i2c_right_.init(I2cClockSpeed);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to initialize right I2C bus");

  rc = gpio_install_isr_service(0);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to install gpio ISR");

  ESP_LOGI(LogTag, "attempting display init:");
  rc = ui_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized display");
  } else {
    ESP_LOGE(LogTag,
             "failed to initialize display matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  rc = keyboard_.early_init();
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to initialize keyboard");

  return ESP_OK;
}

void App::on_ui_key_press(uint8_t key) {
  ESP_LOGI(LogTag, "UI key press: %d", key);
}

void App::on_ui_key_release(uint8_t key) {
  ESP_LOGI(LogTag, "UI key release: %d", key);
}

std::chrono::steady_clock::time_point
App::keyboard_tick(std::chrono::steady_clock::time_point now) {
  // We currently run both keyboard_.tick() and ui_.tick() any time we wake
  // up, regardless of why we wake up.  We potentially could be smarter here in
  // the future, and only run the handler for the specific event that triggered
  // us to wake up.  However, always checking everything is simpler.
  const auto kbd_timeout = keyboard_.tick(now);
  const auto ui_timeout = ui_.tick(now);
  const auto next_timeout = std::min(kbd_timeout, ui_timeout);
  ESP_LOGD(LogTag,
           "tick: next_timeout=%ld",
           static_cast<long int>(next_timeout.count()));
  return now + next_timeout;
}

void App::keyboard_task() {
  ESP_ERROR_CHECK(keyboard_.kbd_task_init());

  auto now = std::chrono::steady_clock::now();
  auto next_timeout = keyboard_tick(now);

  while (true) {
    // TODO: we tend to wake up slightly before the timeout, which causes us to
    // go back to sleep then wake up quickly again a couple times before we
    // really hit the desired timeout.
    const auto max_delay = next_timeout - now;
    const auto max_delay_ticks = (max_delay.count() * configTICK_RATE_HZ *
                                  decltype(max_delay)::period::num) /
                                 decltype(max_delay)::period::den;
    unsigned long notified_value = 0;
    const auto rc =
        xTaskNotifyWait(pdFALSE, ULONG_MAX, &notified_value, max_delay_ticks);
    if (rc == pdTRUE) {
      ESP_LOGD(LogTag, "received notification: %#04lx", notified_value);
      if (notified_value & NotifyBits::LogMessage) {
        ui_.display_log_messages();
      }
    }

    now = std::chrono::steady_clock::now();
    next_timeout = keyboard_tick(now);
  }
}

void App::main() {
  task_handle_ = xTaskGetCurrentTaskHandle();
  ESP_ERROR_CHECK(init());

  bool boot_into_debug_mode = false;
  vTaskDelay(pdMS_TO_TICKS(10));
  if (keyboard_.should_boot_in_debug_mode()) {
    ESP_LOGI(LogTag, "key held down during init: booting in debug mode");
    boot_into_debug_mode = true;
  }

  ESP_LOGI(LogTag, "initializing USB...");
  const auto usb_rc = usb_.init(boot_into_debug_mode);
  if (usb_rc != ESP_OK) {
    ESP_LOGE(LogTag, "failed to initialize USB: %d", usb_rc);
  }

  keyboard_task();
}

} // namespace mantyl
