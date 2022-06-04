#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

"""A script to generate the keyboard mesh in Blender.
To use, run "blender -P blender.py"
"""

from __future__ import annotations

import bpy
import bmesh
import mathutils

import math
import os
import sys
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(__file__))

import mantyl.cad as cad
from mantyl.keyboard import Keyboard
from mantyl.blender_util import (
    blender_mesh,
    delete_all,
    difference,
    new_mesh_obj,
    union,
)


def gen_keyboard(kbd: Keyboard) -> bpy.types.Object:
    mesh = blender_mesh("keyboard_mesh", kbd.mesh)
    obj = new_mesh_obj("keyboard", mesh)

    # Deselect all vertices in the mesh
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")

    # Set bevel weights on the edges
    edge_weights = kbd.get_bevel_weights(mesh.edges)
    mesh.use_customdata_edge_bevel = True
    for edge_idx, weight in edge_weights.items():
        e = mesh.edges[edge_idx]
        e.bevel_weight = weight

    # Add a bevel modifier
    bevel = obj.modifiers.new(name="BevelCorners", type="BEVEL")
    bevel.width = 2.0
    bevel.limit_method = "WEIGHT"
    bevel.segments = 8

    # Apply the bevel modifier
    apply_bevel = True
    if apply_bevel:
        bpy.ops.object.modifier_apply(modifier=bevel.name)

        # Enter edit mode
        bpy.ops.object.mode_set(mode="EDIT")

        # Merge vertices that are close together
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.select_all(action="DESELECT")

    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


class Foot:
    inner_r = 6.5
    outer_r = inner_r + 2.0
    recess_h = 2.75
    base_h = 3.0
    top_h = 15.0

    @classmethod
    def foot_mesh_pos(cls, phase: float) -> cad.Mesh:
        mesh = cad.Mesh()
        l_orig = mesh.add_point(cad.Point(0.0, 0.0, 0.0))
        top = mesh.add_point(cad.Point(-cls.outer_r, 0.0, cls.top_h))

        lower_points: List[cad.MeshPoint] = []
        upper_points: List[cad.MeshPoint] = []

        fn = 24
        for n in range(fn):
            angle = ((360.0 / fn) * n) + phase
            rad = math.radians(angle)

            x = math.sin(rad) * cls.outer_r
            y = math.cos(rad) * cls.outer_r

            pl = mesh.add_point(cad.Point(x, y, 0.0))
            pu = mesh.add_point(cad.Point(x, y, cls.base_h))
            lower_points.append(pl)
            upper_points.append(pu)

        for idx in range(len(lower_points)):
            if idx + 1 == len(lower_points):
                l_next = lower_points[0]
                u_next = upper_points[0]
            else:
                l_next = lower_points[idx + 1]
                u_next = upper_points[idx + 1]

            mesh.add_tri(l_orig, l_next, lower_points[idx])
            mesh.add_tri(top, upper_points[idx], u_next)
            mesh.add_quad(u_next, upper_points[idx], lower_points[idx], l_next)

        return mesh

    @classmethod
    def foot_mesh_neg(cls, phase: float) -> cad.Mesh:
        bottom_h = -1.0

        mesh = cad.Mesh()
        l_orig = mesh.add_point(cad.Point(0.0, 0.0, bottom_h))
        u_orig = mesh.add_point(cad.Point(0.0, 0.0, cls.recess_h))

        lower_points: List[cad.MeshPoint] = []
        upper_points: List[cad.MeshPoint] = []

        fn = 24
        for n in range(fn):
            angle = ((360.0 / fn) * n) + phase
            rad = math.radians(angle)

            x = math.sin(rad) * cls.inner_r
            y = math.cos(rad) * cls.inner_r

            pl = mesh.add_point(cad.Point(x, y, bottom_h))
            pu = mesh.add_point(cad.Point(x, y, cls.recess_h))
            lower_points.append(pl)
            upper_points.append(pu)

        for idx in range(len(lower_points)):
            if idx + 1 == len(lower_points):
                l_next = lower_points[0]
                u_next = upper_points[0]
            else:
                l_next = lower_points[idx + 1]
                u_next = upper_points[idx + 1]

            mesh.add_tri(l_orig, l_next, lower_points[idx])
            mesh.add_tri(u_orig, upper_points[idx], u_next)
            mesh.add_quad(u_next, upper_points[idx], lower_points[idx], l_next)

        return mesh


