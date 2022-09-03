// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <cstdint>
#include <string_view>

namespace mantyl {

struct Glyph {
  /**
   * The width of this glyph, in pixels.
   *
   * The maximum width of any glyph is 5 pixels wide.  (When rendering a word,
   * up to 6 pixels are necessary per glyph, since one additional pixel is
   * required for spacing between glyphs.)
   */
  uint8_t width;
  /**
   * The glyph data.
   *
   * This is points to an array of uint8_t values, one for each pixel of width.
   * Each byte represents one column of the glyph, with the LSB being the top
   * pixel, and the MSB being the bottom pixel.
   *
   * The bottom row of pixels is usually empty, but descenders (p, q, j, etc)
   * can descend into it.
   */
  const uint8_t *data;
};

/*
 * A variable-width 8-pixel high font.
 * Characters are no wider than 6 pixels.
 *
 * This provides ASCII characters, plus some symbols and line drawing
 * characters from Code Page 437.
 */
class Font6x8 {
public:
  static const Glyph& lookupGlyph(char c);

  /**
   * Compute the width of a glyph.
   *
   * Note: this returns the width of just the character itself.
   * When rendering a string, an extra pixel of spacing is required between
   * each character.
   */
  static size_t computeWidth(char c);

  /**
   * Compute the width of a string.
   *
   * This returns the exact width required just for the text.
   * If additional text will be rendered after this string, an extra pixel of
   * spacing should be placed afterwards.
   */
  static size_t computeWidth(std::string_view str);
};

} // namespace mantyl
