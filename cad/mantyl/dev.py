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
    from bpycad import blender_util

    show_halves = True
    show_numpad = True
    show_keycaps = False
    show_oled = False
    show_wrist_rests = False

    rkbd, lkbd, np = kbd_halves.gen_3_sections()

    if show_halves:
        keyboard.gen_keyboard(rkbd, "keyboard.R")
        keyboard.gen_keyboard(lkbd, "keyboard.L")
        #kbd_halves.right_full(rkbd)

    if show_numpad:
        np.gen_object()

    if show_wrist_rests:
        rwr = wrist_rest.right()
        with blender_util.TransformContext(rwr) as ctx:
            ctx.translate(kbd_halves.HALF_OFFSET, 0, 0)
        lwr = wrist_rest.left()
        with blender_util.TransformContext(lwr) as ctx:
            ctx.translate(-kbd_halves.HALF_OFFSET, 0, 0)

    if show_keycaps:
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


def test_np() -> None:
    rkbd, lkbd, np = kbd_halves.gen_3_sections()
    np.gen_object()

    from . import soc
    from bpycad import blender_util
    if False:
        esp32 = soc.esp32s3_wroom_devkit_c()
        with blender_util.TransformContext(esp32) as ctx:
            ctx.rotate(90, "Z")
            ctx.rotate(90, "X")
            ctx.translate(0, 60, 20)
    else:
        mesh = soc.numpad_pcb()
        mesh.translate(0, 0, -0.5)
        mesh.transform(np.plate_tf)
        bmesh = blender_util.blender_mesh(f"pcb_mesh", mesh)
        obj = blender_util.new_mesh_obj("numpad_pcb", bmesh)


def test() -> None:
    # test_full()
    test_np()

    # kbd_halves.right_full()
    # kbd_halves.right_shell()
    # kbd_halves.right_socket_underlay()
    # kbd_halves.right_thumb_underlay()

    # kbd_halves.left_full()
    # kbd_halves.left_shell()
    # kbd_halves.left_socket_underlay()
    # kbd_halves.left_thumb_underlay()
    # kbd_halves.left_oled_backplate()

    # keyboard.main_keys_test()

    # kbd_halves.right_shell_simple()
    # wrist_rest.test()

    # sx1509_holder.test_screw_holder()
    # oled_holder.test()
    # usb_cutout.test()
    # i2c_conn.cable_cap_test()
    #foot.test()

    bpy.ops.object.mode_set(mode="EDIT")
    # blender_util.set_shading_mode("WIREFRAME")
