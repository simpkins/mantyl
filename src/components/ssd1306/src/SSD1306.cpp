// Copyright (c) 2022, Adam Simpkins
#include "SSD1306.h"

#include "mantyl_literals.h"

#include <driver/gpio.h>
#include <esp_check.h>
#include <string.h>

namespace {
const char *LogTag = "mantyl.ssd1306";

struct font_char_info {
    uint8_t width;
    const uint8_t* data;
};

using Font = std::array<font_char_info, 256>;

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


const uint8_t font_data_space[] = {0x00, 0x00};
const uint8_t font_data_bang[] = {0x06, 0x6f, 0x06};
const uint8_t font_data_double_quote[] = {0x03, 0x00, 0x03};
const uint8_t font_data_hash[] = {0x24, 0x7e, 0x24, 0x7e, 0x24};
const uint8_t font_data_dollar[] = {0x24, 0x2a, 0x6b, 0x2a, 0x12};
const uint8_t font_data_percent[] = {0x63, 0x13, 0x08, 0x64, 0x63};
const uint8_t font_data_ampersand[] = {0x36, 0x49, 0x56, 0x20, 0x50};
const uint8_t font_data_single_quote[] = {0x03};
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

constexpr Font make_font() {
    Font font = {};
    font['A'] = font_char_info{sizeof(font_data_A), font_data_A};
    font['B'] = font_char_info{sizeof(font_data_B), font_data_B};
    font['C'] = font_char_info{sizeof(font_data_C), font_data_C};
    font['D'] = font_char_info{sizeof(font_data_D), font_data_D};
    font['E'] = font_char_info{sizeof(font_data_E), font_data_E};
    font['F'] = font_char_info{sizeof(font_data_F), font_data_F};
    font['G'] = font_char_info{sizeof(font_data_G), font_data_G};
    font['H'] = font_char_info{sizeof(font_data_H), font_data_H};
    font['I'] = font_char_info{sizeof(font_data_I), font_data_I};
    font['J'] = font_char_info{sizeof(font_data_J), font_data_J};
    font['K'] = font_char_info{sizeof(font_data_K), font_data_K};
    font['L'] = font_char_info{sizeof(font_data_L), font_data_L};
    font['M'] = font_char_info{sizeof(font_data_M), font_data_M};
    font['N'] = font_char_info{sizeof(font_data_N), font_data_N};
    font['O'] = font_char_info{sizeof(font_data_O), font_data_O};
    font['P'] = font_char_info{sizeof(font_data_P), font_data_P};
    font['Q'] = font_char_info{sizeof(font_data_Q), font_data_Q};
    font['R'] = font_char_info{sizeof(font_data_R), font_data_R};
    font['S'] = font_char_info{sizeof(font_data_S), font_data_S};
    font['T'] = font_char_info{sizeof(font_data_T), font_data_T};
    font['U'] = font_char_info{sizeof(font_data_U), font_data_U};
    font['V'] = font_char_info{sizeof(font_data_V), font_data_V};
    font['W'] = font_char_info{sizeof(font_data_W), font_data_W};
    font['X'] = font_char_info{sizeof(font_data_X), font_data_X};
    font['Y'] = font_char_info{sizeof(font_data_Y), font_data_Y};
    font['Z'] = font_char_info{sizeof(font_data_Z), font_data_Z};

    font['a'] = font_char_info{sizeof(font_data_a), font_data_a};
    font['b'] = font_char_info{sizeof(font_data_b), font_data_b};
    font['c'] = font_char_info{sizeof(font_data_c), font_data_c};
    font['d'] = font_char_info{sizeof(font_data_d), font_data_d};
    font['e'] = font_char_info{sizeof(font_data_e), font_data_e};
    font['f'] = font_char_info{sizeof(font_data_f), font_data_f};
    font['g'] = font_char_info{sizeof(font_data_g), font_data_g};
    font['h'] = font_char_info{sizeof(font_data_h), font_data_h};
    font['i'] = font_char_info{sizeof(font_data_i), font_data_i};
    font['j'] = font_char_info{sizeof(font_data_j), font_data_j};
    font['k'] = font_char_info{sizeof(font_data_k), font_data_k};
    font['l'] = font_char_info{sizeof(font_data_l), font_data_l};
    font['m'] = font_char_info{sizeof(font_data_m), font_data_m};
    font['n'] = font_char_info{sizeof(font_data_n), font_data_n};
    font['o'] = font_char_info{sizeof(font_data_o), font_data_o};
    font['p'] = font_char_info{sizeof(font_data_p), font_data_p};
    font['q'] = font_char_info{sizeof(font_data_q), font_data_q};
    font['r'] = font_char_info{sizeof(font_data_r), font_data_r};
    font['s'] = font_char_info{sizeof(font_data_s), font_data_s};
    font['t'] = font_char_info{sizeof(font_data_t), font_data_t};
    font['u'] = font_char_info{sizeof(font_data_u), font_data_u};
    font['v'] = font_char_info{sizeof(font_data_v), font_data_v};
    font['w'] = font_char_info{sizeof(font_data_w), font_data_w};
    font['x'] = font_char_info{sizeof(font_data_x), font_data_x};
    font['y'] = font_char_info{sizeof(font_data_y), font_data_y};
    font['z'] = font_char_info{sizeof(font_data_z), font_data_z};

    font[' '] = font_char_info{sizeof(font_data_space), font_data_space};
    font['!'] = font_char_info{sizeof(font_data_bang), font_data_bang};
    font['"'] = font_char_info{sizeof(font_data_double_quote), font_data_double_quote};
    font['#'] = font_char_info{sizeof(font_data_hash), font_data_hash};
    font['$'] = font_char_info{sizeof(font_data_dollar), font_data_dollar};
    font['%'] = font_char_info{sizeof(font_data_percent), font_data_percent};
    font['&'] = font_char_info{sizeof(font_data_ampersand), font_data_ampersand};
    font['\''] = font_char_info{sizeof(font_data_single_quote), font_data_single_quote};
    font['('] = font_char_info{sizeof(font_data_open_paren), font_data_open_paren};
    font[')'] = font_char_info{sizeof(font_data_close_paren), font_data_close_paren};
    font['*'] = font_char_info{sizeof(font_data_star), font_data_star};
    font['+'] = font_char_info{sizeof(font_data_plus), font_data_plus};
    font[','] = font_char_info{sizeof(font_data_comma), font_data_comma};
    font['-'] = font_char_info{sizeof(font_data_minus), font_data_minus};
    font['.'] = font_char_info{sizeof(font_data_period), font_data_period};
    font['/'] = font_char_info{sizeof(font_data_slash), font_data_slash};

    font['0'] = font_char_info{sizeof(font_data_0), font_data_0};
    font['1'] = font_char_info{sizeof(font_data_1), font_data_1};
    font['2'] = font_char_info{sizeof(font_data_2), font_data_2};
    font['3'] = font_char_info{sizeof(font_data_3), font_data_3};
    font['4'] = font_char_info{sizeof(font_data_4), font_data_4};
    font['5'] = font_char_info{sizeof(font_data_5), font_data_5};
    font['6'] = font_char_info{sizeof(font_data_6), font_data_6};
    font['7'] = font_char_info{sizeof(font_data_7), font_data_7};
    font['8'] = font_char_info{sizeof(font_data_8), font_data_8};
    font['9'] = font_char_info{sizeof(font_data_9), font_data_9};
    return font;
}

Font font = make_font();
}

