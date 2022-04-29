// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <Adafruit_SSD1306.h>

namespace ocb {

class App {
public:
  App();
  void setup();
  void loop();

private:
  App(App const &) = delete;
  App &operator=(App const &) = delete;

  static constexpr int kSerialBaudRate = 9600;

  static constexpr uint8_t kScreenWidth = 128;
  static constexpr uint8_t kScreenHeight = 32;
  static constexpr int8_t kResetPin = -1;
  static constexpr uint8_t kScreenAddress = 0x3c;

  Adafruit_SSD1306 display_;
};

} // namespace ocb
