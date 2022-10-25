// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "ui/UIMode.h"

#include <functional>
#include <string>
#include <string_view>
#include <vector>

namespace mantyl {

class Menu : public UIMode {
public:
  explicit Menu(UI &ui);

  void render() override;

  void button_left() override;
  void button_right() override;
  void button_up() override;
  void button_down() override;

  // Functions for initializing the menu entries.
  void add_entry(std::string_view text);
  void add_entry(std::string_view text, std::function<void()> &&fn);

private:
  struct MenuEntry {
    MenuEntry(std::string_view t, std::function<void()> &&f)
        : text(t), fn(std::move(f)) {}

    std::string text;
    std::function<void()> fn;
  };

  std::vector<MenuEntry> entries_;
  size_t index_{0};
};

} // namespace mantyl
