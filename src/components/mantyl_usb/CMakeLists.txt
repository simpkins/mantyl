set(component_srcs
    "Esp32UsbDevice.cpp"
    "StaticDescriptorMap.cpp"
    "UsbDescriptorMap.cpp"
    "UsbDevice.cpp"
)

idf_component_register(SRCS "${component_srcs}"
                       INCLUDE_DIRS "include"
                       PRIV_INCLUDE_DIRS ""
                       PRIV_REQUIRES ""
                       REQUIRES "usb" "soc")
