#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

import bpy

from . import i2c_conn
from . import foot
from . import kbd_halves
from . import kbd_middle
from . import keyboard
from . import numpad
from . import oled_holder
from . import sx1509_holder
from . import usb_cutout
from . import wrist_rest


def test_numpad() -> None:
    from bcad import blender_util

    half_offset = 140

    right = kbd_halves.right_shell_simple()
    with blender_util.TransformContext(right) as ctx:
        ctx.translate(half_offset, 0.0, 0.0)

    left = kbd_halves.left_shell_simple()
    with blender_util.TransformContext(left) as ctx:
        ctx.translate(-half_offset, 0.0, 0.0)

    np = numpad.test()
    with blender_util.TransformContext(np) as ctx:
        ctx.rotate(12.0, "X")
        ctx.translate(-9.5, 15.0, 70.0)


def test() -> None:
    #kbd_middle.middle()

    test_numpad()
    #numpad.test()

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
    #foot.test()

    bpy.ops.object.mode_set(mode="EDIT")
    # blender_util.set_shading_mode("WIREFRAME")