def apply_to_wall(
    obj: bpy.types.Object,
    left: Point,
    right: Point,
    x: float = 0.0,
    z: float = 0.0,
) -> None:
    """Move the object on the X and Y axes so that it is centered on the
    wall between the left and right wall endpoints.

    The face of the object should be on the Y axis (this face will be aligned
    on the wall), and it should be centered on the X axis in order to end up
    centered on the wall.
    """
    wall_len = math.sqrt(((right.y - left.y) ** 2) + ((right.x - left.x) ** 2))
    angle = math.atan2(right.y - left.y, right.x - left.x)

    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)

        # Move the object along the x axis so it ends up centered on the wall.
        # This assumes the object starts centered around the origin.
        #
        # Also apply any extra X and Z translation supplied by the caller.
        bmesh.ops.translate(
            bm, verts=bm.verts, vec=(x + wall_len * 0.5, 0.0, z)
        )

        # Next rotate the object so it is at the same angle to the x axis
        # as the wall.
        bmesh.ops.rotate(
            bm,
            verts=bm.verts,
            cent=(0.0, 0.0, 0.0),
            matrix=mathutils.Matrix.Rotation(angle, 3, "Z"),
        )

        # Finally move the object from the origin so it is at the wall location
        bmesh.ops.translate(bm, verts=bm.verts, vec=(left.x, left.y, 0.0))

        bm.to_mesh(obj.data)
    finally:
        bm.free()


def foot_meshes(
    x: float, y: float, angle: float, phase: float
) -> Tuple[cad.Mesh, cad.Mesh]:
    neg_mesh = Foot.foot_mesh_neg(phase)
    pos_mesh = Foot.foot_mesh_pos(phase)
    pos_mesh.translate(Foot.outer_r, 0.0, 0.0)
    neg_mesh.translate(Foot.outer_r, 0.0, 0.0)
    pos_mesh.rotate(0.0, 0.0, angle)
    neg_mesh.rotate(0.0, 0.0, angle)
    pos_mesh.translate(x, y, 0.0)
    neg_mesh.translate(x, y, 0.0)

    return pos_mesh, neg_mesh


def gen_foot(
    name: str, x: float, y: float, angle: float, phase: float
) -> Tuple[bpy.types.Object, bpy.types.Object]:
    pos_mesh, neg_mesh = foot_meshes(x, y, angle, phase)

    neg = new_mesh_obj(f"{name}_neg", neg_mesh)
    foot = new_mesh_obj(name, pos_mesh)
    return foot, neg


def add_foot(
    kbd_obj: bpy.types.Object,
    x: float,
    y: float,
    angle: float,
    phase: float = 0.0,
    dbg: bool = False,
) -> Tuple[bpy.types.Object, bpy.types.Object]:
    """
    Add a foot to the keyboard object.

    (x, y) control the location.  The top of the foot will be at this location.
    angle controls the direction the foot is pointing.

    The phase parameter allows slightly rotating the angles at which the
    cylindrical vertices of the foot are placed.  This doesn't change the
    general shape of the foot or the direction it is pointing, but simply
    allows rotating the location of the vertices slightly.  This helps tweak
    the vertices to prevent blender from generating intersecting faces when
    performing the boolean union and difference, which can happen if the
    intersection points lie close to an existing vertex.  I set this parameter
    experimentally for each foot: Blender's 3D-Print tool can highlight
    intersecting edges.  When any were present on a foot, I tweaked its phase
    until blender no longer generates intersecting geometry on that foot.
    (Disabling the bevel on the interior corners would also have probably
    helped eliminate this bad geometry, but using this phase parameter allows
    keeping the bevel.)
    """
    pos, neg = gen_foot("foot", x, y, angle, phase)
    union(kbd_obj, pos)
    difference(kbd_obj, neg, apply_mod=not dbg)


