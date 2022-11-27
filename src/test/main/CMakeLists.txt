idf_component_register(
  SRCS
    "main.cpp"
    "MockUsbDevice.cpp"
  INCLUDE_DIRS "${CMAKE_CURRENT_SOURCE_DIR}"
  REQUIRES
    "mantyl_util" "mantyl_usb" "mantyl"
    "spi_flash" "log" "usb"
)
