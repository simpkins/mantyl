#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

from .foot import add_feet
from .i2c_conn import add_i2c_connector
from .keyboard import Keyboard, gen_keyboard
from .key_socket_holder import SocketHolderBuilder
from .screw_holes import add_screw_holes


def right_half() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_mesh()

    kbd_obj = gen_keyboard(kbd)
    add_feet(kbd, kbd_obj)
    add_i2c_connector(kbd, kbd_obj)
    add_screw_holes(kbd, kbd_obj)

    return kbd_obj


def right_keyboard_grid() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_main_grid()
    kbd.gen_main_grid_edges()
    mesh = blender_util.blender_mesh("keyboard_mesh", kbd.mesh)
    return blender_util.new_mesh_obj("keyboard2", mesh)


def right_socket_grid() -> bpy.types.Object:
    from . import blender_util
    from . import cad

    builder = SocketHolderBuilder()
    top_builder = SocketHolderBuilder(top_only=True)
    mesh = cad.Mesh()

    kbd = Keyboard()
    base_transform = cad.Transform().translate(0.0, 0.0, -0.5)

    holders: List[List[Optional[KeyHole]]] = []
    for col in range(7):
        holders.append([None] * 6)

    # Add all of the socket holders
    for col, row in kbd.key_indices():
        # Flip all socket holders, except for the top row where they would
        # otherwise hit the back walls
        flip = row != 0

        tf = base_transform.transform(kbd._keys[col][row].transform)
        if not flip:
            h = top_builder.gen(mesh, tf)
        else:
            h = builder.gen(mesh, tf, flip=True)
        holders[col][row] = h

    # Connections between vertical keys on each column
    holders[0][2].join_bottom(holders[0][3])
    holders[0][3].join_bottom(holders[0][4])
    for row in range(4):
        holders[1][row].join_bottom(holders[1][row + 1])
    for col in range(2, 7):
        for row in range(5):
            holders[col][row].join_bottom(holders[col][row + 1])

    # Connections between horizontal keys on each row
    holders[0][2].join_right(holders[1][2])
    holders[0][3].join_right(holders[1][3])
    holders[0][4].join_right(holders[1][4])
    for col in range(1, 6):
        for row in range(1, 5):
            holders[col][row].join_right(holders[col + 1][row])
    for col in range(2, 6):
        holders[col][5].join_right(holders[col + 1][5])

    # Left faces
    holders[1][0].close_left_face()
    holders[1][1].close_left_face()
    holders[0][2].close_left_face()
    holders[0][3].close_left_face()
    holders[0][4].close_left_face()
    holders[2][5].close_left_face()

    # Bottom faces
    holders[0][4].close_bottom_face()
    holders[1][4].close_bottom_face()
    for col in range(2, 7):
        holders[col][5].close_bottom_face()

    # Right faces
    for row in range(6):
        holders[6][row].close_right_face()

    # Top faces
    holders[0][2].close_top_face()
    for col in range(1, 7):
        holders[col][0].close_top_face()

    return blender_util.new_mesh_obj("socket_holders", mesh)
