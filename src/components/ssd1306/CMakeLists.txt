set(component_srcs "src/SSD1306.cpp")

idf_component_register(SRCS "${component_srcs}"
                       INCLUDE_DIRS "include"
                       PRIV_INCLUDE_DIRS ""
                       PRIV_REQUIRES ""
                       REQUIRES "mantyl_util" "i2c_cpp")