namespace mantyl {

SSD1306::SSD1306(I2cMaster &bus, uint8_t addr, gpio_num_t reset_pin)
    : SSD1306{I2cDevice{bus, addr}, reset_pin} {}
SSD1306::SSD1306(I2cDevice &&device, gpio_num_t reset_pin)
    : dev_{std::move(device)},
      reset_pin_{reset_pin},
      buffer_{new uint8_t[buffer_size()]} {
  memset(buffer_.get(), 0x00, buffer_size());

  size_t offset = 0;
  const char* str = "0123456789+-/*()";
  for (const char* p = str; *p != '\0'; ++p) {
    const char c = *p;
    memcpy(buffer_.get() + offset, font[c].data, font[c].width);
    offset += font[c].width + 1;
  }

  offset = 128;
  str = "VWXYZ";
  for (const char* p = str; *p != '\0'; ++p) {
    const char c = *p;
    memcpy(buffer_.get() + offset, font[c].data, font[c].width);
    offset += font[c].width + 1;
  }

  offset = 256;
  str = "abcdefghijklmnopqrstuvw";
  for (const char* p = str; *p != '\0'; ++p) {
    const char c = *p;
    memcpy(buffer_.get() + offset, font[c].data, font[c].width);
    offset += font[c].width + 1;
  }

  offset = 128 * 3;
  str = "xyz";
  for (const char* p = str; *p != '\0'; ++p) {
    const char c = *p;
    memcpy(buffer_.get() + offset, font[c].data, font[c].width);
    offset += font[c].width + 1;
  }
}

SSD1306::~SSD1306() {
  if (reset_pin_ >= 0) {
    gpio_reset_pin(reset_pin_);
  }
}

esp_err_t SSD1306::init() {
  // Settings for an Adafruit 128x32 display
  const uint8_t charge_pump = external_vcc_ ? 0x10_u8 : 0x14_u8;
  const uint8_t precharge = external_vcc_ ? 0x22_u8 : 0xf1_u8;

  esp_err_t rc;

  if (reset_pin_ >= 0) {
    gpio_config_t io_conf = {
        .pin_bit_mask = 1ULL << reset_pin_,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    rc = gpio_config(&io_conf);
    ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure SSD1306 reset pin");

    gpio_set_level(reset_pin_, 0);
    // Minimum reset low pulse width is 3us, according to the datasheet
    vTaskDelay(pdMS_TO_TICKS(1));
    gpio_set_level(reset_pin_, 1);
    vTaskDelay(pdMS_TO_TICKS(10));
  }

  rc = send_commands(Command::DisplayOff);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(0) error initializing SSD1306 %u", dev_.address());
  rc = send_commands(Command::SetDisplayClockDiv,
                     0x80_u8); // reset oscillator frequency and divide ratio
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(1) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetMultiplex, static_cast<uint8_t>(height_ - 1));
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(2) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetDisplayOffset,
                     0x0_u8,
                     static_cast<uint8_t>(Command::SetStartLine | 0x0));
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(3) error initializing SSD1306 %u", dev_.address());
  rc = send_commands(Command::ChargePump, charge_pump);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(4) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetMemoryMode,
                     0x00_u8, // horizontal addressing mode
                     static_cast<uint8_t>(Command::SegRemap | 0x1),
                     Command::ComScanDec);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(5) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetComPins,
                     com_pin_flags_,
                     Command::SetContrast,
                     contrast_,
                     Command::SetPrecharge,
                     precharge);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(6) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetVComDeselect,
                     0x40_u8,
                     Command::DisplayAllOn_RAM,
                     Command::NormalDisplay,
                     Command::DeactivateScroll,
                     Command::DisplayOn);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(7) error initializing SSD1306 %u", dev_.address());

  return ESP_OK;
}

esp_err_t SSD1306::flush() {
  uint8_t const page_end = (height_ + 7) / 8;
  uint8_t const col_end = width_ - 1;
  auto rc = send_commands(Command::SetPageAddr,
                     0_u8,     // start
                     page_end, // end
                     Command::SetColumnAddr,
                     0_u8,   // start
                     col_end // end
                     );
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "error setting mem address on SSD1306 %u", dev_.address());

  uint8_t cmd = 0x40;
  rc = dev_.bus().write2(dev_.address(),
                         &cmd,
                         sizeof(cmd),
                         buffer_.get(),
                         buffer_size(),
                         std::chrono::milliseconds(1000));
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "error writing draw buffer to SSD1306 %u", dev_.address());

  return ESP_OK;
}

esp_err_t SSD1306::send_commands(const uint8_t *data, size_t n) {
  const uint8_t cmd_start = 0;
  return dev_.bus().write2(dev_.address(),
                           &cmd_start,
                           sizeof(cmd_start),
                           data,
                           n,
                           std::chrono::milliseconds(1000));
}

} // namespace mantyl
