#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import math
import random
from typing import Union

import bpy
import bmesh
import mathutils

from . import cad


def delete_all() -> None:
    if bpy.context.object is not None:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def blender_mesh(name: str, mesh: cad.Mesh) -> bpy.types.Mesh:
    points = [(p.x, p.y, p.z) for p in mesh.points]
    faces = [tuple(reversed(f)) for f in mesh.faces]

    blender_mesh = bpy.data.meshes.new(name)
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


def apply_to_wall(
    obj: bpy.types.Object,
    left: cad.Point,
    right: cad.Point,
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
