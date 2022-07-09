#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

import bpy

from . import kbd_halves
from . import key_socket_holder
from . import oled_holder
from . import sx1509_holder
from . import usb_cutout
from . import wrist_rest


def test() -> None:
    # kbd_halves.right_shell()
    # kbd_halves.right_socket_underlay()
    # kbd_halves.right_thumb_underlay()

    kbd_halves.left_shell()
    # kbd_halves.left_socket_underlay()
    # kbd_halves.left_thumb_underlay()

    # sx1509_holder.test()
    # oled_holder.test()

    # wrist_rest.test()

    bpy.ops.object.mode_set(mode="EDIT")
    # blender_util.set_shading_mode("WIREFRAME")
