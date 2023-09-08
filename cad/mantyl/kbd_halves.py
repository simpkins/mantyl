#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy
import copy
from dataclasses import dataclass
from typing import cast, List, Optional, Tuple

from bpycad import blender_util
from bpycad import cad
from .foot import add_feet
from .i2c_conn import add_i2c_connector
from .keyboard import Grid2D, Keyboard, KeyHole, gen_keyboard
from .key_socket_holder import SocketHolder, SocketHolderBuilder, SocketType
from .numpad import NumpadSection
from .screw_holes import gen_screw_hole
from . import cover
from . import oled_holder
from . import numpad
from . import sx1509_holder
from . import usb_cutout
from . import wrist_rest


# The distance between the closest point of the two keyboard halves,
# along the X axis at their closest point (at the tip of the thumb sections).
X_SEPARATION = 35


@dataclass
class GenSettings:
    show_numpad: bool = True
    show_right: bool = True
    show_left: bool = True
    simple_shells: bool = False
    show_wrist_rests: bool = True
    show_cover: bool = True
    show_keycaps: bool = False
    show_controller: bool = False
    show_underlay: bool = True


def generate_all(settings: GenSettings) -> None:
    rkbd = Keyboard()
    rkbd.gen_mesh()

    x_offset = get_x_offset(rkbd)

    right_tf = cad.Transform().translate(x_offset, 0.0, 0.0)
    left_tf = cad.Transform().mirror_x().translate(-x_offset, 0.0, 0.0)

    lkbd = copy.deepcopy(rkbd)
    rkbd.transform(right_tf)
    lkbd.transform(left_tf)

    np = numpad.NumpadSection(rkbd, lkbd)

    if settings.show_numpad:
        if settings.simple_shells:
            np.gen_object_simple()
        else:
            np.gen_object()

        if settings.show_controller:
            from . import soc

            pcb = soc.numpad_pcb()
            with blender_util.TransformContext(pcb) as ctx:
                ctx.rotate(180, "Y")
                ctx.translate(0, 0, -0.5)
                ctx.transform(np.plate_tf)

        if settings.show_keycaps:
            np.gen_keycaps()

    if settings.show_right:
        if settings.simple_shells:
            gen_keyboard(rkbd, name="keyboard.R")
        else:
            right_shell, right_cover_builder = right_shell_obj(rkbd)
            if settings.show_cover:
                right_cover = right_cover_builder.gen_cover("cover.R")
                right_cover.location = (
                    0,
                    0,
                    right_cover_builder.ground_clearance,
                )

        if settings.show_underlay:
            socket_underlay(rkbd, mirror=False, name="underlay.R")
            thumb_underlay(rkbd, mirror=False, name="thumb_underlay.R")

        if settings.show_wrist_rests:
            rwr = wrist_rest.right()
            with blender_util.TransformContext(rwr) as ctx:
                ctx.translate(x_offset, 0, 0)

        if settings.show_keycaps:
            rkbd.gen_keycaps()

    if settings.show_left:
        if settings.simple_shells:
            gen_keyboard(lkbd, name="keyboard.L")
        else:
            left_shell, left_cover_builder = right_shell_obj(
                rkbd, name="keyboard.L"
            )

            if settings.show_cover:
                left_cover = left_cover_builder.gen_cover("cover.L")
                with blender_util.TransformContext(left_cover) as ctx:
                    ctx.mirror_x()
                left_cover.location = (
                    0,
                    0,
                    left_cover_builder.ground_clearance,
                )

            with blender_util.TransformContext(left_shell) as ctx:
                ctx.mirror_x()

        if settings.show_underlay:
            socket_underlay(rkbd, mirror=True, name="underlay.L")
            thumb_underlay(rkbd, mirror=True, name="thumb_underlay.L")

        if settings.show_wrist_rests:
            rwr = wrist_rest.left()
            with blender_util.TransformContext(rwr) as ctx:
                ctx.translate(-x_offset, 0, 0)

        if settings.show_keycaps:
            lkbd.gen_keycaps()

    return


def get_x_offset(kbd: Keyboard) -> float:
    """
    Return the X offset that the keyboard needs to be adjusted for placing at
    the correct location for fully assembling the keyboard and numpad section
    together.

    The keyboard object was modeled with it at the origin, as was the numpad.
    To place them together, the (right) keyboard needs to be moved to the right
    kf the numpad.
    """
    # Find the leftmost portion of the keyboard.  We have to translate at least
    # this much along the X axis to have the two halves not overlap in the
    # middle.
    min_x_offset = kbd.thumb_tl.out2.x
    return -min_x_offset + (X_SEPARATION * 0.5)


def gen_3_sections() -> Tuple[Keyboard, Keyboard, NumpadSection]:
    """
    Generate and return right keyboard half, left keyboard half, and numpad
    section.
    """
    rkbd = Keyboard()
    rkbd.gen_mesh()

    x_offset = get_x_offset(rkbd)

    right_tf = cad.Transform().translate(x_offset, 0.0, 0.0)
    left_tf = cad.Transform().mirror_x().translate(-x_offset, 0.0, 0.0)

    lkbd = copy.deepcopy(rkbd)
    rkbd.transform(right_tf)
    lkbd.transform(left_tf)

    np = numpad.NumpadSection(rkbd, lkbd)

    return rkbd, lkbd, np


def right_shell_obj(
    kbd: Keyboard, name: str = "keyboard.R"
) -> Tuple[bpy.types.Object, cover.CoverBuilder]:
    kbd_obj = gen_keyboard(kbd, name=name)

    add_feet(kbd, kbd_obj)
    cover_builder = add_bottom_cover_parts(kbd, kbd_obj)
    add_wrist_rest_screw_holes(kbd, kbd_obj)

    holes = get_numpad_screw_holes(kbd)
    blender_util.difference(kbd_obj, holes)

    hole = get_rkbd_cable_hole(kbd)
    blender_util.difference(kbd_obj, hole)
    return kbd_obj, cover_builder


