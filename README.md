# Custom concave split keyboard

This is code for my custom keyboard.


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
