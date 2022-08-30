// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "Keymap.h"

namespace mantyl {

class KeymapDB {
public:
  KeymapDB();

  const Keymap& get_builtin() const {
    return builtin_;
  }

private:
  KeymapDB(KeymapDB const &) = delete;
  KeymapDB &operator=(KeymapDB const &) = delete;

  Keymap builtin_;
};

} // namespace mantyl
