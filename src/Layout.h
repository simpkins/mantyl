// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "usb_hid_keyboard.h"

#include <array>
#include <cstdint>

namespace ocb {

enum class Location : uint8_t {
  LeftMain = 1,
  LeftThumb = 2,
  RightMain = 3,
  RightThumb = 4,
};

class PhysicalPosition {
public:
  Location location;
  uint8_t col{0};
  uint8_t row{0};
};

class PhysicalKey;

class KeyMatrixBase {
};

template<uint8_t TColumns, uint8_t TRows>
class KeyMatrix : public KeyMatrixBase {
public:
  static constexpr uint8_t kNumColumns = TColumns;
  static constexpr uint8_t kNumRows = TRows;

  KeyMatrix() : keys_{} {}
  explicit KeyMatrix(const std::array<std::array<const PhysicalKey *, kNumRows>,
                                      kNumColumns> &m)
      : keys_(m) {}

  void addKey(const PhysicalKey& key, uint8_t col, uint8_t row) {
    if (col >= kNumColumns || row < kNumRows) {
      throw std::out_of_range("invalid key matrix position");
    }

    if (keys_[col][row] != nullptr) {
      throw std::invalid_argument(
          "multiple keys defined at one matrix position");
    }
  }

  std::array<std::array<const PhysicalKey*, kNumRows>, kNumColumns> keys_;
};

template<uint8_t N>
class KeyArray {
public:
  KeyArray() : keys_{} {}
  explicit KeyArray(const std::array<const PhysicalKey *, N> &m)
      : keys_(m) {}

  std::array<const PhysicalKey *, N> keys_;
};

template <typename... T>
constexpr auto makeKeyArray(T &&... t)
    -> std::enable_if_t<(std::is_convertible_v<T, const PhysicalKey *> && ...),
                        KeyArray<sizeof...(T)>> {
  std::array<const PhysicalKey *, sizeof...(T)> m = {t...};
  return KeyArray<sizeof...(T)>(m);
}

template <uint8_t C, uint8_t R, typename... T>
constexpr auto makeKeyMatrix_v1(T &&... t) -> std::enable_if_t<
    (std::is_convertible_v<T, std::array<const PhysicalKey *, R>> && ...),
    KeyMatrix<C, R>> {
  std::array<std::array<const PhysicalKey *, R>, C> m = {t...};
  return KeyMatrix<C, R>(m);
}

template <uint8_t C, uint8_t R, typename... T>
constexpr auto makeKeyMatrix(std::initializer_list<T> &&... t) -> std::enable_if_t<
    (std::is_convertible_v<T, const PhysicalKey *> && ...),
    KeyMatrix<C, R>> {
  std::array<std::array<const PhysicalKey *, R>, C> m = {std::array<const PhysicalKey*, R>{t}...};
  return KeyMatrix<C, R>(m);
}

class ScanPosition {
public:
  const KeyMatrixBase& matrix;
  uint8_t col{0};
  uint8_t row{0};
};

/**
 * A matrix of keys connected electrically in columns and rows.
 *
 * My keyboard has multiple separate matrices, each scanned independently
 */

class PhysicalKey {
public:
  template <uint8_t R, uint8_t C>
  PhysicalKey(Location loc, uint8_t phys_col, uint8_t phys_row,
              KeyMatrix<R, C> &matrix, uint8_t scan_col, uint8_t scan_row)
      : phys_{loc, phys_col, phys_row}, scan_{matrix, scan_col, scan_row} {
    matrix.addKey(*this, scan_col, scan_row);
  }

  PhysicalPosition phys_;
  ScanPosition scan_;
};

class KbdV1 {
public:
  void qwertyKeymap();
  void gamingKeymap();

private:
  // 46 keys on left section:
  // - 38 in main section
  // - 8 keys in thumb
  //
  // We use a 6x8 scan matrix

  KeyMatrix<8, 6> left_;
  KeyMatrix<8, 6> right_;

  /*
   * Left main keys
   */
  PhysicalKey L00{Location::LeftMain, 0, 0, left_, 0, 0};
  PhysicalKey L01{Location::LeftMain, 0, 1, left_, 0, 1};
  PhysicalKey L02{Location::LeftMain, 0, 2, left_, 0, 2};
  PhysicalKey L03{Location::LeftMain, 0, 3, left_, 0, 3};
  PhysicalKey L04{Location::LeftMain, 0, 4, left_, 0, 4};
  PhysicalKey L05{Location::LeftMain, 0, 5, left_, 0, 5};

