// Copyright (c) 2022, Adam Simpkins
#include "ui/MainMenu.h"

#include "ui/Menu.h"
#include "ui/UI.h"
#include "ui/UIMode.h"
#include "SSD1306.h"

#include <memory>

namespace mantyl {

namespace {

/**
 * A UIMode that does not respond to any button input other than the back
 * button.
 */
class LeafMode : public UIMode {
public:
  using UIMode::UIMode;

  void render() {
    render_static();
    auto rc = display().flush();
    rc = display().display_on();
    static_cast<void>(rc);
  }

  void button_left() override {
    auto self = ui().pop_mode();
    static_cast<void>(self);
  }
  void button_right() override {}
  void button_up() override {}
  void button_down() override {}

protected:
  virtual void render_static() = 0;
};

class OwnerPage : public LeafMode {
protected:
  using LeafMode::LeafMode;

  void render_static() override {
    display().clear();
    display().write_centered("Adam Simpkins", SSD1306::Line1);
    display().write_centered("adam@adamsimpkins.net", SSD1306::Line2);
  }
};

void push_info_menu(UI &ui) {
  auto info_menu = std::make_unique<Menu>(ui);
  info_menu->add_entry(
      "Owner", [&ui] { ui.push_mode(std::make_unique<OwnerPage>(ui)); });
  info_menu->add_entry("Status");
  info_menu->add_entry("Version");
  ui.push_mode(std::move(info_menu));
}

} // namespace

std::unique_ptr<UIMode> create_main_menu(UI& ui) {
  auto menu = std::make_unique<Menu>(ui);

  menu->add_entry("Info", [&ui] { push_info_menu(ui); });
  menu->add_entry("Select Keymap");
  menu->add_entry("Edit Keymaps");
  menu->add_entry("Settings");
  menu->add_entry("Debug");

  return menu;
}

} // namespace mantyl