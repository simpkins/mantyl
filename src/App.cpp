// Copyright (c) 2022, Adam Simpkins
#include "App.h"

#include "esp_util.h"

namespace mtl {

App::App() : display_{Display::adafruit128x32(&Wire, kScreenAddress)} {}

void App::setup() {
  Serial.begin(kSerialBaudRate);

  Serial.println("mantyl init");
  if (!display_.begin()) {
    Serial.println("display initialization failed");
  } else {
    Serial.println("display initialization success!");
  }

  display_.clearDisplayBuffer();
  display_.canvas().setTextSize(1);      // Normal 1:1 pixel scale
  display_.canvas().setTextColor(1);     // Draw white text
  display_.canvas().setCursor(0, 0);     // Start at top-left corner
  display_.canvas().cp437(true);         // Use full 256 char 'Code Page 437' font
  flushDisplay();
  writeMsg("init");
  flushDisplay();

  if (!leftIO_.begin(kSX1509AddressLeft)) {
    // writeMsg("io init failed");
    Serial.println("io init failed");
  } else {
      // writeMsg("io init success");
      Serial.println("io init success");
      leftIO_.keypad(kLeftRows, kLeftCols, kKeypadSleepTimeMS, kKeypadScanTimeMS,
                     kKeypadDebounceTimeMS);
  }
}

void App::loop() {
  ++counter_;
  display_.clearDisplayBuffer();
  display_.canvas().setCursor(0, 0);
  display_.canvas().print("loop: ");
  display_.canvas().print(counter_);

  display_.canvas().setCursor(0, 8);
  display_.canvas().print("keys: ");
  unsigned int keyData = leftIO_.readKeypad();
  display_.canvas().print(keyData, HEX);

  flushDisplay();
  delay(50);
}

void App::writeMsg(std::string_view msg) {
  for (char c : msg) {
    display_.canvas().write(c);
  }
  flushDisplay();
}

void App::flushDisplay() {
  if (!display_.flush()) {
    Serial.println("display flush failed");
  }
}

} // namespace mtl
