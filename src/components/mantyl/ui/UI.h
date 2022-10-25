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
  class Callback {
  public:
    virtual ~Callback() = default;
    virtual std::chrono::steady_clock::time_point get_boot_time() = 0;
    virtual void notify_new_log_message() = 0;
  };

  UI(Callback* callback, SSD1306 *display);
  ~UI();

  [[nodiscard]] esp_err_t init();

  std::chrono::milliseconds tick(std::chrono::steady_clock::time_point now);

  std::chrono::steady_clock::time_point get_boot_time() {
    return callback_->get_boot_time();
  }

  SSD1306 &display() {
    return *display_;
  }

  /**
   * Append a new log message.
   *
   * Unlike most other UI methods, this method is thread-safe, and can be
   * called from any thread.
   */
  void append_log_message(std::vector<char>&& msg);

  void display_log_messages();

  void button_left();
  void button_right();
  void button_up();
  void button_down();
  void button_press();

  void start_fade_timer();

  /**
   * Push a new UIMode onto the stack.
   */
  void push_mode(std::unique_ptr<UIMode> mode);

  /**
   * Attempt to pop the current UIMode off the stack.
   *
   * May return nullptr if this is the top-most mode, which cannot be popped
   * off.
   */
  std::unique_ptr<UIMode> pop_mode();

private:
  UI(UI const &) = delete;
  UI &operator=(UI const &) = delete;

  static int ui_vprintf(const char *format, va_list ap);

  void on_first_button_activity();

  Callback* const callback_{nullptr};
  SSD1306* const display_{nullptr};

  std::chrono::steady_clock::time_point fade_start_;
  std::unique_ptr<Anim<uint8_t>> fade_;

  std::vector<std::unique_ptr<UIMode>> mode_stack_;

  std::mutex log_mutex_;
  std::vector<std::vector<char>> log_messages_;
};

} // namespace mantyl