  PhysicalKey L10{Location::LeftMain, 1, 0, left_, 1, 0};
  PhysicalKey L11{Location::LeftMain, 1, 1, left_, 1, 1};
  PhysicalKey L12{Location::LeftMain, 1, 2, left_, 1, 2};
  PhysicalKey L13{Location::LeftMain, 1, 3, left_, 1, 3};
  PhysicalKey L14{Location::LeftMain, 1, 4, left_, 1, 4};
  PhysicalKey L15{Location::LeftMain, 1, 5, left_, 1, 5};

  PhysicalKey L20{Location::LeftMain, 2, 0, left_, 2, 0};
  PhysicalKey L21{Location::LeftMain, 2, 1, left_, 2, 1};
  PhysicalKey L22{Location::LeftMain, 2, 2, left_, 2, 2};
  PhysicalKey L23{Location::LeftMain, 2, 3, left_, 2, 3};
  PhysicalKey L24{Location::LeftMain, 2, 4, left_, 2, 4};
  PhysicalKey L25{Location::LeftMain, 2, 5, left_, 2, 5};

  PhysicalKey L30{Location::LeftMain, 3, 0, left_, 3, 0};
  PhysicalKey L31{Location::LeftMain, 3, 1, left_, 3, 1};
  PhysicalKey L32{Location::LeftMain, 3, 2, left_, 3, 2};
  PhysicalKey L33{Location::LeftMain, 3, 3, left_, 3, 3};
  PhysicalKey L34{Location::LeftMain, 3, 4, left_, 3, 4};
  PhysicalKey L35{Location::LeftMain, 3, 5, left_, 3, 5};

  PhysicalKey L40{Location::LeftMain, 4, 0, left_, 4, 0};
  PhysicalKey L41{Location::LeftMain, 4, 1, left_, 4, 1};
  PhysicalKey L42{Location::LeftMain, 4, 2, left_, 4, 2};
  PhysicalKey L43{Location::LeftMain, 4, 3, left_, 4, 3};
  PhysicalKey L44{Location::LeftMain, 4, 4, left_, 4, 4};
  PhysicalKey L45{Location::LeftMain, 4, 5, left_, 4, 5};

  PhysicalKey L50{Location::LeftMain, 5, 0, left_, 5, 0};
  PhysicalKey L51{Location::LeftMain, 5, 1, left_, 5, 1};
  PhysicalKey L52{Location::LeftMain, 5, 2, left_, 5, 2};
  PhysicalKey L53{Location::LeftMain, 5, 3, left_, 5, 3};
  PhysicalKey L54{Location::LeftMain, 5, 4, left_, 5, 4};

  PhysicalKey L62{Location::LeftMain, 6, 2, left_, 6, 2};
  PhysicalKey L63{Location::LeftMain, 6, 3, left_, 6, 3};
  PhysicalKey L64{Location::LeftMain, 6, 4, left_, 6, 4};

  /*
   * Left thumb keys
   */
  PhysicalKey LT00{Location::LeftThumb, 0, 0, left_, 6, 5};
  PhysicalKey LT01{Location::LeftThumb, 0, 1, left_, 5, 5};
  PhysicalKey LT10{Location::LeftThumb, 1, 0, left_, 6, 1};
  PhysicalKey LT11{Location::LeftThumb, 1, 1, left_, 7, 1};
  PhysicalKey LT12{Location::LeftThumb, 1, 2, left_, 7, 3};
  PhysicalKey LT20{Location::LeftThumb, 2, 0, left_, 6, 0};
  PhysicalKey LT21{Location::LeftThumb, 2, 1, left_, 7, 0};
  PhysicalKey LT22{Location::LeftThumb, 2, 2, left_, 7, 2};

  /*
   * Right main keys
   * These are mirrors of the left keys
   */
  PhysicalKey R60{Location::RightMain, 6, 0, right_, 0, 0};
  PhysicalKey R61{Location::RightMain, 6, 1, right_, 0, 1};
  PhysicalKey R62{Location::RightMain, 6, 2, right_, 0, 2};
  PhysicalKey R63{Location::RightMain, 6, 3, right_, 0, 3};
  PhysicalKey R64{Location::RightMain, 6, 4, right_, 0, 4};
  PhysicalKey R65{Location::RightMain, 6, 5, right_, 0, 5};

