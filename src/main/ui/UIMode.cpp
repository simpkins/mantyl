// Copyright (c) 2022, Adam Simpkins
#include "ui/UIMode.h"

#include "ui/UI.h"

namespace mantyl {

SSD1306 &UIMode::display() {
  return ui_->display();
}

} // namespace mantyl