def _get_foot_angle(x: float, y: float) -> float:
    # if x and y are both positive
    if x == 0.0:
        if y > 0.0:
            return 90
        return -90

    if x > 0.0:
        return math.degrees(math.atan(y / x))
    else:
        return 180.0 + math.degrees(math.atan(y / x))


def add_feet(kbd: Keyboard, kbd_obj: bpy.types.Object) -> None:
    # When placing the foot angled 45 degrees in a right angle corner, we want
    # to add this amount to the x and y directions so that it is tangent to the
    # walls
    off_45 = math.sqrt(
        ((math.sqrt((Foot.outer_r ** 2) * 2) - Foot.outer_r) ** 2) / 2
    )

    # Back right foot
    add_foot(
        kbd_obj,
        kbd.br.out3.x - off_45 - 0.3,
        kbd.br.out3.y - off_45 - 0.3,
        -135.0,
        1.5,
    )

    # Back left foot
    add_foot(
        kbd_obj, kbd.bl.out3.x + 0.3, kbd.bl.out3.y - off_45 - 0.3, -45.0, 5.0
    )

    # Front right foot
    add_foot(
        kbd_obj,
        kbd.fr.out3.x - off_45 - 0.2,
        kbd.fr.out3.y + off_45 + 0.2,
        135.0,
        0.0,
    )

    # Thumb bottom left foot
    # First compute the rotation angle
    dir1 = (kbd.thumb_tl.out2.point - kbd.thumb_bl.out2.point).unit()
    dir2 = (kbd.thumb_br.out2.point - kbd.thumb_bl.out2.point).unit()
    mid_dir = dir1 + dir2
    angle = _get_foot_angle(mid_dir.x, mid_dir.y)
    f = 3.3
    add_foot(
        kbd_obj,
        kbd.thumb_bl.out2.x + (mid_dir.x * f),
        kbd.thumb_bl.out2.y + (mid_dir.y * f),
        angle,
        7.0,
    )

    # Thumb top left foot
    # First compute the rotation angle
    dir1 = (kbd.thumb_tr.out2.point - kbd.thumb_tl.out2.point).unit()
    dir2 = (kbd.thumb_bl.out2.point - kbd.thumb_tl.out2.point).unit()
    mid_dir = dir1 + dir2
    angle = _get_foot_angle(mid_dir.x, mid_dir.y)
    f = 2.4
    add_foot(
        kbd_obj,
        kbd.thumb_tl.out2.x + (mid_dir.x * f),
        kbd.thumb_tl.out2.y + (mid_dir.y * f),
        angle,
    )


