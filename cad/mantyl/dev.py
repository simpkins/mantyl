#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from . import cover
from . import i2c_conn
from . import foot
from . import kbd_halves
from . import keyboard
from . import numpad
from . import oled_holder
from . import sx1509_holder
from . import usb_cutout
from . import wrist_rest

from bpycad import blender_util

import bpy


def test_full() -> None:
    show_halves = True
    show_numpad = True
    show_keycaps = False
    show_oled = False
    show_wrist_rests = True

    rkbd, lkbd, np = kbd_halves.gen_3_sections()

    if show_halves:
        keyboard.gen_keyboard(rkbd, "keyboard.R")
        keyboard.gen_keyboard(lkbd, "keyboard.L")
        #kbd_halves.right_full(rkbd)

    if show_numpad:
        np.gen_object_simple()

    if show_wrist_rests:
        rwr = wrist_rest.right()
        orig_kbd = keyboard.Keyboard()
        orig_kbd.gen_mesh()
        x_offset = kbd_halves.get_x_offset(orig_kbd)
        with blender_util.TransformContext(rwr) as ctx:
            ctx.translate(x_offset, 0, 0)
        lwr = wrist_rest.left()
        with blender_util.TransformContext(lwr) as ctx:
            ctx.translate(-x_offset, 0, 0)

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
    return

    from . import soc

    mesh = soc.numpad_pcb()
    mesh.translate(0, 0, -0.5)
    mesh.transform(np.plate_tf)
    bmesh = blender_util.blender_mesh(f"pcb_mesh", mesh)
    obj = blender_util.new_mesh_obj("numpad_pcb", bmesh)


def test() -> None:
    test_full()
    # test_np()
    # cover.cover_clip()

    # kbd_halves.right_full()
    # kbd_halves.right_shell()
    # kbd_halves.right_socket_underlay()
    # kbd_halves.right_thumb_underlay()

    # kbd_halves.left_full()
    # kbd_halves.left_shell()
    # kbd_halves.left_socket_underlay()
    # kbd_halves.left_thumb_underlay()
    # kbd_halves.left_oled_backplate()

    bpy.ops.object.mode_set(mode="EDIT")
    #blender_util.set_shading_mode("WIREFRAME")
