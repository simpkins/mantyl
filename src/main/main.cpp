// Copyright (c) 2022, Adam Simpkins

#include "config.h"
#include "sdkconfig.h"

#include "I2cMaster.h"
#include "Keypad.h"
#include "SSD1306.h"
#include "UI.h"

#include <chrono>

#include <driver/i2c.h>
#include <esp_check.h>
#include <esp_chip_info.h>
#include <esp_flash.h>
#include <esp_log.h>
#include <esp_mac.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <stdio.h>
#include <tinyusb.h>

using namespace std::chrono_literals;

namespace {
const char *LogTag = "mantyl.main";
}

namespace mantyl {

void print_info() {
  /* Print chip information */
  esp_chip_info_t chip_info;
  uint32_t flash_size;
  esp_chip_info(&chip_info);
  ESP_LOGD(LogTag, "This is %s chip with %d CPU core(s), WiFi%s%s, ",
           CONFIG_IDF_TARGET, chip_info.cores,
           (chip_info.features & CHIP_FEATURE_BT) ? "/BT" : "",
           (chip_info.features & CHIP_FEATURE_BLE) ? "/BLE" : "");

  ESP_LOGD(LogTag, "silicon revision %d, ", chip_info.revision);
  if (esp_flash_get_size(NULL, &flash_size) != ESP_OK) {
    ESP_LOGD(LogTag, "Get flash size failed");
    return;
  }

  ESP_LOGD(LogTag, "%uMB %s flash\n", flash_size / (1024 * 1024),
           (chip_info.features & CHIP_FEATURE_EMB_FLASH) ? "embedded"
                                                         : "external");

  ESP_LOGD(LogTag, "Minimum free heap size: %d bytes\n",
           esp_get_minimum_free_heap_size());
}

class App {
public:
  esp_err_t init();
  esp_err_t test();
  esp_err_t init_usb();

  void main();

private:
  enum NotifyBits : unsigned long {
    Left = 0x01,
    Right = 0x02,
  };

  static void left_gpio_intr_handler(void *arg);
  static void right_gpio_intr_handler(void *arg);
  static void keyboard_task_fn(void *arg);

  void keyboard_task();
  std::chrono::steady_clock::time_point
  keyboard_tick(std::chrono::steady_clock::time_point now);
  void on_gpio_interrupt(NotifyBits bits);

