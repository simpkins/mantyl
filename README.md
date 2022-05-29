# ![Ou Kanji](img/ou.png) Custom concave split keyboard

This repository contains code for my custom keyboard.

This includes both modeling code to generate the 3D model, as well as the
firmware.

# Keyboard Model

The keyboard model is generated programmatically, using a mix of Blender and
OpenSCAD.

I initially attempted to model the keyboard solely using OpenSCAD, but kept
running into bugs where OpenSCAD generates bad STL output.  It can't
seem to handle arbitrary hulls, and will sometimes generate reversed facets and
normals, resulting in output that cannot be processed for 3D printing.  I
therefore switched to using pure Python to generate the mesh, and using Blender
Python APIs to apply bevels.


# Dependencies

For the firmware:
* [Adafruit SSD1306](https://github.com/adafruit/Adafruit_SSD1306)

For generating the 3D models:
* [Python](https://www.python.org/)
* [Blender](https://www.blender.org/)
* [OpenSCAD](https://openscad.org/)

# Inspiration

I've used [Maltron](https://www.maltron.com/) keyboards for quite a long time.
My original Maltron keyboard was a PS/2 model, and back in 2013 I built my own
[keyboard controller](https://github.com/simpkins/avrpp) for it using a
[Teensy++ 2.0](https://www.pjrc.com/store/teensypp.html) microcontroller, in
order to convert it to a USB keyboard.

The layout for this keyboard is heavily influenced by the Maltron layout--I
wanted it to be fairly similar since I've used the Maltron layout for so long.

For the 3D modeling, the
[Dactyl-Manuform](https://github.com/abstracthat/dactyl-manuform) keyboard
inspired me to programmatically generate OpenSCAD.  I had initially manually
written an OpenSCAD model for the main keyboard section, but manually writing
OpenSCAD was fairly inflexible, and became especially troublesome once I
started running into issues where OpenSCAD generated STL errors for some hulls.
Switching to programmatically generating the OpenSCAD made the process much
easier.

For some choices of the electronic components I also reused some of the same
choices from my co-worker Wez's [Halfdeck](https://github.com/wez/halfdeck)
keyboard.
