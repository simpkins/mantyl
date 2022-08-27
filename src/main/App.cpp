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

void App::left_gpio_intr_handler(void* arg) {
  auto *app = static_cast<App *>(arg);
  app->on_gpio_interrupt(NotifyBits::Left);
}

void App::right_gpio_intr_handler(void* arg) {
  auto *app = static_cast<App *>(arg);
  app->on_gpio_interrupt(NotifyBits::Right);
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
  done_sem_ = xSemaphoreCreateBinary();

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

  ESP_LOGV(LogTag, "attempting left SX1509 init:");
  rc = left_.init();
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

std::chrono::steady_clock::time_point
App::keyboard_tick(std::chrono::steady_clock::time_point now) {
  const auto left_timeout = left_.tick(now);
  const auto right_timeout = right_.tick(now);
  const auto ui_timeout = ui_.tick(now);
  const auto next_timeout =
      now + std::min(std::min(left_timeout, right_timeout), ui_timeout);
  ESP_LOGD(LogTag,
           "tick: left=%ld (%d) right=%ld (%d)",
           static_cast<long int>(left_timeout.count()),
           (int)left_.num_pressed(),
           static_cast<long int>(right_timeout.count()),
           (int)right_.num_pressed());
  return next_timeout;
}

void App::keyboard_task() {
  ESP_ERROR_CHECK(gpio_isr_handler_add(
      left_.interrupt_pin(), left_gpio_intr_handler, this));
  ESP_ERROR_CHECK(gpio_isr_handler_add(
      right_.interrupt_pin(), right_gpio_intr_handler, this));

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
  xSemaphoreGive(done_sem_);
}

void App::keyboard_task_fn(void* arg) {
  auto *app = static_cast<App *>(arg);
  printf("keyboard_task start; app=%p\n", app);
  app->keyboard_task();
  printf("keyboard_task suspending\n");
  vTaskSuspend(nullptr);
}

void App::main() {
  printf("main task prepare; app=%p\n", this);
  ESP_ERROR_CHECK(init());

  bool debug_mode = true; // TODO: read setting from flash
  bool boot_into_debug_mode = false;
  if (debug_mode) {
    vTaskDelay(pdMS_TO_TICKS(10));
    if (left_.is_interrupt_asserted()) {
      ESP_LOGI(LogTag, "key held down during init");
      boot_into_debug_mode = true;
    }
  }

  if (boot_into_debug_mode) {
    const auto usb_rc = usb_.init();
    if (usb_rc != ESP_OK) {
      ESP_LOGE(LogTag, "failed to initialize USB: %d", usb_rc);
    }
  }

  static constexpr configSTACK_DEPTH_TYPE keyboard_task_stack_size = 4096;
  const auto rc = xTaskCreatePinnedToCore(keyboard_task_fn,
                                          "keyboard",
                                          keyboard_task_stack_size,
                                          this,
                                          2,
                                          &task_handle_,
                                          0);
  if (rc != pdPASS) {
    ESP_LOGE(LogTag, "failed to create keyboard task");
    return;
  }

  // Wait for the keyboard task to finish.
  // (This should normally never happen.)
  printf("main task run\n");
  while (true) {
    if (xSemaphoreTake(done_sem_, portMAX_DELAY) == pdTRUE) {
      break;
    }
  }
}

} // namespace mantyl
