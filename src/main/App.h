// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "sdkconfig.h"
#include "config.h"

#include "I2cMaster.h"
#include "Keyboard.h"
#include "KeymapDB.h"
#include "SSD1306.h"
#include "UI.h"
#include "UsbDevice.h"

#include <esp_err.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#include <chrono>

namespace mantyl {

class App {
public:
  App();
  ~App();

  static App *get() {
    return singleton_;
  }

  [[nodiscard]] esp_err_t init();

  void main();

  UI &ui() {
    return ui_;
  }
  UsbDevice &usb() {
    return usb_;
  }

  void notify_new_log_message();

  void left_keypad_interrupt() {
      on_gpio_interrupt(NotifyBits::Left);
  }
  void right_keypad_interrupt() {
      on_gpio_interrupt(NotifyBits::Right);
  }

  void on_special_action(SpecialAction action, bool press);

private:
  enum NotifyBits : unsigned long {
    Left = 0x01,
    Right = 0x02,
    LogMessage = 0x04,
  };

  App(App const &) = delete;
  App &operator=(App const &) = delete;

  static void keyboard_task_fn(void *arg);

  void keyboard_task();
  std::chrono::steady_clock::time_point
  keyboard_tick(std::chrono::steady_clock::time_point now);
  void on_gpio_interrupt(NotifyBits bits);

  static App *singleton_;

  UsbDevice usb_;
  I2cMaster i2c_left_{PinConfig::LeftI2cSDA, PinConfig::LeftI2cSCL, I2C_NUM_0};
  I2cMaster i2c_right_{
      PinConfig::RightI2cSDA, PinConfig::RightI2cSCL, I2C_NUM_1};
  SSD1306 display_{i2c_left_, 0x3c, GPIO_NUM_1};
  UI ui_{&display_};
  KeymapDB keymap_db_;
  Keyboard keyboard_{i2c_left_, i2c_right_, keymap_db_};

  TaskHandle_t task_handle_{};
};

} // namespace mantyl
