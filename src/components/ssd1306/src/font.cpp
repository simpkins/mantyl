// Copyright (c) 2022, Adam Simpkins
#include "font.h"

#include <array>
#include <cstddef>
#include <cstdint>

namespace {

using Font = std::array<mantyl::Glyph, 128>;

const uint8_t font_data_space[] = {0x00, 0x00};
const uint8_t font_data_bang[] = {0x06, 0x6f, 0x06};
const uint8_t font_data_double_quote[] = {0x07, 0x00, 0x07};
const uint8_t font_data_hash[] = {0x24, 0x7e, 0x24, 0x7e, 0x24};
const uint8_t font_data_dollar[] = {0x24, 0x2a, 0x6b, 0x2a, 0x12};
const uint8_t font_data_percent[] = {0x63, 0x13, 0x08, 0x64, 0x63};
const uint8_t font_data_ampersand[] = {0x36, 0x49, 0x56, 0x20, 0x50};
const uint8_t font_data_single_quote[] = {0x07};
const uint8_t font_data_open_paren[] = {0x3e, 0x41};
const uint8_t font_data_close_paren[] = {0x41, 0x3e};
const uint8_t font_data_star[] = {0x2a, 0x1c, 0x7f, 0x1c, 0x2a};
const uint8_t font_data_plus[] = {0x08, 0x08, 0x3e, 0x08, 0x08};
const uint8_t font_data_comma[] = {0xe0, 0x60};
const uint8_t font_data_minus[] = {0x08, 0x08, 0x08, 0x08, 0x08};
const uint8_t font_data_period[] = {0x60, 0x60};
const uint8_t font_data_slash[] = {0x60, 0x18, 0x0c, 0x03};

const uint8_t font_data_0[] = {0x3e, 0x51, 0x49, 0x45, 0x3e};
const uint8_t font_data_1[] = {0x42, 0x7f, 0x40};
const uint8_t font_data_2[] = {0x42, 0x61, 0x51, 0x49, 0x46};
const uint8_t font_data_3[] = {0x22, 0x41, 0x49, 0x49, 0x36};
const uint8_t font_data_4[] = {0x18, 0x14, 0x12, 0x7f, 0x10};
// Alternate square 4
// const uint8_t font_data_4[] = {0x1f, 0x10, 0x10, 0x7f, 0x10};
const uint8_t font_data_5[] = {0x2f, 0x49, 0x49, 0x49, 0x31};
const uint8_t font_data_6[] = {0x3c, 0x4a, 0x49, 0x49, 0x30};
const uint8_t font_data_7[] = {0x01, 0x71, 0x09, 0x05, 0x03};
const uint8_t font_data_8[] = {0x36, 0x49, 0x49, 0x49, 0x36};
const uint8_t font_data_9[] = {0x06, 0x49, 0x49, 0x29, 0x1e};

const uint8_t font_data_colon[] = {0x36, 0x36};
const uint8_t font_data_semicolon[] = {0x76, 0x36};
// const uint8_t font_data_semicolon[] = {0x40, 0x36, 0x36};
const uint8_t font_data_left_angle[] = {0x08, 0x14, 0x22, 0x41};
// const uint8_t font_data_equal[] = {0x36, 0x36, 0x36, 0x36};
const uint8_t font_data_equal[] = {0x24, 0x24, 0x24, 0x24, 0x24};
const uint8_t font_data_right_angle[] = {0x41, 0x22, 0x14, 0x08};
const uint8_t font_data_question[] = {0x02, 0x01, 0x51, 0x09, 0x06};
const uint8_t font_data_at[] = {0x3e, 0x41, 0x5d, 0x55, 0x1e};

const uint8_t font_data_A[] = {0x7e, 0x11, 0x11, 0x11, 0x7e};
const uint8_t font_data_B[] = {0x7f, 0x49, 0x49, 0x49, 0x36};
const uint8_t font_data_C[] = {0x3e, 0x41, 0x41, 0x41, 0x22};
const uint8_t font_data_D[] = {0x7f, 0x41, 0x41, 0x41, 0x3e};
const uint8_t font_data_E[] = {0x7f, 0x49, 0x49, 0x49, 0x49};
const uint8_t font_data_F[] = {0x7f, 0x09, 0x09, 0x09, 0x09};
const uint8_t font_data_G[] = {0x3e, 0x41, 0x49, 0x49, 0x7a};
const uint8_t font_data_H[] = {0x7f, 0x08, 0x08, 0x08, 0x7f};
const uint8_t font_data_I[] = {0x41, 0x41, 0x7f, 0x41, 0x41};
const uint8_t font_data_J[] = {0x30, 0x40, 0x40, 0x40, 0x3f};
const uint8_t font_data_K[] = {0x7f, 0x08, 0x14, 0x22, 0x41};
const uint8_t font_data_L[] = {0x7f, 0x40, 0x40, 0x40, 0x40};
const uint8_t font_data_M[] = {0x7f, 0x02, 0x04, 0x02, 0x7f};
const uint8_t font_data_N[] = {0x7f, 0x02, 0x04, 0x08, 0x7f};
const uint8_t font_data_O[] = {0x3e, 0x41, 0x41, 0x41, 0x3e};
const uint8_t font_data_P[] = {0x7f, 0x09, 0x09, 0x09, 0x06};
const uint8_t font_data_Q[] = {0x3e, 0x41, 0x51, 0x21, 0x5e};
const uint8_t font_data_R[] = {0x7f, 0x09, 0x19, 0x29, 0x46};
const uint8_t font_data_S[] = {0x26, 0x49, 0x49, 0x49, 0x32};
const uint8_t font_data_T[] = {0x01, 0x01, 0x7f, 0x01, 0x01};
const uint8_t font_data_U[] = {0x3f, 0x40, 0x40, 0x40, 0x3f};
const uint8_t font_data_V[] = {0x3f, 0x20, 0x40, 0x20, 0x3f};
const uint8_t font_data_W[] = {0x3f, 0x40, 0x3c, 0x40, 0x3f};
const uint8_t font_data_X[] = {0x63, 0x14, 0x08, 0x14, 0x63};
const uint8_t font_data_Y[] = {0x07, 0x08, 0x70, 0x08, 0x07};
const uint8_t font_data_Z[] = {0x61, 0x51, 0x49, 0x45, 0x43};

const uint8_t font_data_left_bracket[] = {0x7f, 0x41};
const uint8_t font_data_backslash[] = {0x03, 0x0c, 0x18, 0x60};
const uint8_t font_data_right_bracket[] = {0x41, 0x7f};
const uint8_t font_data_carat[] = {0x04, 0x02, 0x01, 0x02, 0x04};
const uint8_t font_data_underscore[] = {0x04, 0x04, 0x04, 0x04, 0x04};
const uint8_t font_data_backtick[] = {0x01, 0x03, 0x06};

const uint8_t font_data_a[] = {0x20, 0x54, 0x54, 0x54, 0x78};
const uint8_t font_data_b[] = {0x7f, 0x44, 0x44, 0x44, 0x38};
const uint8_t font_data_c[] = {0x38, 0x44, 0x44, 0x44, 0x28};
const uint8_t font_data_d[] = {0x38, 0x44, 0x44, 0x44, 0x7f};
const uint8_t font_data_e[] = {0x38, 0x54, 0x54, 0x54, 0x08};
const uint8_t font_data_f[] = {0x08, 0x7e, 0x09, 0x09};
const uint8_t font_data_g[] = {0x18, 0xa4, 0xa4, 0xa4, 0x7c};
const uint8_t font_data_h[] = {0x7f, 0x04, 0x04, 0x04, 0x78};
const uint8_t font_data_i[] = {0x7a, 0x40};
const uint8_t font_data_j[] = {0x40, 0x80, 0x84, 0x7d};
const uint8_t font_data_k[] = {0x7f, 0x10, 0x28, 0x44};
const uint8_t font_data_l[] = {0x7f, 0x40};
const uint8_t font_data_m[] = {0x7c, 0x04, 0x78, 0x04, 0x78};
const uint8_t font_data_n[] = {0x7c, 0x04, 0x04, 0x04, 0x78};
const uint8_t font_data_o[] = {0x38, 0x44, 0x44, 0x44, 0x38};
const uint8_t font_data_p[] = {0xf8, 0x24, 0x24, 0x24, 0x18};
const uint8_t font_data_q[] = {0x18, 0x24, 0x24, 0x24, 0xf8};
const uint8_t font_data_r[] = {0x04, 0x78, 0x04, 0x04, 0x08};
const uint8_t font_data_s[] = {0x08, 0x54, 0x54, 0x54, 0x20};
const uint8_t font_data_t[] = {0x04, 0x3f, 0x44, 0x44, 0x20};
const uint8_t font_data_u[] = {0x3c, 0x40, 0x40, 0x20, 0x7c};
const uint8_t font_data_v[] = {0x1c, 0x20, 0x40, 0x20, 0x1c};
const uint8_t font_data_w[] = {0x3c, 0x40, 0x30, 0x40, 0x3c};
const uint8_t font_data_x[] = {0x44, 0x28, 0x10, 0x28, 0x44};
const uint8_t font_data_y[] = {0x1c, 0xa0, 0xa0, 0xa0, 0x7c};
const uint8_t font_data_z[] = {0x44, 0x64, 0x54, 0x4c, 0x44};

const uint8_t font_data_left_brace[] = {0x08, 0x3e, 0x41, 0x41};
const uint8_t font_data_pipe[] = {0x7f};
const uint8_t font_data_right_brace[] = {0x41, 0x41, 0x3e, 0x08};
const uint8_t font_data_tilde[] = {0x08, 0x04, 0x08, 0x10, 0x08};

const uint8_t font_data_unknown[] = {0x7f, 0x41, 0x41, 0x41, 0x7f};

template<size_t N>
constexpr mantyl::Glyph make_glyph(const uint8_t (&data)[N]) {
  return mantyl::Glyph{N, data};
}

constexpr mantyl::Glyph unknown_glyph = make_glyph(font_data_unknown);

constexpr Font make_font() {
    Font font = {};

    font['\x00'] = unknown_glyph;
    font['\x01'] = unknown_glyph;
    font['\x02'] = unknown_glyph;
    font['\x03'] = unknown_glyph;
    font['\x04'] = unknown_glyph;
    font['\x05'] = unknown_glyph;
    font['\x06'] = unknown_glyph;
    font['\x07'] = unknown_glyph;
    font['\x08'] = unknown_glyph;
    font['\x09'] = unknown_glyph;
    font['\x0a'] = unknown_glyph;
    font['\x0b'] = unknown_glyph;
    font['\x0c'] = unknown_glyph;
    font['\x0d'] = unknown_glyph;
    font['\x0e'] = unknown_glyph;
    font['\x0f'] = unknown_glyph;
    font['\x10'] = unknown_glyph;
    font['\x11'] = unknown_glyph;
    font['\x12'] = unknown_glyph;
    font['\x13'] = unknown_glyph;
    font['\x14'] = unknown_glyph;
    font['\x15'] = unknown_glyph;
    font['\x16'] = unknown_glyph;
    font['\x17'] = unknown_glyph;
    font['\x18'] = unknown_glyph;
    font['\x19'] = unknown_glyph;
    font['\x1a'] = unknown_glyph;
    font['\x1b'] = unknown_glyph;
    font['\x1c'] = unknown_glyph;
    font['\x1d'] = unknown_glyph;
    font['\x1e'] = unknown_glyph;
    font['\x1f'] = unknown_glyph;

    font[' '] = make_glyph(font_data_space);
    font['!'] = make_glyph(font_data_bang);
    font['"'] = make_glyph(font_data_double_quote);
    font['#'] = make_glyph(font_data_hash);
    font['$'] = make_glyph(font_data_dollar);
    font['%'] = make_glyph(font_data_percent);
    font['&'] = make_glyph(font_data_ampersand);
    font['\''] = make_glyph(font_data_single_quote);
    font['('] = make_glyph(font_data_open_paren);
    font[')'] = make_glyph(font_data_close_paren);
    font['*'] = make_glyph(font_data_star);
    font['+'] = make_glyph(font_data_plus);
    font[','] = make_glyph(font_data_comma);
    font['-'] = make_glyph(font_data_minus);
    font['.'] = make_glyph(font_data_period);
    font['/'] = make_glyph(font_data_slash);

    font['0'] = make_glyph(font_data_0);
    font['1'] = make_glyph(font_data_1);
    font['2'] = make_glyph(font_data_2);
    font['3'] = make_glyph(font_data_3);
    font['4'] = make_glyph(font_data_4);
    font['5'] = make_glyph(font_data_5);
    font['6'] = make_glyph(font_data_6);
    font['7'] = make_glyph(font_data_7);
    font['8'] = make_glyph(font_data_8);
    font['9'] = make_glyph(font_data_9);

    font[':'] = make_glyph(font_data_colon);
    font[';'] = make_glyph(font_data_semicolon);
    font['<'] = make_glyph(font_data_left_angle);
    font['='] = make_glyph(font_data_equal);
    font['>'] = make_glyph(font_data_right_angle);
    font['?'] = make_glyph(font_data_question);
    font['@'] = make_glyph(font_data_at);

    font['A'] = make_glyph(font_data_A);
    font['B'] = make_glyph(font_data_B);
    font['C'] = make_glyph(font_data_C);
    font['D'] = make_glyph(font_data_D);
    font['E'] = make_glyph(font_data_E);
    font['F'] = make_glyph(font_data_F);
    font['G'] = make_glyph(font_data_G);
    font['H'] = make_glyph(font_data_H);
    font['I'] = make_glyph(font_data_I);
    font['J'] = make_glyph(font_data_J);
    font['K'] = make_glyph(font_data_K);
    font['L'] = make_glyph(font_data_L);
    font['M'] = make_glyph(font_data_M);
    font['N'] = make_glyph(font_data_N);
    font['O'] = make_glyph(font_data_O);
    font['P'] = make_glyph(font_data_P);
    font['Q'] = make_glyph(font_data_Q);
    font['R'] = make_glyph(font_data_R);
    font['S'] = make_glyph(font_data_S);
    font['T'] = make_glyph(font_data_T);
    font['U'] = make_glyph(font_data_U);
    font['V'] = make_glyph(font_data_V);
    font['W'] = make_glyph(font_data_W);
    font['X'] = make_glyph(font_data_X);
    font['Y'] = make_glyph(font_data_Y);
    font['Z'] = make_glyph(font_data_Z);

    font['['] = make_glyph(font_data_left_bracket);
    font['\\'] = make_glyph(font_data_backslash);
    font[']'] = make_glyph(font_data_right_bracket);
    font['^'] = make_glyph(font_data_carat);
    font['_'] = make_glyph(font_data_underscore);
    font['`'] = make_glyph(font_data_backtick);

    font['a'] = make_glyph(font_data_a);
    font['b'] = make_glyph(font_data_b);
    font['c'] = make_glyph(font_data_c);
    font['d'] = make_glyph(font_data_d);
    font['e'] = make_glyph(font_data_e);
    font['f'] = make_glyph(font_data_f);
    font['g'] = make_glyph(font_data_g);
    font['h'] = make_glyph(font_data_h);
    font['i'] = make_glyph(font_data_i);
    font['j'] = make_glyph(font_data_j);
    font['k'] = make_glyph(font_data_k);
    font['l'] = make_glyph(font_data_l);
    font['m'] = make_glyph(font_data_m);
    font['n'] = make_glyph(font_data_n);
    font['o'] = make_glyph(font_data_o);
    font['p'] = make_glyph(font_data_p);
    font['q'] = make_glyph(font_data_q);
    font['r'] = make_glyph(font_data_r);
    font['s'] = make_glyph(font_data_s);
    font['t'] = make_glyph(font_data_t);
    font['u'] = make_glyph(font_data_u);
    font['v'] = make_glyph(font_data_v);
    font['w'] = make_glyph(font_data_w);
    font['x'] = make_glyph(font_data_x);
    font['y'] = make_glyph(font_data_y);
    font['z'] = make_glyph(font_data_z);

    font['{'] = make_glyph(font_data_left_brace);
    font['|'] = make_glyph(font_data_pipe);
    font['}'] = make_glyph(font_data_right_brace);
    font['~'] = make_glyph(font_data_tilde);
    font['\x7f'] = unknown_glyph;

    return font;
}

constexpr Font font = make_font();
} // namespace

namespace mantyl {

const Glyph &Font6x8::lookupGlyph(char c) {
  const auto idx = static_cast<unsigned char>(c);
  if (idx < font.size()) {
    return font[idx];
  }
  return unknown_glyph;
}

size_t Font6x8::computeWidth(char c) {
  return lookupGlyph(c).width;
}

size_t Font6x8::computeWidth(std::string_view str) {
  size_t width = 0;
  if (str.empty()) {
    return 0;
  }
  for (const char c : str) {
    width += lookupGlyph(c).width + 1;
  }
  // We don't actually need the extra space after the last character.
  return width - 1;
}

} // namespace mantyl
