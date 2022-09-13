// Copyright (c) 2022, Adam Simpkins
#include "ui/Menu.h"

#include "SSD1306.h"
#include "ui/UI.h"

namespace mantyl {

Menu::Menu(UI &ui) : UIMode(ui) {}

void Menu::render() {
  SSD1306::WriteResult result;
  constexpr size_t num_display_lines = 4;
  size_t start_idx = num_display_lines * (index_ / num_display_lines);
  for (size_t line_idx = 0; line_idx < num_display_lines; ++line_idx) {
    size_t entry_idx = start_idx + line_idx;
    const uint16_t line_px_start = 128 * line_idx;
    const SSD1306::OffsetRange left_range{line_px_start, line_px_start + 8};
    const SSD1306::OffsetRange text_range{line_px_start + 8, line_px_start + 122};
    const SSD1306::OffsetRange right_range{line_px_start + 122, line_px_start + 128};

    auto result = display().write_text(
        index_ == entry_idx ? "\x10" : "", left_range, true);
    result = display().write_text(
        entry_idx < entries_.size() ? entries_[entry_idx].text : "",
        text_range,
        true);

    std::string_view right_data;
    if (line_idx == 0 && entry_idx > 0) {
      right_data = "\x1e";
    } else if (line_idx == 3 && entry_idx + 1 < entries_.size()) {
      right_data = "\x1f";
    }
    result = display().write_text(right_data, right_range, true);
  }

  auto rc = display().flush();
  rc = display().display_on();
  static_cast<void>(rc);
}

void Menu::button_left() {
  // Beware: pop_mode() will typically return a unique_ptr to ourself.  (It may
  // return nullptr if we are the main menu, and cannot be popped off.)
  // We will typically be deleted when it is destroyed, so we should not access
  // any member variables after it goes out of scope.
  auto self = ui().pop_mode();
  static_cast<void>(self);
}

void Menu::button_right() {
  if (index_ < entries_.size()) {
    entries_[index_].fn();
  }
}

void Menu::button_up() {
  if (index_ > 0) {
    --index_;
  }
  render();
}

void Menu::button_down() {
  if (index_ + 1 < entries_.size()) {
    ++index_;
  }
  render();
}

void Menu::add_entry(std::string_view text) {
  entries_.emplace_back(text, []() {});
}

void Menu::add_entry(std::string_view text, std::function<void()> &&fn) {
  entries_.emplace_back(text, std::move(fn));
}

} // namespace mantyl
