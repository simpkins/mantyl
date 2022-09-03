// Copyright (c) 2022, Adam Simpkins
#include "UI.h"

#include "App.h"
#include "CompositeAnim.h"
#include "ConstantAnim.h"
#include "LinearAnim.h"
#include "SSD1306.h"

#include <esp_log.h>

#include <cstdarg>

namespace {
const char *LogTag = "mantyl.ui";
vprintf_like_t orig_log_vprintf;

constexpr size_t max_log_msg_len = 128;

int ui_vprintf(const char *format, va_list ap) {
  // Write to the original log function
  int result = 0;
  const auto orig_fn = orig_log_vprintf;
  if (orig_fn) {
    va_list ap2;
    va_copy(ap2, ap);
    result = orig_fn(format, ap2);
    va_end(ap2);
  }

  // Format for our own logging purposes
  std::vector<char> buf;
  buf.resize(max_log_msg_len);
  auto size_written = vsnprintf(buf.data(), buf.size(), format, ap);
  if (size_written >= 0 && size_written < buf.size()) {
    buf.resize(size_written);
  }

#if CONFIG_LOG_COLORS
  // Strip off color escape sequences.
  static constexpr std::string_view kResetSequence(LOG_RESET_COLOR "\n");
  if (buf.size() >= kResetSequence.size()) {
    if (memcmp(buf.data() + buf.size() - kResetSequence.size(),
               kResetSequence.data(),
               kResetSequence.size()) == 0) {
      buf.resize(buf.size() - kResetSequence.size());
    }
  }

  if (buf.size() >= 3 && buf[0] == '\033' && buf[1] == '[') {
    size_t strip_idx = 2;
    while (strip_idx < buf.size()) {
      if (buf[strip_idx] == 'm') {
        ++strip_idx;
        break;
      }
      ++strip_idx;
    }
    // It might be nicer to store both a vector and a string_view,
    // so that we could strip without actually doing a memmove().
    memmove(buf.data(), buf.data() + strip_idx, buf.size() - strip_idx);
    buf.resize(buf.size() - strip_idx);
  }
#else
  // Strip off a trailing newline
  if (buf.size() >= 1 && buf[buf.size() - 1] == '\n') {
    buf.resize(buf.size() - 1);
  }
#endif // CONFIG_LOG_COLORS

  auto* app = mantyl::App::get();
  app->ui().append_log_message(std::move(buf));
  app->notify_new_log_message();

  return result;
}

} // namespace

namespace mantyl {

UI::UI(SSD1306 *display) : display_{display} {}

UI::~UI() {
  if (orig_log_vprintf) {
    esp_log_set_vprintf(orig_log_vprintf);
  }
}

esp_err_t UI::init() {
  auto rc = display_->init();
  if (rc != ESP_OK) {
    return rc;
  }

  start_fade_timer();

  display_->write_centered("Adam Simpkins", SSD1306::Line1);
  display_->write_centered("adam@adamsimpkins.net", SSD1306::Line2);
  rc = display_->flush();
  if (rc != ESP_OK) {
    return rc;
  }

  orig_log_vprintf = esp_log_set_vprintf(ui_vprintf);

  return ESP_OK;
}

void UI::button_left() {
  // TODO
}

void UI::button_right() {
  // TODO
}

void UI::button_up() {
  // TODO
}

void UI::button_down() {
  // TODO
}

void UI::button_press() {
  // It is difficult to press the directional switch directly in without also
  // accidentally pressing other directions.  Therefore we do not use the
  // center press in the UI.  All "confirm" actions are done with a right press
  // instead.
}

void UI::start_fade_timer() {
  fade_start_ = std::chrono::steady_clock::now();
  const uint8_t init_contrast = 0xff;
  auto constant_portion = std::make_unique<ConstantAnim<uint8_t>>(
      init_contrast, std::chrono::seconds(2));
  auto fade_portion = std::make_unique<LinearAnim<uint8_t>>(
      init_contrast, 0x00, std::chrono::seconds(3));
  fade_ = std::make_unique<CompositeAnim<uint8_t>>(std::move(constant_portion),
                                                   std::move(fade_portion));
  auto rc = display_->set_contrast(init_contrast);
  // Don't log any warnings if set_contrast() fails, since we don't want to
  // emit more log messages when an error occurs processing a log message.
  static_cast<void>(rc);
}

std::chrono::milliseconds UI::tick(std::chrono::steady_clock::time_point now) {
  if (fade_) {
    const auto anim_time =
        std::chrono::duration_cast<std::chrono::milliseconds>(now -
                                                              fade_start_);
    const auto contrast = fade_->get_value(anim_time);
    if (contrast == 0) {
      fade_.reset();
      const auto rc = display_->display_off();
      if (rc != ESP_OK) {
        ESP_LOGW(LogTag, "error turning display off: %s", esp_err_to_name(rc));
      }
      return std::chrono::minutes(60);
    } else {
      const auto rc = display_->set_contrast(contrast);
      if (rc != ESP_OK) {
        ESP_LOGW(
            LogTag, "error setting display contrast: %s", esp_err_to_name(rc));
      }
      return std::chrono::milliseconds(30);
    }
  }

  return std::chrono::minutes(60);
}

void UI::append_log_message(std::vector<char>&& msg) {
  // This method may be called from any thread.
  {
    std::lock_guard<std::mutex> lock(log_mutex_);
    log_messages_.emplace_back(std::move(msg));
  }
}

void UI::display_log_messages() {
  // This method is called from the main I2C thread, after
  // append_log_message() has added new messages to log_messages_
  std::vector<std::vector<char>> messages;
  {
    std::lock_guard<std::mutex> lock(log_mutex_);
    messages.swap(log_messages_);
  }

  display_->clear();
  start_fade_timer();

  // TODO: just print the last message.  As-is this code writes multiple
  // messages but doesn't clear previous ones properly.
  for (const auto& msg : messages) {
    std::string_view str(msg.data(), msg.size());
    for (const auto& line_range :
         {SSD1306::Line0, SSD1306::Line1, SSD1306::Line2, SSD1306::Line3}) {
      auto result = display_->write_text(str, line_range);
      str = str.substr(result.char_end);
      if (str.empty()) {
        break;
      }
    }
  }
  auto rc = display_->flush();
  rc = display_->display_on();
  static_cast<void>(rc);
}

} // namespace mantyl
