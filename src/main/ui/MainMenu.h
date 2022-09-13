// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <memory>

namespace mantyl {

class UI;
class UIMode;

std::unique_ptr<UIMode> create_main_menu(UI& ui);

} // namespace mantyl
