// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "ui/UIMode.h"

#include <string>
#include <string_view>
#include <vector>

namespace mantyl {

class Menu : public UIMode {
public:
  explicit Menu(UI *ui);
  explicit Menu(UI *ui, std::vector<std::string> &&entries);

  void render() override;

  void button_left() override;
  void button_right() override;
  void button_up() override;
  void button_down() override;

protected:
  void add_entry(std::string_view text);

private:
  std::vector<std::string> entries_;
  size_t index_{0};
};

} // namespace mantyl
