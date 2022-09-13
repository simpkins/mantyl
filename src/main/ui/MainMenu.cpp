// Copyright (c) 2022, Adam Simpkins
#include "ui/MainMenu.h"

namespace mantyl {

MainMenu::MainMenu(UI *ui) : Menu(ui) {
  add_entry("Info");
  add_entry("Select Keymap");
  add_entry("Edit Keymaps");
  add_entry("Settings");
  add_entry("Debug");
}

} // namespace mantyl