  I2cMaster i2c_left_{PinConfig::LeftI2cSDA, PinConfig::LeftI2cSCL, 0};
  I2cMaster i2c_right_{PinConfig::RightI2cSDA, PinConfig::RightI2cSCL, 1};
  SSD1306 display_{i2c_left_, 0x3c, GPIO_NUM_1};
  UI ui_{&display_};
  Keypad left_{"left", i2c_left_, 0x3e, GPIO_NUM_33, 7, 8};
  Keypad right_{"right", i2c_right_, 0x3f, GPIO_NUM_11, 6, 8};
  SemaphoreHandle_t done_sem_{};
  TaskHandle_t task_handle_{};
};

void App::left_gpio_intr_handler(void* arg) {
  auto *app = static_cast<App *>(arg);
  app->on_gpio_interrupt(NotifyBits::Left);
}

void App::right_gpio_intr_handler(void* arg) {
  auto *app = static_cast<App *>(arg);
  app->on_gpio_interrupt(NotifyBits::Right);
}

void App::on_gpio_interrupt(NotifyBits bits) {
  BaseType_t high_task_wakeup = pdFALSE;
  xTaskNotifyFromISR(task_handle_, bits, eSetBits, &high_task_wakeup);

  if (high_task_wakeup == pdTRUE) {
    portYIELD_FROM_ISR();
  }
}

esp_err_t App::init() {
  done_sem_ = xSemaphoreCreateBinary();

  auto rc = i2c_left_.init(I2cClockSpeed);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to initialize left I2C bus");

  rc = i2c_right_.init(I2cClockSpeed);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to initialize right I2C bus");

  rc = gpio_install_isr_service(0);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to install gpio ISR");

  ESP_LOGI(LogTag, "attempting display init:");
  rc = ui_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized display");
  } else {
    ESP_LOGE(LogTag,
             "failed to initialize display matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  ESP_LOGV(LogTag, "attempting left SX1509 init:");
  rc = left_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized left key matrix");
  } else {
    ESP_LOGE(LogTag,
             "failed to initialize left key matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  ESP_LOGV(LogTag, "attempting right SX1509 init:");
  rc = right_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized right key matrix");
  } else {
    // Maybe the right key matrix is not connected.
    ESP_LOGE(LogTag,
             "failed to initialize right key matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  return ESP_OK;
}

static std::array<char, 14> serial_str = {};

static char hexlify(uint8_t n) {
  if (n < 10) {
    return '0' + n;
  }
  return 'a' + (n - 10);
}

esp_err_t init_serial_str() {
  std::array<uint8_t, 6> mac_bytes;
  auto rc = esp_read_mac(mac_bytes.data(), ESP_MAC_WIFI_STA);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to get MAC");

  size_t out_idx = 0;
  for (size_t n = 0; n < mac_bytes.size(); ++n) {
    serial_str[out_idx] = hexlify((mac_bytes[n] >> 4) & 0xf);
    serial_str[out_idx + 1] = hexlify(mac_bytes[n] & 0xf);
    out_idx += 2;
    if (n == 2) {
      serial_str[out_idx] = '-';
      ++out_idx;
    }
  }
  serial_str[out_idx] = '\0';
  assert(out_idx + 1 == serial_str.size());

  return ESP_OK;
}

esp_err_t App::init_usb() {
  ESP_LOGI(LogTag, "USB initialization");

  tusb_desc_device_t usb_descriptor = {
      .bLength = sizeof(usb_descriptor),
      .bDescriptorType = TUSB_DESC_DEVICE,
      .bcdUSB = 0x0200, // USB version. 0x0200 means version 2.0
      .bDeviceClass = TUSB_CLASS_HID,
      .bDeviceSubClass = 1, // Boot
      .bDeviceProtocol = 1, // Keyboard
      .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,

      .idVendor = 0x303A, // Espressif's Vendor ID
      .idProduct = 0x9999,
      .bcdDevice = 0x0001, // Device FW version

      // String descriptor indices
      .iManufacturer = 0x01,
      .iProduct = 0x02,
      .iSerialNumber = 0x03,

      .bNumConfigurations = 0x01};

  tusb_desc_strarray_device_t descriptor_strings = {
      "\x09\x04",        // 0: is supported language is English (0x0409)
      "Adam Simpkins",   // 1: Manufacturer
      "Mantyl Keyboard", // 2: Product
      serial_str.data(),    // 3: Serial
  };

  tinyusb_config_t tusb_cfg = {
      .descriptor = &usb_descriptor,
      .string_descriptor = descriptor_strings,
      .external_phy = false,
      .configuration_descriptor = nullptr,
  };

  ESP_ERROR_CHECK(tinyusb_driver_install(&tusb_cfg));
  ESP_LOGI(LogTag, "USB initialization DONE");

  return ESP_OK;
}

std::chrono::steady_clock::time_point
App::keyboard_tick(std::chrono::steady_clock::time_point now) {
  const auto left_timeout = left_.tick(now);
  const auto right_timeout = right_.tick(now);
  const auto ui_timeout = ui_.tick(now);
  const auto next_timeout =
      now + std::min(std::min(left_timeout, right_timeout), ui_timeout);
  ESP_LOGD(LogTag,
           "tick: left=%ld (%d) right=%ld (%d)",
           static_cast<long int>(left_timeout.count()),
           (int)left_.num_pressed(),
           static_cast<long int>(right_timeout.count()),
           (int)right_.num_pressed());
  return next_timeout;
}

void App::keyboard_task() {
  ESP_ERROR_CHECK(gpio_isr_handler_add(
      left_.interrupt_pin(), left_gpio_intr_handler, this));
  ESP_ERROR_CHECK(gpio_isr_handler_add(
      right_.interrupt_pin(), right_gpio_intr_handler, this));

  auto now = std::chrono::steady_clock::now();
  auto next_timeout = keyboard_tick(now);

  while (true) {
    // TODO: we tend to wake up slightly before the timeout, which causes us to
    // go back to sleep then wake up quickly again a couple times before we
    // really hit the desired timeout.
    const auto max_delay = next_timeout - now;
    const auto max_delay_ticks = (max_delay.count() * configTICK_RATE_HZ *
                                  decltype(max_delay)::period::num) /
                                 decltype(max_delay)::period::den;
    unsigned long notified_value = 0;
    const auto rc =
        xTaskNotifyWait(pdFALSE, ULONG_MAX, &notified_value, max_delay_ticks);
    if (rc == pdTRUE) {
      ESP_LOGD(LogTag, "received notification: %#04x", notified_value);
    }

    now = std::chrono::steady_clock::now();
    next_timeout = keyboard_tick(now);
  }
  xSemaphoreGive(done_sem_);
}

void App::keyboard_task_fn(void* arg) {
  auto *app = static_cast<App *>(arg);
  printf("keyboard_task start; app=%p\n", app);
  app->keyboard_task();
  printf("keyboard_task suspending\n");
  vTaskSuspend(nullptr);
}

void App::main() {
  printf("main task prepare; app=%p\n", this);
  ESP_ERROR_CHECK(init());

  bool debug_mode = true; // TODO: read setting from flash
  bool boot_into_debug_mode = false;
  if (debug_mode) {
    vTaskDelay(pdMS_TO_TICKS(10));
    if (left_.is_interrupt_asserted()) {
      ESP_LOGI(LogTag, "key held down during init");
      boot_into_debug_mode = true;
    }
  }

#if 0
  if (!boot_into_debug_mode) {
    init_usb();
  }
#endif

  static constexpr configSTACK_DEPTH_TYPE keyboard_task_stack_size = 4096;
  const auto rc = xTaskCreatePinnedToCore(keyboard_task_fn,
                                          "keyboard",
                                          keyboard_task_stack_size,
                                          this,
                                          2,
                                          &task_handle_,
                                          0);
  if (rc != pdPASS) {
    ESP_LOGE(LogTag, "failed to create keyboard task");
    return;
  }

  // Wait for the keyboard task to finish.
  // (This should normally never happen.)
  printf("main task run\n");
  while (true) {
    if (xSemaphoreTake(done_sem_, portMAX_DELAY) == pdTRUE) {
      break;
    }
  }
}

} // namespace mantyl

extern "C" void app_main() {
  esp_log_level_set("mantyl.main", ESP_LOG_DEBUG);

  mantyl::print_info();

  mantyl::App app;
  app.main();
  ESP_LOGW(LogTag, "main task exiting");
}
