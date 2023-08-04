#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

import bpy

from . import i2c_conn
from . import foot
from . import kbd_halves
from . import keyboard
from . import numpad
from . import oled_holder
from . import sx1509_holder
from . import usb_cutout
from . import wrist_rest


def test_full() -> None:
    from bcad import blender_util

    half_offset = 140

    show_halves = True
    if show_halves:
        from . import kbd_halves

        right = kbd_halves.right_shell_simple()
        with blender_util.TransformContext(right) as ctx:
            ctx.translate(half_offset, 0.0, 0.0)

        left = kbd_halves.left_shell_simple()
        with blender_util.TransformContext(left) as ctx:
            ctx.translate(-half_offset, 0.0, 0.0)

    show_numpad = True
    if show_numpad:
        obj = numpad.gen_numpad(half_offset)

    show_oled = False
    if show_oled:
        # Possible display panel:
        # https://www.dfrobot.com/product-2019.html
        oled = blender_util.range_cube((-20.5, 20.5), (-6, 6), (-2.0, 2.0))
        with blender_util.TransformContext(oled) as ctx:
            ctx.rotate(-3.0, "X")
            ctx.translate(0, -41.0, 62.5)


def test() -> None:
    test_full()

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
