// Copyright (c) 2022, Adam Simpkins
#include "ui/MainMenu.h"

#include "ui/Menu.h"
#include "ui/UI.h"
#include "ui/UIMode.h"
#include "App.h"
#include "SSD1306.h"

#include <esp_app_desc.h>
#include <esp_system.h>

#include <cinttypes>
#include <cstdint>
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

class VersionPage : public LeafMode {
protected:
  using LeafMode::LeafMode;

  void render_static() override {
    const auto *app_desc = esp_app_get_description();
    std::array<char, 48> buf;

    snprintf(buf.data(), buf.size(), "Version: %s", app_desc->version);
    display().write_text(buf.data(), SSD1306::Line0, true);

    snprintf(buf.data(), buf.size(), "Build Date: %s", app_desc->date);
    display().write_text(buf.data(), SSD1306::Line1, true);

    snprintf(buf.data(), buf.size(), "Build Time: %s", app_desc->time);
    display().write_text(buf.data(), SSD1306::Line2, true);

    snprintf(buf.data(), buf.size(), "IDF: %s", app_desc->idf_ver);
    display().write_text(buf.data(), SSD1306::Line3, true);
  }
};

class StatusPage : public UIMode {
public:
  using UIMode::UIMode;

  void render() {
    render_contents();
    auto rc = display().flush();
    rc = display().display_on();
    static_cast<void>(rc);
  }

  void button_left() override {
    auto self = ui().pop_mode();
    static_cast<void>(self);
  }
  void button_right() override {
    render();
  }
  void button_up() override {
    render();
  }
  void button_down() override {
    render();
  }

private:
  void render_contents() {
    display().clear();
    std::array<char, 48> buf;

    const auto uptime =
        std::chrono::steady_clock::now() - App::get()->get_boot_time();
    const auto uptime_secs =
        std::chrono::duration_cast<std::chrono::seconds>(uptime);

    // TODO: format the uptime into Ndays HH:MM:SS
    snprintf(buf.data(),
             buf.size(),
             "Uptime: %" PRId64,
             static_cast<int64_t>(uptime_secs.count()));
    display().write_text(buf.data(), SSD1306::Line0, true);

    snprintf(buf.data(), buf.size(), "Reset Reason: %d", esp_reset_reason());
    display().write_text(buf.data(), SSD1306::Line1, true);

    // TODO:
    // - report whether right keyboard half is connected
    // - report most recent error log
  }
};

void push_info_menu(UI &ui) {
  auto info_menu = std::make_unique<Menu>(ui);
  info_menu->add_entry(
      "Owner", [&ui] { ui.push_mode(std::make_unique<OwnerPage>(ui)); });
  info_menu->add_entry(
      "Version", [&ui] { ui.push_mode(std::make_unique<VersionPage>(ui)); });
  info_menu->add_entry(
      "Status", [&ui] { ui.push_mode(std::make_unique<StatusPage>(ui)); });
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
