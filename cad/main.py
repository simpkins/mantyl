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

import math
import random
import os
import sys
from typing import List, Union

sys.path.insert(0, os.path.dirname(__file__))

import cad
import oukey


def blender_mesh(name: str, mesh: Mesh) -> bpy.types.Mesh:
    points = [(p.x, p.y, p.z) for p in mesh.points]
    faces = [tuple(reversed(f)) for f in mesh.faces]

    blender_mesh = bpy.data.meshes.new("keyboard_mesh")
    blender_mesh.from_pydata(points, edges=[], faces=faces)
    blender_mesh.update()
    return blender_mesh


def new_mesh_obj(
    name: str, mesh: Union[cad.Mesh, bpy.types.Mesh]
) -> bpy.types.Object:
    if isinstance(mesh, cad.Mesh):
        mesh = blender_mesh(f"{name}_mesh", mesh)

    obj = bpy.data.objects.new(name, mesh)
    collection = bpy.data.collections[0]
    collection.objects.link(obj)

    # Select the newly created object
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    return obj


def gen_keyboard(kbd: oukey.Keyboard) -> bpy.types.Object:
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


def boolean_op(
    obj1: bpy.types.Object,
    obj2: bpy.types.Object,
    op: str,
    apply_mod: bool = True,
) -> None:
    """
    Modifies obj1 by performing a boolean operation with obj2.

    If apply_mod is True, the modifier is applied and obj2 is deleted before reutrning.
    if apply_mod is False, obj2 cannot be deleted before applying the modifier.
    """
    bpy.ops.object.select_all(action="DESELECT")
    obj1.select_set(True)
    bpy.context.view_layer.objects.active = obj1

    randn = random.randint(0, 1000000)
    mod_name = f"bool_op_{randn}"
    mod = obj1.modifiers.new(name=mod_name, type="BOOLEAN")
    mod.object = obj2
    mod.operation = op
    mod.double_threshold = 1e-12

    if apply_mod:
        bpy.ops.object.modifier_apply(modifier=mod.name)

        bpy.ops.object.select_all(action="DESELECT")
        obj2.select_set(True)
        bpy.ops.object.delete(use_global=False)

        # Enter edit mode
        bpy.ops.object.mode_set(mode="EDIT")

        # Merge vertices that are close together
        # Do this after every boolean operator, otherwise blender ends up
        # leaving slightly bad geometry in some cases where the intersections
        # are close to existing vertices.
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.select_all(action="DESELECT")

        bpy.ops.object.mode_set(mode="OBJECT")


def difference(
    obj1: bpy.types.Object, obj2: bpy.types.Object, apply_mod: bool = True
) -> None:
    boolean_op(obj1, obj2, "DIFFERENCE", apply_mod=apply_mod)


def union(
    obj1: bpy.types.Object, obj2: bpy.types.Object, apply_mod: bool = True
) -> None:
    boolean_op(obj1, obj2, "UNION", apply_mod=apply_mod)


def foot_meshes(
    x: float, y: float, angle: float, phase: float
) -> Tuple[cad.mesh, cad.mesh]:
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


def delete_all() -> None:
    if bpy.context.object is not None:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


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


def do_main() -> None:
    print("=" * 60)
    print("Generating keyboard...")

    delete_all()

    kbd = oukey.Keyboard()
    kbd.gen_mesh()

    kbd_obj = gen_keyboard(kbd)

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
        kbd_obj, kbd.bl.out3.x + 0.3, kbd.bl.out3.y - off_45 - 0.3, -45.0, 3.0
    )

    # Front right foot
    add_foot(
        kbd_obj,
        kbd.fr.out3.x - off_45 - 0.1,
        kbd.fr.out3.y + off_45 + 0.1,
        135.0,
        2.0,
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
        7.0
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
