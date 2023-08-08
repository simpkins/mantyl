if(CONFIG_USB_OTG_SUPPORTED)
    set(component_srcs
        "CtrlOutTransfer.cpp"
        "CtrlInTransfer.cpp"
        "Esp32UsbDevice.cpp"
        "StaticDescriptorMap.cpp"
        "UsbDescriptorMap.cpp"
        "UsbDevice.cpp"
    )
endif()

idf_component_register(SRCS "${component_srcs}"
                       INCLUDE_DIRS "include"
                       PRIV_INCLUDE_DIRS ""
                       PRIV_REQUIRES ""
                       REQUIRES "usb" "soc")
