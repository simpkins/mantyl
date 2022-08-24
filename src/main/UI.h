// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <esp_err.h>

#include <chrono>
#include <memory>

namespace mantyl {

template <typename T>
class Anim;

class SSD1306;

class UI {
public:
  explicit UI(SSD1306 *display);
  ~UI();

  [[nodiscard]] esp_err_t init();

  std::chrono::milliseconds tick(std::chrono::steady_clock::time_point now);

private:
  UI(UI const &) = delete;
  UI &operator=(UI const &) = delete;

  SSD1306* const display_{nullptr};

  std::chrono::steady_clock::time_point start_;
  std::unique_ptr<Anim<uint8_t>> fade_;
};

} // namespace mantyl
