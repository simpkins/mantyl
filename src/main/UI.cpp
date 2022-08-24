// Copyright (c) 2022, Adam Simpkins
#include "UI.h"

#include "CompositeAnim.h"
#include "ConstantAnim.h"
#include "LinearAnim.h"
#include "SSD1306.h"

#include <esp_log.h>

namespace {
const char *LogTag = "mantyl.ui";
}

namespace mantyl {

UI::UI(SSD1306 *display) : display_{display} {}

UI::~UI() = default;

esp_err_t UI::init() {
  auto rc = display_->init();
  if (rc != ESP_OK) {
    return rc;
  }

  start_ = std::chrono::steady_clock::now();
  const uint8_t init_contrast = 0xff;
  auto constant_portion = std::make_unique<ConstantAnim<uint8_t>>(
      init_contrast, std::chrono::seconds(2));
  auto fade_portion = std::make_unique<LinearAnim<uint8_t>>(
      init_contrast, 0x00, std::chrono::seconds(3));
  fade_ = std::make_unique<CompositeAnim<uint8_t>>(std::move(constant_portion),
                                                   std::move(fade_portion));
  rc = display_->set_contrast(init_contrast);
  if (rc != ESP_OK) {
    ESP_LOGW(LogTag, "error setting display contrast: %s", esp_err_to_name(rc));
  }

  display_->write_centered("Adam Simpkins", SSD1306::Line1);
  display_->write_centered("adam@adamsimpkins.net", SSD1306::Line2);
  rc = display_->flush();
  if (rc != ESP_OK) {
    return rc;
  }

  return ESP_OK;
}

std::chrono::milliseconds UI::tick(std::chrono::steady_clock::time_point now) {
  if (fade_) {
    const auto anim_time =
        std::chrono::duration_cast<std::chrono::milliseconds>(now - start_);
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

} // namespace mantyl
