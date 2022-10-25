// Copyright (c) 2022, Adam Simpkins
#pragma once

namespace mantyl {

class SSD1306;
class UI;

class UIMode {
public:
  explicit UIMode(UI &ui) : ui_{&ui} {}

  UI &ui() {
    return *ui_;
  }
  const UI &ui() const {
    return *ui_;
  }

  SSD1306 &display();

  virtual void render() = 0;

  virtual void button_left() = 0;
  virtual void button_right() = 0;
  virtual void button_up() = 0;
  virtual void button_down() = 0;

private:
  UIMode(UIMode const &) = delete;
  UIMode &operator=(UIMode const &) = delete;

  UI* const ui_{nullptr};
};

} // namespace mantyl