  PhysicalKey R50{Location::RightMain, 5, 0, right_, 1, 0};
  PhysicalKey R51{Location::RightMain, 5, 1, right_, 1, 1};
  PhysicalKey R52{Location::RightMain, 5, 2, right_, 1, 2};
  PhysicalKey R53{Location::RightMain, 5, 3, right_, 1, 3};
  PhysicalKey R54{Location::RightMain, 5, 4, right_, 1, 4};
  PhysicalKey R55{Location::RightMain, 5, 5, right_, 1, 5};

  PhysicalKey R40{Location::RightMain, 4, 0, right_, 2, 0};
  PhysicalKey R41{Location::RightMain, 4, 1, right_, 2, 1};
  PhysicalKey R42{Location::RightMain, 4, 2, right_, 2, 2};
  PhysicalKey R43{Location::RightMain, 4, 3, right_, 2, 3};
  PhysicalKey R44{Location::RightMain, 4, 4, right_, 2, 4};
  PhysicalKey R45{Location::RightMain, 4, 5, right_, 2, 5};

  PhysicalKey R30{Location::RightMain, 3, 0, right_, 3, 0};
  PhysicalKey R31{Location::RightMain, 3, 1, right_, 3, 1};
  PhysicalKey R32{Location::RightMain, 3, 2, right_, 3, 2};
  PhysicalKey R33{Location::RightMain, 3, 3, right_, 3, 3};
  PhysicalKey R34{Location::RightMain, 3, 4, right_, 3, 4};
  PhysicalKey R35{Location::RightMain, 3, 5, right_, 3, 5};

  PhysicalKey R20{Location::RightMain, 2, 0, right_, 4, 0};
  PhysicalKey R21{Location::RightMain, 2, 1, right_, 4, 1};
  PhysicalKey R22{Location::RightMain, 2, 2, right_, 4, 2};
  PhysicalKey R23{Location::RightMain, 2, 3, right_, 4, 3};
  PhysicalKey R24{Location::RightMain, 2, 4, right_, 4, 4};
  PhysicalKey R25{Location::RightMain, 2, 5, right_, 4, 5};

  PhysicalKey R10{Location::RightMain, 1, 0, right_, 5, 0};
  PhysicalKey R11{Location::RightMain, 1, 1, right_, 5, 1};
  PhysicalKey R12{Location::RightMain, 1, 2, right_, 5, 2};
  PhysicalKey R13{Location::RightMain, 1, 3, right_, 5, 3};
  PhysicalKey R14{Location::RightMain, 1, 4, right_, 5, 4};

  PhysicalKey R02{Location::RightMain, 0, 2, right_, 6, 2};
  PhysicalKey R03{Location::RightMain, 0, 3, right_, 6, 3};
  PhysicalKey R04{Location::RightMain, 0, 4, right_, 6, 4};

  /*
   * Right thumb keys
   */
  PhysicalKey RT20{Location::RightThumb, 2, 0, right_, 6, 5};
  PhysicalKey RT21{Location::RightThumb, 2, 1, right_, 5, 5};
  PhysicalKey RT10{Location::RightThumb, 1, 0, right_, 6, 1};
  PhysicalKey RT11{Location::RightThumb, 1, 1, right_, 7, 1};
  PhysicalKey RT12{Location::RightThumb, 1, 2, right_, 7, 3};
  PhysicalKey RT00{Location::RightThumb, 0, 0, right_, 6, 0};
  PhysicalKey RT01{Location::RightThumb, 0, 1, right_, 7, 0};
  PhysicalKey RT02{Location::RightThumb, 0, 2, right_, 7, 2};

  /*
   * Scan matrices
   */
  const KeyMatrix<6, 8> left2_{
      std::array<std::array<const PhysicalKey *, 8>, 6>{{
          {&L00, &L10, &L20, &L30, &L40, &L50, &LT20, &LT21},
          {&L01, &L11, &L21, &L31, &L41, &L51, &LT10, &LT11},
          {&L02, &L12, &L22, &L32, &L42, &L52, &L62, &LT22},
          {&L03, &L13, &L23, &L33, &L43, &L53, &L63, &LT12},
          {&L04, &L14, &L24, &L34, &L44, &L54, &L64, nullptr},
          {&L05, &L15, &L25, &L35, &L45, &LT01, &LT00, nullptr},
      }}};
};

} // namespace ocb
