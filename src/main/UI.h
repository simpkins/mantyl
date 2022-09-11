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

  void button_left();
  void button_right();
  void button_up();
  void button_down();
  void button_press();

private:
  UI(UI const &) = delete;
  UI &operator=(UI const &) = delete;

  void start_fade_timer();
  void render_menu();

  SSD1306* const display_{nullptr};

  std::chrono::steady_clock::time_point fade_start_;
  std::unique_ptr<Anim<uint8_t>> fade_;

  std::mutex log_mutex_;
  std::vector<std::vector<char>> log_messages_;

  std::array<std::string_view, 4> menu_entries_;
  int index_{0};
};

} // namespace mantyl
