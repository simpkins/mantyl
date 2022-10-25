// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "ui/anim/Anim.h"

namespace mantyl {

template <typename T>
class ConstantAnim : public Anim<T> {
public:
  explicit ConstantAnim(T value, std::chrono::milliseconds duration)
      : value_{value}, duration_{duration} {}

  T get_value(std::chrono::milliseconds time_since_start) override {
    return value_;
  }

  std::chrono::milliseconds duration() const override {
    return duration_;
  }

private:
  const T value_{};
  std::chrono::milliseconds duration_{};
};

} // namespace mantyl
