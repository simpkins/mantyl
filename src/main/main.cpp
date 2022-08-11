// Copyright (c) 2022, Adam Simpkins

#include "config.h"
#include "sdkconfig.h"

#include "I2cMaster.h"
#include "SSD1306.h"
#include "Keypad.h"

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
  static void left_gpio_intr_handler(void *arg);
  static void keyboard_task_fn(void *arg);

  void on_left_gpio_intr();
  void keyboard_task();

  I2cMaster i2c_{PinConfig::I2cSDA, PinConfig::I2cSCL};
  SSD1306 display_{i2c_, 0x3c, GPIO_NUM_38};
  Keypad left_{i2c_, 0x3e, GPIO_NUM_6, 7, 8};
  Keypad right_{i2c_, 0x3f, GPIO_NUM_NC, 6, 8};
  SemaphoreHandle_t done_sem_{};
  TaskHandle_t task_handle_{};
};

void App::left_gpio_intr_handler(void* arg) {
  auto *app = static_cast<App *>(arg);
  app->on_left_gpio_intr();
}

void App::on_left_gpio_intr() {
  BaseType_t high_task_wakeup = pdFALSE;
  xTaskNotifyFromISR(task_handle_, 0x01, eSetBits, &high_task_wakeup);

  if (high_task_wakeup == pdTRUE) {
    portYIELD_FROM_ISR();
  }
}

esp_err_t App::init() {
  done_sem_ = xSemaphoreCreateBinary();

  auto rc = i2c_.init(I2cClockSpeed);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to initialized I2C bus");

  rc = gpio_install_isr_service(0);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to install gpio ISR");

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

  rc = gpio_isr_handler_add(left_.interrupt_pin(), left_gpio_intr_handler, this);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to add left keypad ISR");

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

  ESP_LOGI(LogTag, "attempting display init:");
  rc = display_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized display");
  } else {
    ESP_LOGE(LogTag,
             "failed to initialize display matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }
  rc = display_.flush();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully wrote to display");
  } else {
    ESP_LOGE(LogTag,
             "failed to perform display write: %d: %s",
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

void App::keyboard_task() {
  while (true) {
    unsigned long notified_value = 0;
    // TODO: allow registering timeout events, and wait until the desired next
    // timeout.  This way we can have a short timeout when a key is pressed to
    // detect the release, and a long timeout when no keys are pressed.
    // We also want to support timeouts for display fade/animation/etc.
    const auto rc = xTaskNotifyWait(
        pdFALSE, ULONG_MAX, &notified_value, pdMS_TO_TICKS(50));
    if (rc == pdTRUE) {
      ESP_LOGD(LogTag, "got notification: %#04x", notified_value);
      left_.on_interrupt();
    } else {
      ESP_LOGD(LogTag, "no notification!");
      left_.on_timeout();
    }
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
  // init_usb();

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