class I2cCutout:
    wall_thickness = 4.0
    # Make the front and back stick out 1mm past the wall, just to avoid
    # coincident faces when doing the boolean difference with the wall.
    back_y = wall_thickness + 1.0
    face_y = -1.0

    # If printing the holder face down, h = 4.5 is a good value.
    # However, if printing vertically with support needed to hold up the top
    # of the opening, then this value needs to be a little bit bigger.
    h = 4.8
    d = 4.05
    w = 20.6

    flange_d = 2.25
    flange_offset = 0.90

    nub_y = wall_thickness - (flange_d + flange_offset)
    nub_z = 0.75
    nub_x = 0.55

    @classmethod
    def main(cls) -> bpy.types.Object:
        """
        A cutout for the 5-pin magnetic connector I am using for the I2C
        connection: https://www.adafruit.com/product/5413
        """
        mesh = cad.Mesh()

        core_r = cls.h / 2.0
        half_h = cls.h * 0.5
        half_w = cls.w * 0.5
        left_face_points: List[MeshPoint] = []
        left_inner_points: List[MeshPoint] = []
        right_face_points: List[MeshPoint] = []
        right_inner_points: List[MeshPoint] = []

        right_orig = mesh.add_xyz(half_w - half_h, cls.face_y, 0.0)
        left_orig = mesh.add_xyz(-(half_w - half_h), cls.face_y, 0.0)

        inner_tl = mesh.add_xyz(-half_w, cls.flange_d, half_h)
        inner_tr = mesh.add_xyz(half_w, cls.flange_d, half_h)
        back_tl = mesh.add_xyz(-half_w, cls.back_y, half_h)
        back_tr = mesh.add_xyz(half_w, cls.back_y, half_h)

        inner_bl = mesh.add_xyz(-half_w, cls.flange_d, -half_h)
        inner_br = mesh.add_xyz(half_w, cls.flange_d, -half_h)
        back_bl = mesh.add_xyz(-half_w, cls.back_y, -half_h)
        back_br = mesh.add_xyz(half_w, cls.back_y, -half_h)

        back_tlo = mesh.add_xyz(left_orig.x, cls.back_y, half_h)
        back_tro = mesh.add_xyz(right_orig.x, cls.back_y, half_h)
        back_blo = mesh.add_xyz(left_orig.x, cls.back_y, -half_h)
        back_bro = mesh.add_xyz(right_orig.x, cls.back_y, -half_h)

        fn = 16
        for n in range(fn + 1):
            angle = (180.0 / fn) * n
            rad = math.radians(angle)

            x = math.sin(rad) * core_r
            z = math.cos(rad) * core_r
            right_face_points.append(
                mesh.add_xyz(right_orig.x + x, cls.face_y, z)
            )
            right_inner_points.append(
                mesh.add_xyz(right_orig.x + x, cls.flange_d, z)
            )
            left_face_points.append(
                mesh.add_xyz(left_orig.x - x, cls.face_y, z)
            )
            left_inner_points.append(
                mesh.add_xyz(left_orig.x - x, cls.flange_d, z)
            )

        for idx in range(1, len(right_face_points)):
            prev = idx - 1
            mesh.add_quad(
                right_inner_points[prev],
                right_inner_points[idx],
                right_face_points[idx],
                right_face_points[prev],
            )
            mesh.add_tri(
                right_orig, right_face_points[prev], right_face_points[idx]
            )
            mesh.add_quad(
                left_face_points[prev],
                left_face_points[idx],
                left_inner_points[idx],
                left_inner_points[prev],
            )
            mesh.add_tri(
                left_orig, left_face_points[idx], left_face_points[prev]
            )

            if idx < (len(right_face_points) / 2):
                left_corner = inner_tl
                right_corner = inner_tr
            else:
                left_corner = inner_bl
                right_corner = inner_br
            mesh.add_tri(
                left_corner, left_inner_points[prev], left_inner_points[idx]
            )
            mesh.add_tri(
                right_corner, right_inner_points[idx], right_inner_points[prev]
            )

        # Front face
        mesh.add_quad(
            left_face_points[0], right_face_points[0], right_orig, left_orig
        )
        mesh.add_quad(
            left_orig, right_orig, right_face_points[-1], left_face_points[-1]
        )
        # Cylinder cutout top
        mesh.add_quad(
            left_inner_points[0],
            right_inner_points[0],
            right_face_points[0],
            left_face_points[0],
        )
        # Cylinder cutout bottom
        mesh.add_quad(
            left_face_points[-1],
            right_face_points[-1],
            right_inner_points[-1],
            left_inner_points[-1],
        )

        # Back outer wall
        left_inner_mid = left_inner_points[len(left_inner_points) // 2]
        mesh.add_tri(back_tl, inner_tl, left_inner_mid)
        mesh.add_tri(back_bl, left_inner_mid, inner_bl)
        mesh.add_tri(back_tl, left_inner_mid, back_bl)

        right_inner_mid = right_inner_points[len(right_inner_points) // 2]
        mesh.add_tri(back_tr, right_inner_mid, inner_tr)
        mesh.add_tri(back_br, inner_br, right_inner_mid)
        mesh.add_tri(back_tr, back_br, right_inner_mid)

        mesh.add_quad(back_tl, back_tlo, left_inner_points[0], inner_tl)
        mesh.add_quad(
            back_tlo, back_tro, right_inner_points[0], left_inner_points[0]
        )
        mesh.add_quad(back_tro, back_tr, inner_tr, right_inner_points[0])

        mesh.add_quad(inner_bl, left_inner_points[-1], back_blo, back_bl)
        mesh.add_quad(
            left_inner_points[-1], right_inner_points[-1], back_bro, back_blo
        )
        mesh.add_quad(right_inner_points[-1], inner_br, back_br, back_bro)

        # Back face wall
        mesh.add_quad(back_tr, back_tro, back_bro, back_br)
        mesh.add_quad(back_tro, back_tlo, back_blo, back_bro)
        mesh.add_quad(back_tlo, back_tl, back_bl, back_blo)

        return new_mesh_obj("i2c_cutout", mesh)

    @classmethod
    def nub(
        cls, x: float, y: float, z: float, mirror_x: bool = False
    ) -> bpy.types.Object:
        t = 0.01  # extra tolerance to avoid coincident faces

        nub_mesh = cad.Mesh()
        b0 = nub_mesh.add_xyz(t, 0.0, -t)
        b1 = nub_mesh.add_xyz(-cls.nub_x, 0.0, -t)
        b2 = nub_mesh.add_xyz(t, cls.nub_y, -t)

        t0 = nub_mesh.add_xyz(t, 0.0, cls.nub_z + t)
        t1 = nub_mesh.add_xyz(-cls.nub_x, 0.0, cls.nub_z + t)
        t2 = nub_mesh.add_xyz(t, cls.nub_y, cls.nub_z + t)

        nub_mesh.add_tri(b0, b2, b1)
        nub_mesh.add_tri(t0, t1, t2)
        nub_mesh.add_quad(t1, b1, b2, t2)
        nub_mesh.add_quad(t2, b2, b0, t0)
        nub_mesh.add_quad(t0, b0, b1, t1)

        if mirror_x:
            nub_mesh.mirror_x()

        nub_mesh.translate(x, y, z)
        return new_mesh_obj("i2c_cutout_nub", nub_mesh)

    @classmethod
    def gen(cls) -> bpy.types.Object:
        main = cls.main()

        nub_tr = cls.nub(
            cls.w * 0.5,
            cls.flange_d + cls.flange_offset,
            cls.h * 0.5 - cls.nub_z,
        )
        difference(main, nub_tr)

        nub_br = cls.nub(
            cls.w * 0.5, cls.flange_d + cls.flange_offset, cls.h * -0.5
        )
        difference(main, nub_br)

        nub_tl = cls.nub(
            -cls.w * 0.5,
            cls.flange_d + cls.flange_offset,
            cls.h * 0.5 - cls.nub_z,
            mirror_x=True,
        )
        difference(main, nub_tl)

        nub_bl = cls.nub(
            -cls.w * 0.5,
            cls.flange_d + cls.flange_offset,
            cls.h * -0.5,
            mirror_x=True,
        )
        difference(main, nub_bl)
        return main


def add_i2c_connector(kbd: Keyboard, kbd_obj: bpy.types.Object) -> None:
    i2c_cutout = I2cCutout.gen()

    x_off = 0.0
    z_off = 5 + I2cCutout.h * 0.5
    apply_to_wall(
        i2c_cutout, kbd.thumb_tr_connect, kbd.thumb_tl.out2, x=x_off, z=z_off
    )

    difference(kbd_obj, i2c_cutout)


def gen_screw_hole(kbd: Keyboard) -> bpy.types.Object:
    # Big enough to fit a US #6 screw
    mesh = cad.Mesh()
    front_y = -1.0
    back_y = kbd.wall_thickness + 1.0

    front_center = mesh.add_xyz(0.0, front_y, 0.0)
    back_center = mesh.add_xyz(0.0, back_y, 0.0)
    front_points: List[MeshPoint] = []
    back_points: List[MeshPoint] = []

    r = 1.9
    fn = 24
    for n in range(fn):
        angle = (360.0 / fn) * n
        rad = math.radians(angle)

        circle_x = math.sin(rad) * r
        circle_z = math.cos(rad) * r

        front_points.append(mesh.add_xyz(circle_x, front_y, circle_z))
        back_points.append(mesh.add_xyz(circle_x, back_y, circle_z))

    for idx, fp in enumerate(front_points):
        # Note: this intentionally wraps around to -1 when idx == 0
        prev_f = front_points[idx - 1]
        prev_b = back_points[idx - 1]

        mesh.add_tri(front_center, prev_f, fp)
        mesh.add_tri(back_center, back_points[idx], prev_b)
        mesh.add_quad(prev_f, prev_b, back_points[idx], fp)

    return new_mesh_obj("screw_hole", mesh)


def add_screw_hole(
    kbd: Keyboard, kbd_obj: bpy.types.Object, x: float, z: float
) -> None:
    screw_hole = gen_screw_hole(kbd)
    apply_to_wall(screw_hole, kbd.fl.out2, kbd.fr.out2, x=x, z=z)
    difference(kbd_obj, screw_hole)


def add_screw_holes(kbd: Keyboard, kbd_obj: bpy.types.Object) -> None:
    x_spacing = 40
    add_screw_hole(kbd, kbd_obj, x=-x_spacing * 0.5, z=10)
    add_screw_hole(kbd, kbd_obj, x=x_spacing * 0.5, z=10)
    add_screw_hole(kbd, kbd_obj, x=-x_spacing * 0.5, z=25)
    add_screw_hole(kbd, kbd_obj, x=x_spacing * 0.5, z=25)

    # An extra screw hole on the thumb section
    if False:
        screw_hole = gen_screw_hole(kbd)
        apply_to_wall(
            screw_hole, kbd.thumb_bl.out2, kbd.thumb_br_connect, x=30, z=10
        )
        difference(kbd_obj, screw_hole)


def do_main() -> None:
    print("=" * 60)
    print("Generating keyboard...")

    delete_all()

    kbd = Keyboard()
    kbd.gen_mesh()

    kbd_obj = gen_keyboard(kbd)
    add_feet(kbd, kbd_obj)
    add_i2c_connector(kbd, kbd_obj)
    add_screw_holes(kbd, kbd_obj)

    bpy.ops.object.mode_set(mode="EDIT")
    print("done")


def command_line_main() -> None:
    try:
        do_main()

        # Adjust the camera to better show the keyboard
        layout = bpy.data.screens["Layout"]
        view_areas = [a for a in layout.areas if a.type == "VIEW_3D"]
        for a in view_areas:
            region = a.spaces.active.region_3d
            region.view_distance = 350
    except Exception as ex:
        import logging

        logging.exception(f"unhandled exception: {ex}")
        sys.exit(1)


def main() -> None:
    # If we are being run as a script on the command line,
    # then exit on error rather than let blender finish opening even though we
    # didn't run correctly.  We don't want this behavior when being run
    # on-demand in an existing blender session, though.
    for arg in sys.argv:
        if arg == "-P" or arg == "--python":
            command_line_main()
            return

    do_main()


if __name__ == "__main__":
    main()
