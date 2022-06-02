// Copyright (c) 2021, Adam Simpkins
#pragma once

#include <chrono>
#include <esp_sleep.h>

namespace mtl {

inline void set_sleep_timer_wakeup(std::chrono::microseconds us) {
  // esp_sleep_enable_timer_wakeup() takes the time duration as microseconds.
  // This helper function simply helps automatically convert the duration.
  esp_sleep_enable_timer_wakeup(us.count());
}

} // namespace mtl
