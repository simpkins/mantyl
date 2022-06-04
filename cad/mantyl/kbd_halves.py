#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

from mantyl.foot import add_feet
from mantyl.i2c_conn import add_i2c_connector
from mantyl.keyboard import Keyboard, gen_keyboard
from mantyl.screw_holes import add_screw_holes


def right_half() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_mesh()

    kbd_obj = gen_keyboard(kbd)
    add_feet(kbd, kbd_obj)
    add_i2c_connector(kbd, kbd_obj)
    add_screw_holes(kbd, kbd_obj)

    return kbd_obj
