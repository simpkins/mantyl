This directory contains the source code for the firmware.

In order to support multiple hardware variants, there are separate
subdirectories for each hardware configuration.  In order to build the code for
a specific variant, cd into that variant subdirectory and build with
`idf.py build`  (`idf.py` is part of the ESP-IDF.)

* v1: The initial hardware configuration.
  There are two separate halves, controlled by an FeatherS3 in the left half,
  an SSD1306 display in the left half, and two SX1509 chips for each keyboard
  half.
