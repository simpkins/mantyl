# C++17 Support

This code uses C++17 features, and Arduino currently does not build with C++17
by default.  Support for C++17 has to be enabled by manually editing the
platform.txt file in the hardware package
(e.g., `$HOME/.arduino15/packages/esp32/hardware/esp32/$VERSION/platform.txt`).
Replace all instances of `-std=gnu++11` with `-std=gnu++17`.
