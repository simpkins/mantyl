#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

from .foot import add_feet
from .i2c_conn import add_i2c_connector
from .keyboard import Keyboard, gen_keyboard
from .key_socket_holder import socket_holder
from .screw_holes import add_screw_holes


def right_half() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_mesh()

    kbd_obj = gen_keyboard(kbd)
    add_feet(kbd, kbd_obj)
    add_i2c_connector(kbd, kbd_obj)
    add_screw_holes(kbd, kbd_obj)

    return kbd_obj


def right_socket_grid() -> bpy.types.Object:
    from . import blender_util

    kbd = Keyboard()
    kbd2 = Keyboard()
    kbd2.gen_main_grid()
    kbd2.gen_main_grid_edges()

    for col, row in kbd.key_indices():
        holder = socket_holder()
        with blender_util.TransformContext(holder) as ctx:
            if row != 0:
                ctx.rotate(180, "Z")
            ctx.translate(0, 0, -0.2)
            ctx.transform(kbd._keys[col][row].transform)

    mesh = blender_util.blender_mesh("keyboard_mesh", kbd.mesh)
    obj = blender_util.new_mesh_obj("keyboard", mesh)

    mesh2 = blender_util.blender_mesh("keyboard_mesh", kbd2.mesh)
    obj2 = blender_util.new_mesh_obj("keyboard2", mesh2)
