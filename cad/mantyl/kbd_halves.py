#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

from .foot import add_feet
from .i2c_conn import add_i2c_connector
from .keyboard import Keyboard, gen_keyboard
from .key_socket_holder import socket_holder, SocketParams
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
    from . import cad

    z_offset = -0.2
    collection = bpy.data.collections[0]

    kbd = Keyboard()
    holder = socket_holder()

    def add_holder(col: int, row: int) -> byp.types.Object:
        h = bpy.data.objects.new("socket_holder", holder.data.copy())
        collection.objects.link(h)
        with blender_util.TransformContext(h) as ctx:
            if row != 0:
                ctx.rotate(180, "Z")
            ctx.translate(0, 0, z_offset)
            ctx.transform(kbd._keys[col][row].transform)

        return h

    full_size = 17.4
    z_top = z_offset
    z_bottom = z_offset - SocketParams().thickness

    def join_vertical(k1: KeyHole, k2: KeyHole) -> None:
        x_left = -5
        x_right = 2.5
        y_top = full_size * 0.499
        y_bottom = -full_size * 0.499

        ttl = k1.add_point(x_left, y_bottom, z_top)
        ttr = k1.add_point(x_right, y_bottom, z_top)
        tbl = k2.add_point(x_left, y_top, z_top)
        tbr = k2.add_point(x_right, y_top, z_top)
        btl = k1.add_point(x_left, y_bottom, z_bottom)
        btr = k1.add_point(x_right, y_bottom, z_bottom)
        bbl = k2.add_point(x_left, y_top, z_bottom)
        bbr = k2.add_point(x_right, y_top, z_bottom)

        kbd.mesh.add_quad(ttl, ttr, tbr, tbl)
        kbd.mesh.add_quad(bbl, bbr, btr, btl)
        kbd.mesh.add_quad(tbl, tbr, bbr, bbl)
        kbd.mesh.add_quad(ttl, tbl, bbl, btl)
        kbd.mesh.add_quad(ttr, ttl, btl, btr)
        kbd.mesh.add_quad(tbr, ttr, btr, bbr)

    def join_horizontal(k1: KeyHole, k2: KeyHole) -> None:
        x_left = -full_size * 0.499
        x_right = full_size * 0.499
        y_top = 1
        y_bottom = -5

        ttl = k1.add_point(x_right, y_top, z_top)
        ttr = k2.add_point(x_left, y_top, z_top)
        tbl = k1.add_point(x_right, y_bottom, z_top)
        tbr = k2.add_point(x_left, y_bottom, z_top)
        btl = k1.add_point(x_right, y_top, z_bottom)
        btr = k2.add_point(x_left, y_top, z_bottom)
        bbl = k1.add_point(x_right, y_bottom, z_bottom)
        bbr = k2.add_point(x_left, y_bottom, z_bottom)

        kbd.mesh.add_quad(ttl, ttr, tbr, tbl)
        kbd.mesh.add_quad(bbl, bbr, btr, btl)
        kbd.mesh.add_quad(tbl, tbr, bbr, bbl)
        kbd.mesh.add_quad(ttl, tbl, bbl, btl)
        kbd.mesh.add_quad(ttr, ttl, btl, btr)
        kbd.mesh.add_quad(tbr, ttr, btr, bbr)

    # Connections between vertical keys on each column
    join_vertical(kbd.k02, kbd.k03)
    join_vertical(kbd.k03, kbd.k04)
    for row in range(4):
        join_vertical(kbd._keys[1][row], kbd._keys[1][row + 1])
    for col in range(2, 7):
        for row in range(5):
            join_vertical(kbd._keys[col][row], kbd._keys[col][row + 1])

    # Connections between horizontal keys on each row
    join_horizontal(kbd.k02, kbd.k12)
    join_horizontal(kbd.k03, kbd.k13)
    join_horizontal(kbd.k04, kbd.k14)
    for col in range(1, 6):
        for row in range(5):
            join_horizontal(kbd._keys[col][row], kbd._keys[col + 1][row])
    for col in range(2, 6):
        join_horizontal(kbd._keys[col][5], kbd._keys[col + 1][5])

    mesh = blender_util.blender_mesh("keyboard_mesh", kbd.mesh)
    obj = blender_util.new_mesh_obj("keyboard", mesh)

    # Add all of the socket holders
    for col, row in kbd.key_indices():
        h = add_holder(col, row)
        blender_util.union(obj, h)

    # Delete the original socket holder reference object
    bpy.data.objects.remove(holder)

    return obj

    kbd2 = Keyboard()
    kbd2.gen_main_grid()
    kbd2.gen_main_grid_edges()
    mesh2 = blender_util.blender_mesh("keyboard_mesh", kbd2.mesh)
    obj2 = blender_util.new_mesh_obj("keyboard2", mesh2)
