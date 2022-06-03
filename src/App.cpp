// Copyright (c) 2022, Adam Simpkins
#include "App.h"

#include "esp_util.h"

#define NEW_DISPLAY 1

namespace mtl {

App::App()
    : display_(kScreenWidth, kScreenHeight, &Wire, kResetPin),
      disp_{Display::adafruit128x32(&Wire, kScreenAddress)} {}

void App::setup() {
  Serial.begin(kSerialBaudRate);

#ifdef NEW_DISPLAY
  if(!disp_.begin()) {
    Serial.println(F("display initialization failed"));
  } else {
    Serial.println(F("display initialization success!"));
  }
#else
  // SSD1306_SWITCHCAPVCC = generate display voltage from 3.3V internally
  if (!display_.begin(SSD1306_SWITCHCAPVCC, kScreenAddress)) {
    Serial.println(F("old display initialization failed"));
    // Go to deep sleep for 30 seconds.  When we wake up setup() will restart
    mtl::set_sleep_timer_wakeup(std::chrono::seconds{30});
    esp_deep_sleep_start();
  }

  Serial.println(F("mantyl init"));
  display_.clearDisplay();
  display_.setTextSize(1);      // Normal 1:1 pixel scale
  display_.setTextColor(SSD1306_WHITE); // Draw white text
  display_.setCursor(0, 0);     // Start at top-left corner
  display_.cp437(true);         // Use full 256 char 'Code Page 437' font
  display_.display();
#endif
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
#ifndef NEW_DISPLAY
  display_.clearDisplay();
  display_.setCursor(0, 0);
  display_.print(counter_);
  display_.print(": loop\nkeys: ");
  unsigned int keyData = leftIO_.readKeypad();
  display_.print(keyData, HEX);

  display_.display();
#endif
  delay(50);
}

void App::writeMsg(std::string_view msg) {
#ifdef NEW_DISPLAY
  (void)disp_.draw_pixel(0, 0, true);
  (void)disp_.draw_pixel(2, 0, true);
  (void)disp_.draw_pixel(4, 0, true);
  (void)disp_.draw_pixel(1, 1, true);
  (void)disp_.draw_pixel(3, 1, true);
  if (!disp_.flush()) {
    Serial.println(F("display flush failed"));
  } else {
    Serial.println(F("display flush succeeded"));
  }
#else
  for (char c : msg) {
    display_.write(c);
  }
  display_.display();
#endif
}

} // namespace mtl
