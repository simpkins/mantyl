// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "Anim.h"

#include <memory>
#include <vector>

namespace mantyl {

template <typename T>
class CompositeAnim : public Anim<T> {
public:
  explicit CompositeAnim(std::vector<std::unique_ptr<Anim<T>>> &&anims)
      : anims_(std::move(anims)) {}

  template<typename Anim1, typename... Anims>
  explicit CompositeAnim(std::unique_ptr<Anim1>&& anim1, Anims&&... anims) {
    anims_.reserve(1 + sizeof...(anims));
    emplace_anims(std::move(anim1), std::forward<Anims>(anims)...);
  }

  T get_value(std::chrono::milliseconds time_since_start) override {
    if (anims_.empty()) {
      return T{};
    }

    size_t idx = 0;
    std::chrono::milliseconds anim_start{0};
    std::chrono::milliseconds anim_end{0};
    while (true) {
      auto& anim = anims_[idx];
      anim_end += anim->duration();
      if (anim_end > time_since_start || (idx + 1) >= anims_.size()) {
        return anim->get_value(time_since_start - anim_start);
      }
      anim_start = anim_end;
      ++idx;
    }
  }

  std::chrono::milliseconds duration() const override {
    std::chrono::milliseconds duration{0};
    for (auto &anim : anims_) {
      duration += anim->duration();
    }
    return duration;
  }

private:
  template<typename Anim1>
  void emplace_anims(std::unique_ptr<Anim1>&& a) {
    anims_.emplace_back(std::move(a));
  }

  template<typename Anim1, typename... Anims>
  void emplace_anims(std::unique_ptr<Anim1>&& a, Anims&&... rest) {
    anims_.emplace_back(std::move(a));
    emplace_anims(std::forward<Anims>(rest)...);
  }

  std::vector<std::unique_ptr<Anim<T>>> anims_;
};

} // namespace mantyl
