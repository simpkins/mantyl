// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "Display.h"

#include <Adafruit_SSD1306.h>
#include <SparkFunSX1509.h>

#include <string_view>

namespace mtl {

class App {
public:
  App();
  void setup();
  void loop();

private:
  App(App const &) = delete;
  App &operator=(App const &) = delete;

  void writeMsg(std::string_view msg);

  static constexpr int kSerialBaudRate = 115200;

  static constexpr uint8_t kScreenWidth = 128;
  static constexpr uint8_t kScreenHeight = 32;
  static constexpr int8_t kResetPin = -1;
  static constexpr uint8_t kScreenAddress = 0x3c;

  static constexpr uint8_t kSX1509AddressLeft = 0x3e;
  static constexpr uint8_t kLeftRows = 3;
  static constexpr uint8_t kLeftCols = 2;
  static constexpr uint16_t kKeypadSleepTimeMS = 256;
  static constexpr uint8_t kKeypadScanTimeMS = 2;
  static constexpr uint8_t kKeypadDebounceTimeMS = 1;

  Adafruit_SSD1306 display_;
  Display disp_;
  SX1509 leftIO_;
  uint32_t counter_{0};
};

} // namespace mtl
