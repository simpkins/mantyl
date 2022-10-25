// Copyright (c) 2022, Adam Simpkins
#include "keyboard/KeymapDB.h"

#include "mantyl_usb/hid.h"

#include <esp_log.h>

namespace {
const char *LogTag = "mantyl.app";
}

namespace mantyl {

using namespace hid;

KeymapDB::KeymapDB()
    : builtin_(
          "Default",
          {{
              // Left Row 0
              {Key::F1, 0},
              {Key::F2, 0},
              {Key::F3, 0},
              {Key::F4, 0},
              {Key::F5, 0},
              {Key::F6, 0},
              {Key::LeftAlt, Modifier::LeftAlt},
              {Key::SysReq, 0},

              // Left Row 1
              {KeySpecial, SpecialAction::Keymap0},
              {Key::Num1, 0},
              {Key::Num2, 0},
              {Key::Num3, 0},
              {Key::Num4, 0},
              {Key::Num5, 0},
              {Key::Escape, 0},
              {Key::Left, 0},

              // Left Row 2
              {KeySpecial, SpecialAction::KeymapNext},
              {Key::Q, 0},
              {Key::W, 0},
              {Key::E, 0},
              {Key::R, 0},
              {Key::T, 0},
              {Key::ScrollLock, 0},
              {Key::Backspace, 0},

              // Left Row 3
              {Key::LeftControl, Modifier::LeftControl},
              {Key::A, 0},
              {Key::S, 0},
              {Key::D, 0},
              {Key::F, 0},
              {Key::G, 0},
              {Key::Pause, 0},
              {Key::None, 0}, // Not connected

              // Left Row 4
              {Key::LeftShift, Modifier::LeftShift},
              {Key::Z, 0},
              {Key::X, 0},
              {Key::C, 0},
              {Key::V, 0},
              {Key::B, 0},
              {Key::PageUp, 0},
              {Key::None, 0}, // Not connected

              // Left Row 5
              {Key::None, 0},
              {Key::Home, 0},
              {Key::Backslash, 0},
              {Key::BracketLeft, 0},
              {Key::Minus, 0},
              {Key::Enter, 0},
              {Key::LeftGui, Modifier::LeftGui},
              {Key::Up, 0},

              // Right Row 0
              {Key::F12, 0},
              {Key::F11, 0},
              {Key::F10, 0},
              {Key::F9, 0},
              {Key::F8, 0},
              {Key::F7, 0},
              {Key::RightAlt, Modifier::RightAlt}, // thumb top center
              {Key::Insert, 0},                    // thumb top left

              // Right Row 1
              {Key::Tilde, 0},
              {Key::Num0, 0},
              {Key::Num9, 0},
              {Key::Num8, 0},
              {Key::Num7, 0},
              {Key::Num6, 0},
              {Key::RightGui, Modifier::RightGui}, // thumb center
              {Key::Right, 0},                     // thumb center left

              // Right Row 2
              {KeySpecial, SpecialAction::KeymapPrev},
              {Key::P, 0},
              {Key::O, 0},
              {Key::I, 0},
              {Key::U, 0},
              {Key::Y, 0},
              {Key::NumLock, 0},
              {Key::Delete, 0}, // thumb top right

              // Right Row 3
              {Key::RightControl, Modifier::RightControl},
              {Key::Semicolon, 0},
              {Key::L, 0},
              {Key::K, 0},
              {Key::J, 0},
              {Key::H, 0},
              {Key::PrintScreen, 0},
              {Key::None, 0}, // Not connected

              // Right Row 4
              {Key::RightShift, Modifier::RightShift},
              {Key::Quote, 0},
              {Key::Period, 0},
              {Key::Comma, 0},
              {Key::M, 0},
              {Key::N, 0},
              {Key::PageDown, 0},
              {Key::None, 0}, // Not connected

              // Right Row 5
              {Key::None, 0},
              {Key::End, 0},
              {Key::Slash, 0},
              {Key::BracketRight, 0},
              {Key::Equal, 0},
              {Key::Space, 0}, // thumb bottom right
              {Key::Tab, 0},   // thumb bottom middle
              {Key::Down, 0}   // thumb bottom left
          }}),
      wasd_("WASD Gaming",
            {{
                // Left Row 0
                {Key::F1, 0},
                {Key::F2, 0},
                {Key::F3, 0},
                {Key::F4, 0},
                {Key::F5, 0},
                {Key::F6, 0},
                {Key::LeftAlt, Modifier::LeftAlt},
                {Key::LeftGui, Modifier::LeftGui},

                // Left Row 1
                {KeySpecial, SpecialAction::Keymap0},
                {Key::Num1, 0},
                {Key::Num2, 0},
                {Key::Num3, 0},
                {Key::Num4, 0},
                {Key::Num5, 0},
                {Key::Escape, 0},
                {Key::Left, 0},

                // Left Row 2
                {KeySpecial, SpecialAction::KeymapNext},
                {Key::Tab, 0},
                {Key::Q, 0},
                {Key::W, 0},
                {Key::E, 0},
                {Key::R, 0},
                {Key::T, 0},
                {Key::Backspace, 0},

                // Left Row 3
                {Key::LeftControl, Modifier::LeftControl},
                {Key::LeftShift, Modifier::LeftShift},
                {Key::A, 0},
                {Key::S, 0},
                {Key::D, 0},
                {Key::F, 0},
                {Key::G, 0},
                {Key::None, 0}, // Not connected

                // Left Row 4
                {Key::LeftShift, Modifier::LeftShift},
                {Key::LeftControl, Modifier::LeftControl},
                {Key::Z, 0},
                {Key::X, 0},
                {Key::C, 0},
                {Key::V, 0},
                {Key::B, 0},
                {Key::None, 0}, // Not connected

                // Left Row 5
                {Key::Enter, 0},
                {Key::Home, 0},
                {Key::Backslash, 0},
                {Key::BracketLeft, 0},
                {Key::Minus, 0},
                {Key::Space, 0},
                {Key::LeftAlt, Modifier::LeftAlt},
                {Key::Up, 0},

                // Right Row 0
                {Key::F12, 0},
                {Key::F11, 0},
                {Key::F10, 0},
                {Key::F9, 0},
                {Key::F8, 0},
                {Key::F7, 0},
                {Key::RightAlt, Modifier::RightAlt}, // thumb top center
                {Key::Insert, 0},                    // thumb top left

                // Right Row 1
                {Key::Tilde, 0},
                {Key::Num0, 0},
                {Key::Num9, 0},
                {Key::Num8, 0},
                {Key::Num7, 0},
                {Key::Num6, 0},
                {Key::RightGui, Modifier::RightGui}, // thumb center
                {Key::Right, 0},                     // thumb center left

                // Right Row 2
                {KeySpecial, SpecialAction::KeymapPrev},
                {Key::P, 0},
                {Key::O, 0},
                {Key::I, 0},
                {Key::U, 0},
                {Key::Y, 0},
                {Key::NumLock, 0},
                {Key::Delete, 0}, // thumb top right

                // Right Row 3
                {Key::RightControl, Modifier::RightControl},
                {Key::Semicolon, 0},
                {Key::L, 0},
                {Key::K, 0},
                {Key::J, 0},
                {Key::H, 0},
                {Key::PageUp, 0},
                {Key::None, 0}, // Not connected

                // Right Row 4
                {Key::RightShift, Modifier::RightShift},
                {Key::Quote, 0},
                {Key::Period, 0},
                {Key::Comma, 0},
                {Key::M, 0},
                {Key::N, 0},
                {Key::PageDown, 0},
                {Key::None, 0}, // Not connected

                // Right Row 5
                {Key::None, 0},
                {Key::End, 0},
                {Key::Slash, 0},
                {Key::BracketRight, 0},
                {Key::Equal, 0},
                {Key::Space, 0}, // thumb bottom right
                {Key::Tab, 0},   // thumb bottom middle
                {Key::Down, 0}   // thumb bottom left
            }}),
      right_dir_(
          "Right Hand Directional",
          {{
              // Left Row 0
              {Key::F1, 0},
              {Key::F2, 0},
              {Key::F3, 0},
              {Key::F4, 0},
              {Key::F5, 0},
              {Key::F6, 0},
              {Key::LeftAlt, Modifier::LeftAlt},
              {Key::SysReq, 0},

              // Left Row 1
              {KeySpecial, SpecialAction::Keymap0},
              {Key::Num1, 0},
              {Key::Num2, 0},
              {Key::Num3, 0},
              {Key::Num4, 0},
              {Key::Num5, 0},
              {Key::Escape, 0},
              {Key::Left, 0},

              // Left Row 2
              {KeySpecial, SpecialAction::KeymapNext},
              {Key::Q, 0},
              {Key::W, 0},
              {Key::E, 0},
              {Key::R, 0},
              {Key::T, 0},
              {Key::ScrollLock, 0},
              {Key::Backspace, 0},

              // Left Row 3
              {Key::LeftControl, Modifier::LeftControl},
              {Key::A, 0},
              {Key::S, 0},
              {Key::D, 0},
              {Key::F, 0},
              {Key::G, 0},
              {Key::Pause, 0},
              {Key::None, 0}, // Not connected

              // Left Row 4
              {Key::LeftShift, Modifier::LeftShift},
              {Key::Z, 0},
              {Key::X, 0},
              {Key::C, 0},
              {Key::V, 0},
              {Key::B, 0},
              {Key::PageUp, 0},
              {Key::None, 0}, // Not connected

              // Left Row 5
              {Key::None, 0},
              {Key::Home, 0},
              {Key::Backslash, 0},
              {Key::BracketLeft, 0},
              {Key::Minus, 0},
              {Key::Enter, 0},
              {Key::LeftGui, Modifier::LeftGui},
              {Key::Up, 0},

              // Right Row 0
              {Key::F12, 0},
              {Key::F11, 0},
              {Key::F10, 0},
              {Key::F9, 0},
              {Key::F8, 0},
              {Key::F7, 0},
              {Key::RightAlt, Modifier::RightAlt}, // thumb top center
              {Key::Insert, 0},                    // thumb top left

              // Right Row 1
              {Key::Tilde, 0},
              {Key::Num0, 0},
              {Key::Num9, 0},
              {Key::Num8, 0},
              {Key::Num7, 0},
              {Key::Num6, 0},
              {Key::RightGui, Modifier::RightGui}, // thumb center
              {Key::Right, 0},                     // thumb center left

              // Right Row 2
              {KeySpecial, SpecialAction::KeymapPrev},
              {Key::P, 0},
              {Key::O, 0},
              {Key::Up, 0},
              {Key::U, 0},
              {Key::Y, 0},
              {Key::NumLock, 0},
              {Key::Delete, 0}, // thumb top right

              // Right Row 3
              {Key::RightControl, Modifier::RightControl},
              {Key::Enter, 0},
              {Key::Right, 0},
              {Key::Down, 0},
              {Key::Left, 0},
              {Key::H, 0},
              {Key::PrintScreen, 0},
              {Key::None, 0}, // Not connected

              // Right Row 4
              {Key::RightShift, Modifier::RightShift},
              {Key::Quote, 0},
              {Key::Period, 0},
              {Key::Comma, 0},
              {Key::Keypad0, 0},
              {Key::N, 0},
              {Key::PageDown, 0},
              {Key::None, 0}, // Not connected

              // Right Row 5
              {Key::None, 0},
              {Key::End, 0},
              {Key::Slash, 0},
              {Key::BracketRight, 0},
              {Key::Equal, 0},
              {Key::LeftShift, Modifier::LeftShift},     // thumb bottom right
              {Key::LeftControl, Modifier::LeftControl}, // thumb bottom middle
              {Key::Down, 0}                             // thumb bottom left
          }}),
      numpad_("Numpad",
              {{
                  // Left Row 0
                  {Key::F1, 0},
                  {Key::F2, 0},
                  {Key::F3, 0},
                  {Key::F4, 0},
                  {Key::F5, 0},
                  {Key::F6, 0},
                  {Key::LeftAlt, Modifier::LeftAlt},
                  {Key::SysReq, 0},

                  // Left Row 1
                  {KeySpecial, SpecialAction::Keymap0},
                  {Key::Num1, 0},
                  {Key::Num2, 0},
                  {Key::Num3, 0},
                  {Key::Num4, 0},
                  {Key::Num5, 0},
                  {Key::Escape, 0},
                  {Key::Left, 0},

                  // Left Row 2
                  {KeySpecial, SpecialAction::KeymapNext},
                  {Key::Q, 0},
                  {Key::W, 0},
                  {Key::E, 0},
                  {Key::R, 0},
                  {Key::T, 0},
                  {Key::ScrollLock, 0},
                  {Key::Backspace, 0},

                  // Left Row 3
                  {Key::LeftControl, Modifier::LeftControl},
                  {Key::A, 0},
                  {Key::S, 0},
                  {Key::D, 0},
                  {Key::F, 0},
                  {Key::G, 0},
                  {Key::Pause, 0},
                  {Key::None, 0}, // Not connected

                  // Left Row 4
                  {Key::LeftShift, Modifier::LeftShift},
                  {Key::Z, 0},
                  {Key::X, 0},
                  {Key::C, 0},
                  {Key::V, 0},
                  {Key::B, 0},
                  {Key::PageUp, 0},
                  {Key::None, 0}, // Not connected

                  // Left Row 5
                  {Key::None, 0},
                  {Key::Home, 0},
                  {Key::Backslash, 0},
                  {Key::BracketLeft, 0},
                  {Key::Minus, 0},
                  {Key::Enter, 0},
                  {Key::LeftGui, Modifier::LeftGui},
                  {Key::Up, 0},

                  // Right Row 0
                  {Key::F12, 0},
                  {Key::F11, 0},
                  {Key::F10, 0},
                  {Key::F9, 0},
                  {Key::F8, 0},
                  {Key::F7, 0},
                  {Key::RightAlt, Modifier::RightAlt}, // thumb top center
                  {Key::Insert, 0},                    // thumb top left

                  // Right Row 1
                  {Key::Tilde, 0},
                  {Key::Num0, 0},
                  {Key::Keypad9, 0},
                  {Key::Keypad8, 0},
                  {Key::Keypad7, 0},
                  {Key::Num6, 0},
                  {Key::RightGui, Modifier::RightGui}, // thumb center
                  {Key::Right, 0},                     // thumb center left

                  // Right Row 2
                  {KeySpecial, SpecialAction::KeymapPrev},
                  {Key::P, 0},
                  {Key::Keypad6, 0},
                  {Key::Keypad5, 0},
                  {Key::Keypad4, 0},
                  {Key::Y, 0},
                  {Key::NumLock, 0},
                  {Key::Delete, 0}, // thumb top right

                  // Right Row 3
                  {Key::RightControl, Modifier::RightControl},
                  {Key::KeypadEnter, 0},
                  {Key::Keypad3, 0},
                  {Key::Keypad2, 0},
                  {Key::Keypad1, 0},
                  {Key::H, 0},
                  {Key::PrintScreen, 0},
                  {Key::None, 0}, // Not connected

                  // Right Row 4
                  {Key::RightShift, Modifier::RightShift},
                  {Key::Quote, 0},
                  {Key::Period, 0},
                  {Key::Comma, 0},
                  {Key::Keypad0, 0},
                  {Key::N, 0},
                  {Key::PageDown, 0},
                  {Key::None, 0}, // Not connected

                  // Right Row 5
                  {Key::None, 0},
                  {Key::End, 0},
                  {Key::Slash, 0},
                  {Key::BracketRight, 0},
                  {Key::Equal, 0},
                  {Key::Space, 0}, // thumb bottom right
                  {Key::Tab, 0},   // thumb bottom middle
                  {Key::Down, 0}   // thumb bottom left
              }}) {}

void KeymapDB::next_keymap() {
  ++current_index_;
  if (current_index_ >= keymaps_.size()) {
    current_index_ = 0;
  }
  on_keymap_change();
}

void KeymapDB::prev_keymap() {
  if (current_index_ == 0) {
    current_index_ = keymaps_.size() - 1;
  } else {
    --current_index_;
  }
  on_keymap_change();
}

void KeymapDB::set_keymap(size_t index) {
  if (index < keymaps_.size()) {
    current_index_ = index;
    on_keymap_change();
  } else {
    ESP_LOGW(LogTag, "keymap %zu does not exist", index);
  }
}

void KeymapDB::on_keymap_change() {
  ESP_LOGI(LogTag,
           "changed to keymap %zu: %s",
           current_index_,
           current_keymap().name().c_str());
}

} // namespace mantyl
