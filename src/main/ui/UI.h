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
class UIMode;

class UI {
public:
  explicit UI(SSD1306 *display);
  ~UI();

  [[nodiscard]] esp_err_t init();

  std::chrono::milliseconds tick(std::chrono::steady_clock::time_point now);

  SSD1306 &display() {
    return *display_;
  }

  /**
   * Append a new log message.
   *
   * Unlike most other UI methods, this method is thread-safe, and can be
   * called from any threa.
   */
  void append_log_message(std::vector<char>&& msg);

  void display_log_messages();

  void button_left();
  void button_right();
  void button_up();
  void button_down();
  void button_press();

  void pop_mode();
  void start_fade_timer();

private:
  UI(UI const &) = delete;
  UI &operator=(UI const &) = delete;

  void on_first_button_activity();

  SSD1306* const display_{nullptr};

  std::chrono::steady_clock::time_point fade_start_;
  std::unique_ptr<Anim<uint8_t>> fade_;

  std::vector<std::unique_ptr<UIMode>> mode_stack_;

  std::mutex log_mutex_;
  std::vector<std::vector<char>> log_messages_;
};

} // namespace mantyl
