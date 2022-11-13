// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <string>
#include <string_view>

namespace mantyl {

std::string readline(std::string_view prompt);
void puts(std::string_view str);
void putc(char c);

} // namespace mantyl
