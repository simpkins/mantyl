#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import math
import random
from typing import Optional, Type, Union
from types import TracebackType

import bpy
import bmesh
import mathutils

from . import cad


def delete_all() -> None:
    if bpy.context.object is not None:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def set_view_distance(distance: float) -> None:
    """Update the camera distance in all viewport panels"""
    layout = bpy.data.screens["Layout"]
    view_areas = [a for a in layout.areas if a.type == "VIEW_3D"]
    for a in view_areas:
        region = a.spaces.active.region_3d
        region.view_distance = distance


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

    with TransformContext(obj) as ctx:
        # Move the object along the x axis so it ends up centered on the wall.
        # This assumes the object starts centered around the origin.
        #
        # Also apply any extra X and Z translation supplied by the caller.
        ctx.translate(x + wall_len * 0.5, 0.0, z)

        # Next rotate the object so it is at the same angle to the x axis
        # as the wall.
        ctx.rotate(math.degrees(angle), "Z")

        # Finally move the object from the origin so it is at the wall location
        ctx.translate(left.x, left.y, 0.0)


class TransformContext:
    def __init__(self, obj: bpy.types.Object) -> None:
        self.obj = obj
        self.bmesh = bmesh.new()
        self.bmesh.from_mesh(obj.data)

    def __enter__(self) -> TransformContext:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if exc_value is None:
            self.bmesh.to_mesh(self.obj.data)
        self.bmesh.free()

    def rotate(
        self,
        angle: float,
        axis: str,
        center: Optional[Tuple[float, float, float]] = None,
    ) -> None:
        if center is None:
            center = (0.0, 0.0, 0.0)

        bmesh.ops.rotate(
            self.bmesh,
            verts=self.bmesh.verts,
            cent=center,
            matrix=mathutils.Matrix.Rotation(math.radians(angle), 3, axis),
        )

    def translate(self, x: float, y: float, z: float) -> None:
        bmesh.ops.translate(self.bmesh, verts=self.bmesh.verts, vec=(x, y, z))

    def transform(self, tf: cad.Transform) -> None:
        matrix = mathutils.Matrix(tf._data)
        bmesh.ops.transform(self.bmesh, verts=self.bmesh.verts, matrix=matrix)

    def triangulate(self) -> None:
        bmesh.ops.triangulate(self.bmesh, faces=self.bmesh.faces[:])

    def mirror_x(self) -> None:
        geom = self.bmesh.faces[:] + self.bmesh.verts[:] + self.bmesh.edges[:]
        # Mirror creates new mirrored geometry
        # Set merge_dist to a negative value to prevent any of the new mirrored
        # geometry from being merged with the original vertices.
        ret = bmesh.ops.mirror(
            self.bmesh, geom=geom, axis="X", merge_dist=-1.0
        )
        # Delete the original geometry
        bmesh.ops.delete(self.bmesh, geom=geom)
        # Reverse the faces to restore the correct normal direction
        bmesh.ops.reverse_faces(
            self.bmesh, faces=self.bmesh.faces[:]
        )


def set_shading_mode(mode: str) -> None:
    for area in bpy.context.workspace.screens[0].areas:
        for space in area.spaces:
            if space.type == "VIEW_3D":
                space.shading.type = mode


def cube(x: float, y: float, z: float, name: str = "cube") -> bpy.types.Object:
    mesh = cad.cube(x, y, z)
    return new_mesh_obj(name, mesh)


def range_cube(
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    z_range: Tuple[float, float],
    name: str = "cube",
) -> bpy.types.Object:
    mesh = cad.range_cube(x_range, y_range, z_range)
    return new_mesh_obj(name, mesh)


def cylinder(
    r: float,
    h: float,
    fn: int = 24,
    rotation: float = 360.0,
    name: str = "cylinder",
    r2: Optional[float] = None,
) -> bpy.types.Object:
    mesh = cad.cylinder(r, h, fn=fn, rotation=rotation, r2=r2)
    return new_mesh_obj(name, mesh)


def cone(
    r: float,
    h: float,
    fn: int = 24,
    rotation: float = 360.0,
    name: str = "cylinder",
) -> bpy.types.Object:
    mesh = cad.cone(r, h, fn=fn, rotation=rotation)
    return new_mesh_obj(name, mesh)
