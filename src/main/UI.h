// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <chrono>

#include <esp_err.h>

namespace mantyl {

class SSD1306;

class UI {
public:
  explicit UI(SSD1306* display) : display_{display} {}

  [[nodiscard]] esp_err_t init();

  std::chrono::milliseconds tick(std::chrono::steady_clock::time_point now);

private:
  UI(UI const &) = delete;
  UI &operator=(UI const &) = delete;

  SSD1306* const display_{nullptr};

  std::chrono::steady_clock::time_point start_;
};

} // namespace mantyl
