// Copyright (c) 2022, Adam Simpkins
#include "App.h"

#include "esp_util.h"

namespace ocb {

App::App() : display_(kScreenWidth, kScreenHeight, &Wire, kResetPin) {}

void App::setup() {
  Serial.begin(kSerialBaudRate);

  // SSD1306_SWITCHCAPVCC = generate display voltage from 3.3V internally
  if(!display_.begin(SSD1306_SWITCHCAPVCC, kScreenAddress)) {
    Serial.println(F("display initialization failed"));
    // Go to deep sleep for 30 seconds.  When we wake up setup() will restart
    ntpclock::set_sleep_timer_wakeup(std::chrono::seconds{30});
    esp_deep_sleep_start();
  }

  display_.display();
}

void App::loop() {}

} // namespace ocb
