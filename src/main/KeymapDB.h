// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "Keymap.h"

namespace mantyl {

class KeymapDB {
public:
  KeymapDB();

  const Keymap& current_keymap() const {
    return *keymaps_[current_index_];
  }

  KeyInfo get_key(bool left, uint8_t row, uint8_t col) const {
    return current_keymap().get_key(left, row, col);
  }

  void next_keymap();
  void prev_keymap();
  void set_keymap(size_t index);

private:
  KeymapDB(KeymapDB const &) = delete;
  KeymapDB &operator=(KeymapDB const &) = delete;

  void on_keymap_change();

  Keymap builtin_;
  Keymap wasd_;
  Keymap right_dir_;
  Keymap numpad_;
  std::array<Keymap*, 4> keymaps_{&builtin_, &wasd_, &right_dir_, &numpad_};
  size_t current_index_{0};
};

} // namespace mantyl
