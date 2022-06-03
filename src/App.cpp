// Copyright (c) 2022, Adam Simpkins
#include "App.h"

#include "esp_util.h"

namespace mtl {

App::App() : display_{Display::adafruit128x32(&Wire, kScreenAddress)} {}

void App::setup() {
  Serial.begin(kSerialBaudRate);

  Serial.println(F("mantyl init"));
  if(!display_.begin()) {
    Serial.println(F("display initialization failed"));
  } else {
    Serial.println(F("display initialization success!"));
  }

  display_.clearDisplayBuffer();
  display_.canvas().setTextSize(1);      // Normal 1:1 pixel scale
  display_.canvas().setTextColor(1);     // Draw white text
  display_.canvas().setCursor(0, 0);     // Start at top-left corner
  display_.canvas().cp437(true);         // Use full 256 char 'Code Page 437' font
  flushDisplay();
  writeMsg("init");

#if 0
  if (!leftIO_.begin(kSX1509AddressLeft)) {
    writeMsg("io init failed");
  }

  writeMsg("io init success");
  leftIO_.keypad(kLeftRows, kLeftCols, kKeypadSleepTimeMS, kKeypadScanTimeMS,
                 kKeypadDebounceTimeMS);
#endif
}

void App::loop() {
  ++counter_;
  display_.clearDisplayBuffer();
  display_.canvas().setCursor(0, 0);
  display_.canvas().print("loop: ");
  display_.canvas().print(counter_);

#if 0
  display_.canvas().setCursor(0, 8);
  display_.canvas().print("keys: ");
  unsigned int keyData = leftIO_.readKeypad();
  display_.canvas().print(keyData, HEX);
#endif

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
    Serial.println(F("display flush failed"));
  } else {
    Serial.println(F("display flush succeeded"));
  }
}

} // namespace mtl
