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

* Pull-up resistors (x2)

  I am currently using 4.7kOhm resistors.

  The maximum allowed resistance is determined by the bus capacitance.  Since
  we do have a relatively long connection for an I2C bus, going too high could
  be problematic.  I haven't had problems with 4.7kOhm so far.

  The minimum resistance is determined by the amount of current needed to pull
  the bus line low.  Our signal level is 3.3V; the bus must be pulled lower
  than (3.3V * 0.3) to be recognized as low, or lower than 0.99V.  Pulling the
  bus to .99V across a 4.7kOhm resistor requires 0.5mA.  Pulling it all the way
  to 0V requires 0.7mA.

  The ESP32S3 GPIO pins have a maximum low-level sink current of 28mA, which
  gives us plenty of room.  The SX1509 has a maximum low-level sink current of
  8mA at 3.3V.  The SSD1306 datasheet unfortunately does not clearly list the
  maximum allowed voltage.  (It documents the maximum logic current as 150uA,
  but this seems like it might be for the SPI logic mode.)

* Diodes

  I am using 1N4148 diodes.  1N5817 should also work.

* Key switches

  Any cherry-compatible key switches should work.

* Screws

  * 8 #6-32 1/2" screws for connecting the wrist rests
  * 3 #6-32 1/4" screws for the LED backplate
  * 2 #6-32 1/4" screws for the USB connector backplate
  * 8 #2 1/4" screws for the SX1509 boards
  * 1 #2 1/4" screw for the FeatherS3

* Cable: Wire and Paracord

  For making the cable that connects the two halves, I used some very thin wire
  (34AWG wire), and threaded it through #95 paracord.  #275 paracord is just
  slightly larger, and would also be a reasonable choice.

  Wire: https://www.adafruit.com/product/4734
