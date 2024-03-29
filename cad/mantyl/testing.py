#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

import bpy

from . import i2c_conn
from . import foot
from . import kbd_halves
from . import keyboard
from . import key_socket_holder
from . import oled_holder
from . import sx1509_holder
from . import usb_cutout
from . import wrist_rest


def test() -> None:
    # kbd_halves.right_full()
    # kbd_halves.right_shell()
    # kbd_halves.right_socket_underlay()
    # kbd_halves.right_thumb_underlay()

    # kbd_halves.left_full()
    # kbd_halves.left_shell()
    # kbd_halves.left_socket_underlay()
    # kbd_halves.left_thumb_underlay()
    # kbd_halves.left_oled_backplate()

    # keyboard.test()

    # wrist_rest.test()
    # sx1509_holder.test_screw_holder()
    # oled_holder.test()
    # usb_cutout.test()
    # i2c_conn.cable_cap_test()
    foot.test()

    bpy.ops.object.mode_set(mode="EDIT")
    # blender_util.set_shading_mode("WIREFRAME")
