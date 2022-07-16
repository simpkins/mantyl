* [FeatherS3](https://esp32s3.com/feathers3.html)

  The ESP32 supports USB, Wifi, and BLE.  This board is pretty beefy for a
  microcontroller--dual core processor, 8MB PSRAM, and 16MB flash.  It's
  overkill for this project, but still relatively inexpensive.

* [SX1509 I/O Expander Breakout](https://www.sparkfun.com/products/13601)
  Maybe in the future I'll print a PCB for this project where the SX1509
  can be incorporated directly on a board with the other components.  This
  breakout makes it very easy to use for now.

  [Arduino Library](https://github.com/sparkfun/SparkFun_SX1509_Arduino_Library)

* [128x32 I2C Monochrome OLED](https://www.adafruit.com/product/4440)

  [Arduino Library](https://github.com/adafruit/Adafruit_SSD1306)

* [5-pin magnetic connector](https://www.adafruit.com/product/5413)

  I used this connector for the cable between the two halves.  Having 5 pins
  allows me to also connect the SX1509 interrupt pin, in addition to I2C.

  Using a [TRRS Jack](https://www.sparkfun.com/products/12639) would also have
  been an option, and would allow using off-the-shelf audio cables, but would
  not allow connecting the interrupt pin.

  This [5-pin connector](https://www.adafruit.com/product/5317) is another
  option, but is a bit on the large and expensive side.

* [USB C right angle connector](https://www.amazon.com/AGVEE-Degree-Angled-Adapter-Converter/dp/B09FJTTZWY)

  I used this to expose the external USB-C socket.  This is a cheap connector I
  found on Amazon, and I have no idea if it will continue to be available in
  the future.  This connector is a perfect size for directly plugging it in to
  the FeatherS3 and exposing the port through the shell wall.

  I also considered using USB-C keystone jacks, but these would take up more
  space, and would require running a cable on the inside of the keyboard from
  the keystone jack to the FeatherS3.  Even a 6-inch cable is too long for
  this, and there are relatively few cables available that are shorter.

  Another option would be just using a plain
  [USB-C socket](https://www.adafruit.com/product/4396), and soldering half of
  a cable to it.  This would just require a little CAD rework to come up with a
  solution for securely fastening it to the keyboard shell.



# Volume control

I also wanted to include an audio volume control slider in the keyboard body.
* 3.5mm Audio Jack
  [Panel mount](https://www.adafruit.com/product/3692)
  [3.5mm Audio Jack](https://www.sparkfun.com/products/8032)
* Audio potentiometer: Alps Alpine: RSA0K12A1013 (100mm) or RS60N1219A04 (60mm)
