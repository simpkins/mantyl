#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy
from typing import cast, List, Optional, Tuple

from bpycad import blender_util
from bpycad import cad
from .foot import add_feet
from .i2c_conn import add_i2c_connector
from .keyboard import Grid2D, Keyboard, KeyHole, gen_keyboard
from .key_socket_holder import SocketHolder, SocketHolderBuilder, SocketType
from .numpad import NumpadSection
from .screw_holes import add_screw_holes
from . import oled_holder
from . import numpad
from . import sx1509_holder
from . import usb_cutout


def right_shell_simple(name: str = "right_keyboard") -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_mesh()
    return gen_keyboard(kbd, name=name)


def left_shell_simple(name: str = "left_keyboard") -> bpy.types.Object:
    kbd_obj = right_shell_simple(name=name)
    with blender_util.TransformContext(kbd_obj) as ctx:
        ctx.mirror_x()
    return kbd_obj


# The distance between the closest point of the two keyboard halves,
# along the X axis at their closest point (at the tip of the thumb sections).
X_SEPARATION = 35


def gen_3_sections() -> Tuple[Keyboard, Keyboard, NumpadSection]:
    """
    Generate and return right keyboard half, left keyboard half, and numpad
    section.
    """
    rkbd = Keyboard()
    rkbd.gen_mesh()

    # Find the leftmost portion of the keyboard.  We have to translate at least
    # this much along the X axis to have the two halves not overlap in the
    # middle.
    min_x_offset = rkbd.thumb_tl.out2.x
    x_offset = -min_x_offset + (X_SEPARATION * 0.5)

    right_tf = cad.Transform().translate(x_offset, 0.0, 0.0)
    left_tf = cad.Transform().mirror_x().translate(-x_offset, 0.0, 0.0)

    rkbd.transform(right_tf)

    lkbd = Keyboard()
    lkbd.gen_mesh()
    lkbd.transform(left_tf)

    np = numpad.NumpadSection(rkbd, lkbd)

    return rkbd, lkbd, np


def right_shell() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_mesh()
    return right_shell_obj(kbd)


def right_shell_obj(
    kbd: Keyboard, name: str = "keyboard.R"
) -> bpy.types.Object:
    kbd_obj = gen_keyboard(kbd, name=name)
    add_feet(kbd, kbd_obj)
    add_i2c_connector(kbd, kbd_obj)
    add_screw_holes(kbd, kbd_obj)

    sx1509_holder.apply_screw_holder(
        kbd_obj, kbd.left_wall[-5].in3, kbd.left_wall[-1].in3, x=5.0, z=20.0
    )
    return kbd_obj


def left_shell() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_mesh()
    return left_shell_obj(kbd)


def left_shell_obj(
    kbd: Keyboard, name: str = "keyboard.L"
) -> bpy.types.Object:
    kbd_obj = gen_keyboard(kbd, name=name)

    oled_holder.apply_oled_holder(
        kbd_obj,
        kbd.thumb_tl.out2.point,
        kbd.thumb_bl.out2.point,
        mirror_x=True,
    )
    usb_cutout.Cutout().apply(
        kbd_obj,
        kbd.br.out3.point,
        kbd.bl.out3.point,
        mirror_x=True,
        flip=True,
        x=-46,
        z=20,
    )
    sx1509_holder.apply_screw_holder(
        kbd_obj, kbd.left_wall[-5].in3, kbd.left_wall[-1].in3, x=5.0, z=20.0
    )
    add_feet(kbd, kbd_obj)
    add_i2c_connector(kbd, kbd_obj)
    add_screw_holes(kbd, kbd_obj)

    with blender_util.TransformContext(kbd_obj) as ctx:
        ctx.mirror_x()

    return kbd_obj


def left_oled_backplate(kbd: Optional[Keyboard] = None) -> bpy.types.Object:
    if kbd is None:
        kbd = Keyboard()
        kbd.gen_mesh()

    backplate = oled_holder.Backplate(left=True).gen_backplate()
    with blender_util.TransformContext(backplate) as ctx:
        ctx.mirror_x()
    blender_util.apply_to_wall(
        backplate,
        kbd.thumb_tl.out2.point,
        kbd.thumb_bl.out2.point,
        x=0.0,
        z=27.0,
    )
    with blender_util.TransformContext(backplate) as ctx:
        ctx.mirror_x()

    return backplate


def right_keyboard_grid() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_main_grid()
    kbd.gen_main_grid_edges()
    mesh = blender_util.blender_mesh("keyboard_mesh", kbd.mesh)
    return blender_util.new_mesh_obj("keyboard2", mesh)


