* [Adafruit HUZZAH32](https://www.adafruit.com/product/3405)
  This microcontroller is overkill for this project, but I had a couple lying
  around.

* [SX1509 I/O Expander Breakout](https://www.sparkfun.com/products/13601)
  Maybe in the future I'll print a PCB for this project where the SX1509
  can be incorporated directly on a board with the other components.  This
  breakout makes it very easy to use for now.

  [Arduino Library](https://github.com/sparkfun/SparkFun_SX1509_Arduino_Library)

* [128x32 I2C Monochrome OLED](https://www.adafruit.com/product/4440)

  [Arduino Library](https://github.com/adafruit/Adafruit_SSD1306)

* [TRRS Jack](https://www.sparkfun.com/products/12639)

  For running an I2C connection between the keyboard halves.

  I have considered using other connectors.  This
  [5-pin connector](https://www.adafruit.com/product/5317) is kind of cool,
  and would allow also using the INT pin from the SX1509.  It seems a bit
  expensive, though, and the cable connector is a little large.

* [USB Micro-B plug](https://www.adafruit.com/product/1829)
  For bringing the USB connection from the ESP32 out to the case.



# Volume control

I also wanted to include an audio volume control slider in the keyboard body.
* 3.5mm Audio Jack
  [Panel mount](https://www.adafruit.com/product/3692)
  [3.5mm Audio Jack](https://www.sparkfun.com/products/8032)
* Audio potentiometer: Alps Alpine: RSA0K12A1013 (100mm) or RS60N1219A04 (60mm)
