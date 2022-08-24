// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <chrono>

namespace mantyl {

template <typename T>
class Anim {
public:
  using value_type = T;

  virtual T get_value(std::chrono::milliseconds time_since_start) = 0;
  virtual std::chrono::milliseconds duration() const = 0;
};

} // namespace mantyl
