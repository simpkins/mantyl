// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <esp_err.h>

#include <chrono>
#include <memory>
#include <mutex>
#include <vector>

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

  /**
   * Append a new log message.
   *
   * Unlike most other UI methods, this method is thread-safe, and can be
   * called from any threa.
   */
  void append_log_message(std::vector<char>&& msg);

  void display_log_messages();

private:
  UI(UI const &) = delete;
  UI &operator=(UI const &) = delete;

  SSD1306* const display_{nullptr};

  std::chrono::steady_clock::time_point start_;
  std::unique_ptr<Anim<uint8_t>> fade_;

  std::mutex log_mutex_;
  std::vector<std::vector<char>> log_messages_;
};

} // namespace mantyl
