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

    show_halves = True
    show_numpad = True
    show_keys = False
    show_oled = False

    rkbd, lkbd, np = kbd_halves.gen_3_sections()

    if show_halves:
        keyboard.gen_keyboard(rkbd, "keyboard.R")
        keyboard.gen_keyboard(lkbd, "keyboard.L")

    if show_numpad:
        mesh = blender_util.blender_mesh("numpad_mesh", np.mesh)
        np_obj = blender_util.new_mesh_obj("numpad", mesh)
        np.apply_bevels(np_obj)

    if show_keys:
        rkbd.gen_keycaps()
        lkbd.gen_keycaps()
        np.gen_keycaps()

    if show_oled:
        # Possible display panel:
        # https://www.dfrobot.com/product-2019.html
        oled = blender_util.range_cube((-20.5, 20.5), (-6, 6), (-2.0, 2.0))
        with blender_util.TransformContext(oled) as ctx:
            ctx.rotate(-1.0, "X")
            ctx.translate(0, -41.5, 62.1)


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
