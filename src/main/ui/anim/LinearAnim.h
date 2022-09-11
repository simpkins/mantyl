// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "ui/anim/Anim.h"

#include <type_traits>

namespace mantyl {

template <typename T>
class LinearAnim : public Anim<T> {
public:
  explicit LinearAnim(T start, T end, std::chrono::milliseconds duration)
      : start_{start}, end_{end}, duration_{duration} {}

  T get_value(std::chrono::milliseconds time_since_start) override {
    if (time_since_start >= duration_) {
      return end_;
    }

    if (std::is_floating_point_v<T>) {
      const T f =
          ((end_ - start_) * time_since_start.count()) / duration_.count();
      return start_ + f;
    } else {
      const T f = static_cast<T>(
          (static_cast<int64_t>(end_ - start_) * time_since_start.count()) /
          duration_.count());
      return start_ + f;
    }
  }

  std::chrono::milliseconds duration() const override {
    return duration_;
  }

private:
  T start_{};
  T end_{};
  const std::chrono::milliseconds duration_{};
};

} // namespace mantyl
