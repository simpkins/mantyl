// Copyright (c) 2022, Adam Simpkins
#include "UI.h"

#include "SSD1306.h"

#include <esp_log.h>

namespace {
const char *LogTag = "mantyl.ui";
}

namespace mantyl {

esp_err_t UI::init() {
  auto rc = display_->init();
  if (rc != ESP_OK) {
    return rc;
  }

  display_->write_centered("Adam Simpkins", SSD1306::Line1);
  display_->write_centered("adam@adamsimpkins.net", SSD1306::Line2);

  rc = display_->flush();
  if (rc != ESP_OK) {
    return rc;
  }

  start_ = std::chrono::steady_clock::now();
  return ESP_OK;
}

std::chrono::milliseconds UI::tick(std::chrono::steady_clock::time_point now) {
  constexpr std::chrono::milliseconds pre_fade_time = std::chrono::seconds(2);
  constexpr std::chrono::milliseconds fade_duration = std::chrono::seconds(3);

  const auto fade_start = start_ + pre_fade_time;
  if (now < fade_start) {
    return std::chrono::duration_cast<std::chrono::milliseconds>(fade_start -
                                                                 now);
  }
  const auto fade_end = fade_start + fade_duration;
  if (now < fade_end) {
    constexpr uint32_t contrast_steps = 32;
    const std::chrono::milliseconds fade_elapsed =
        std::chrono::duration_cast<std::chrono::milliseconds>(now - fade_start);
    const auto fraction =
        (contrast_steps * fade_elapsed.count()) / fade_duration.count();

    constexpr int kContrastMax = 0x7f;
    const int contrast =
        (kContrastMax * (contrast_steps - fraction)) / contrast_steps;
    ESP_LOGD(LogTag,
             "fade: elapsed=%d duration=%d fraction=%d contrast=%d",
             static_cast<int>(std::chrono::milliseconds{fade_elapsed}.count()),
             static_cast<int>(fade_duration.count()),
             fraction,
             contrast);

    if (contrast == 0) {
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
    }

    const auto next = fraction + 1;
    const auto next_time =
        ((next * fade_duration) / contrast_steps) + fade_start;
    std::chrono::milliseconds timeout =
        std::chrono::duration_cast<std::chrono::milliseconds>(next_time - now);
    ESP_LOGD(LogTag, "ui sleep until %d", static_cast<int>(timeout.count()));
    return timeout;
  }

  const auto rc = display_->display_off();
  if (rc != ESP_OK) {
    ESP_LOGW(LogTag, "error turning display off: %s", esp_err_to_name(rc));
  }
  return std::chrono::minutes(60);
}

} // namespace mantyl