def socket_underlay(kbd: Keyboard, mirror: bool = False) -> bpy.types.Object:
    builder = SocketHolderBuilder(mirror=mirror)
    top_builder = SocketHolderBuilder(SocketType.TOP, mirror=mirror)
    mesh = cad.Mesh()

    base_transform = cad.Transform().translate(0.0, 0.0, -0.5)

    holders: Grid2D[SocketHolder] = Grid2D(7, 6)

    # Add all of the socket holders
    for col, row, key in kbd.enumerate_keys():
        # Flip all socket holders, except for the top row where they would
        # otherwise hit the back walls
        tf = base_transform.transform(key.transform)
        if row == 0:
            h = top_builder.gen(mesh, tf)
        else:
            h = builder.gen(mesh, tf)
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
        for row in range(5):
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
    holders[2][5].close_bottom_face()
    holders[3][5].close_bottom_face()
    holders[4][5].close_bottom_face()
    holders[5][5].close_bottom_face()
    holders[6][5].close_bottom_face()

    # Right faces
    for row in range(6):
        holders[6][row].close_right_face()

    # Top faces
    holders[0][2].close_top_face()
    for col in range(1, 7):
        holders[col][0].close_top_face()

    obj = blender_util.new_mesh_obj("underlay", mesh)
    if mirror:
        with blender_util.TransformContext(obj) as ctx:
            ctx.mirror_x()
    return obj


def thumb_underlay(kbd: Keyboard, mirror: bool = False) -> bpy.types.Object:
    builder: SocketHolderBuilder = SocketHolderBuilder(mirror=mirror)
    mesh: cad.Mesh = cad.Mesh()

    base_transform: cad.Transform = cad.Transform().translate(0.0, 0.0, -0.5)

    def make_holder(builder: SocketHolderBuilder, k: KeyHole) -> SocketHolder:
        tf = base_transform.transform(k.transform)
        return builder.gen(mesh, tf)

    h00 = make_holder(builder, kbd.t00)
    h01 = make_holder(builder, kbd.t01)
    h02 = make_holder(builder, kbd.t02)

    h10 = make_holder(builder, kbd.t10)
    h11 = make_holder(builder, kbd.t11)
    h12 = make_holder(builder, kbd.t12)

    h20 = make_holder(builder, kbd.t20)
    h21 = make_holder(builder, kbd.t21)

    h00.close_left_face()
    h01.close_left_face()
    h02.close_left_face()

    h20.close_right_face()
    h21.close_right_face()

    h00.close_top_face()
    h10.close_top_face()

    h02.close_bottom_face()
    h12.close_bottom_face()
    h21.close_bottom_face()

    h00.join_bottom(h01)
    h01.join_bottom(h02)
    h10.join_bottom(h11)
    h11.join_bottom(h12)
    h20.join_bottom(h21)

    h00.join_right(h10)
    h01.join_right(h11)
    h02.join_right(h12)

    h11.join_right(h20)
    h12.join_right(h21)

    # Join the right of h10 to the top of h20
    mesh.add_quad(
        h10.right_points[0][0],
        h20.top_points[0][1],
        h20.top_points[1][1],
        h10.right_points[1][0],
    )
    mesh.add_quad(
        h10.right_points[0][1],
        h10.right_points[1][1],
        h20.top_points[1][0],
        h20.top_points[0][0],
    )
    mesh.add_quad(
        h10.right_points[0][0],
        h10.right_points[0][1],
        h20.top_points[0][0],
        h20.top_points[0][1],
    )
    mesh.add_quad(
        h10.right_points[1][1],
        h10.right_points[1][0],
        h20.top_points[1][1],
        h20.top_points[1][0],
    )

    obj = blender_util.new_mesh_obj("thumb_underlay", mesh)
    if mirror:
        with blender_util.TransformContext(obj) as ctx:
            ctx.mirror_x()
    return obj


def right_socket_underlay() -> bpy.types.Object:
    return socket_underlay(Keyboard(), mirror=False)


def right_thumb_underlay() -> bpy.types.Object:
    return thumb_underlay(Keyboard(), mirror=False)


def left_socket_underlay() -> bpy.types.Object:
    return socket_underlay(Keyboard(), mirror=True)


def left_thumb_underlay() -> bpy.types.Object:
    return thumb_underlay(Keyboard(), mirror=True)


def right_full(kbd: Optional[Keyboard] = None) -> List[bpy.types.Object]:
    if kbd is None:
        kbd = Keyboard()
        kbd.gen_mesh()

    return [
        right_shell_obj(kbd),
        socket_underlay(kbd, mirror=False),
        thumb_underlay(kbd, mirror=False),
    ]


def left_full(kbd: Optional[Keyboard] = None) -> List[bpy.types.Object]:
    if kbd is None:
        kbd = Keyboard()
        kbd.gen_mesh()

    return [
        left_shell_obj(kbd),
        left_oled_backplate(kbd),
        socket_underlay(kbd, mirror=True),
        thumb_underlay(kbd, mirror=True),
    ]
