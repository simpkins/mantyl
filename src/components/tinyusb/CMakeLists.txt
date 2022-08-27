idf_build_get_property(target IDF_TARGET)

set(tusb_debug_level 0)
if(target STREQUAL "esp32s3")
  set(tusb_mcu "OPT_MCU_ESP32S3")
  set(tusb_family "esp32sx")
elseif(target STREQUAL "esp32s2")
  set(tusb_mcu "OPT_MCU_ESP32S2")
  set(tusb_family "esp32sx")
else()
  message(FATAL_ERROR "TinyUSB is not supported on ${target}.")
  return()
endif()

idf_component_get_property(freertos_component_dir freertos COMPONENT_DIR)

idf_component_register(
  SRCS
    "tinyusb/src/portable/espressif/${tusb_family}/dcd_${tusb_family}.c"
    "tinyusb/src/class/cdc/cdc_device.c"
    "tinyusb/src/class/hid/hid_device.c"
    "tinyusb/src/class/midi/midi_device.c"
    "tinyusb/src/class/msc/msc_device.c"
    "tinyusb/src/class/vendor/vendor_device.c"
    "tinyusb/src/common/tusb_fifo.c"
    "tinyusb/src/device/usbd_control.c"
    "tinyusb/src/device/usbd.c"
    "tinyusb/src/tusb.c"
  INCLUDE_DIRS
    "tinyusb/src/"
    "include"
    # The FreeRTOS API include convention in tinyusb is different from esp-idf
    "${freertos_component_dir}/FreeRTOS-Kernel/include/freertos"
  PRIV_INCLUDE_DIRS
    "tinyusb/hw/bsp/"
    "tinyusb/src/"
    "tinyusb/src/device"
  PRIV_REQUIRES "usb" "driver"
)

target_compile_definitions(
  ${COMPONENT_LIB} PUBLIC
    "CFG_TUSB_MCU=${tusb_mcu}"
    "CFG_TUSB_DEBUG=${tusb_debug_level}"
)