def add_bottom_cover_parts(
    kbd: Keyboard, kbd_obj: bpy.types.Object
) -> cover.CoverBuilder:
    cb = cover.CoverBuilder(kbd_obj)

    cb.add_stop(30, kbd.left_wall[-1].in3, kbd.left_wall[-5].in3, x=-5)
    cb.add_stop(50, kbd.right_wall[-1].in3, kbd.right_wall[0].in3)

    front_x_off = -2.75
    cb.add_clip(kbd.fr.in3, kbd.fl.in3, x=front_x_off)
    cb.add_stop(6, kbd.fr.in3, kbd.fl.in3, x=front_x_off - 14)
    cb.add_stop(6, kbd.fr.in3, kbd.fl.in3, x=front_x_off + 14)

    cb.add_clip(kbd.bl.in3, kbd.br.in3)
    cb.add_stop(10, kbd.bl.in3, kbd.br.in3, x=20)
    cb.add_stop(10, kbd.bl.in3, kbd.br.in3, x=-20)

    cb.add_clip(kbd.thumb_bl.in2, kbd.thumb_tl.in2)
    cb.add_stop(15, kbd.thumb_br.in2.point, kbd.thumb_bl.in2.point, -10)
    cb.add_stop(15, kbd.thumb_tl.in2.point, kbd.thumb_tr.in2.point, 5)

    return cb


def add_wrist_rest_screw_holes(
    kbd: Keyboard, kbd_obj: bpy.types.Object
) -> None:
    def add_screw_hole(x: float, z: float) -> None:
        screw_hole = gen_screw_hole(kbd.wall_thickness)
        blender_util.apply_to_wall(
            screw_hole, kbd.fl.out2, kbd.fr.out2, x=x, z=z
        )
        blender_util.difference(kbd_obj, screw_hole)

    x_spacing = 45
    x_offset = 0
    add_screw_hole(x=x_offset - (x_spacing * 0.5), z=8)
    add_screw_hole(x=x_offset + (x_spacing * 0.5), z=8)
    add_screw_hole(x=x_offset - (x_spacing * 0.5), z=22)
    add_screw_hole(x=x_offset + (x_spacing * 0.5), z=22)


def get_numpad_screw_holes(kbd: Keyboard) -> None:
    p0 = kbd.left_wall[-1].in3
    p1 = kbd.left_wall[-5].in3
    x_off = -5
    h1 = gen_screw_hole(kbd.wall_thickness * 3)
    blender_util.apply_to_wall(h1, p0, p1, x=x_off - 12.5, z=40)
    h2 = gen_screw_hole(kbd.wall_thickness * 3)
    blender_util.apply_to_wall(h2, p0, p1, x=x_off + 12.5, z=40)
    h3 = gen_screw_hole(kbd.wall_thickness * 3)
    blender_util.apply_to_wall(h3, p0, p1, x=x_off, z=20)

    h4 = gen_screw_hole(kbd.wall_thickness * 3)
    blender_util.apply_to_wall(
        h4, kbd.thumb_tl.in2.point, kbd.thumb_tr.in2.point, x=5, z=20
    )

    blender_util.union(h1, h2)
    blender_util.union(h1, h3)
    blender_util.union(h1, h4)

    return h1


def get_rkbd_cable_hole(kbd: Keyboard) -> bpy.types.Object:
    return get_cable_hole(
        kbd.left_wall[-6].in3, kbd.left_wall[-5].in3, x=2, z=45.0
    )


def get_cable_hole(
    p1: cad.Point, p2: cad.Point, x: float = 0.0, z: float = 0.0
) -> bpy.types.Object:
    """
    Add a hole to fit a ribbon cable between each keyboard half and the center
    numpad section.
    """
    width = 10
    height = 40

    r = width * 0.5
    thickness = Keyboard.wall_thickness * 5
    bottom = 20
    top = 40
    hole = blender_util.cylinder(r=r, h=thickness)
    hole2 = blender_util.cylinder(r=r, h=thickness)
    with blender_util.TransformContext(hole) as ctx:
        ctx.translate(0, height * 0.5 - r, 0)
    with blender_util.TransformContext(hole2) as ctx:
        ctx.translate(0, height * -0.5 + r, 0)
    hole3 = blender_util.cube(width, height - 2 * r, thickness)
    blender_util.union(hole, hole2)
    blender_util.union(hole, hole3)

    with blender_util.TransformContext(hole) as ctx:
        ctx.translate(0, 0, thickness * 0.5 - 4.0)
        ctx.rotate(90, "X")
        ctx.rotate(20, "Z")

    blender_util.apply_to_wall(hole, p1, p2, x, z)
    return hole


def left_shell_obj(
    kbd: Keyboard, name: str = "keyboard.L"
) -> bpy.types.Object:
    obj = right_shell_obj(kbd)
    with blender_util.TransformContext(obj) as ctx:
        ctx.mirror_x()
    return obj


def left_shell_obj_v1(
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
    add_wrist_rest_screw_holes(kbd, kbd_obj)

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


def socket_underlay(
    kbd: Keyboard, mirror: bool = False, name: str = "underlay"
) -> bpy.types.Object:
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

    obj = blender_util.new_mesh_obj(name, mesh)
    if mirror:
        with blender_util.TransformContext(obj) as ctx:
            ctx.mirror_x()
    return obj


def thumb_underlay(
    kbd: Keyboard, mirror: bool = False, name: str = "thumb_underlay"
) -> bpy.types.Object:
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

    obj = blender_util.new_mesh_obj(name, mesh)
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
