#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

import bpy

from . import blender_util, cad


def blender_cube(
    x: float, y: float, z: float, name: str = "cube"
) -> bpy.types.Object:
    mesh = cad.cube(x, y, z)
    return blender_util.new_mesh_obj(name, mesh)


def blender_cylinder(
    r: float, h: float, fn: int = 24, name: str = "cylinder"
) -> bpy.types.Object:
    mesh = cad.cylinder(r, h, fn=fn)
    return blender_util.new_mesh_obj(name, mesh)


def socket_holder_obj() -> bpy.types.Object:
    width = 12.0
    height = 18.0
    thickness = 1.0

    obj = blender_cube(width, height, thickness, name="socket_holder")
    with blender_util.TransformContext(obj) as ctx:
        ctx.translate(0, 0, -thickness * 0.5)

    # Cut-outs for the switch legs
    leg_r_cutout = blender_cylinder(r=1.6, h=thickness * 2, fn=85)
    with blender_util.TransformContext(leg_r_cutout) as ctx:
        ctx.translate(3.65, -2.7, -thickness)
    leg_l_cutout = blender_cylinder(r=1.6, h=thickness * 2, fn=85)
    with blender_util.TransformContext(leg_l_cutout) as ctx:
        ctx.translate(-2.7, -5.2, -thickness)

    # Cut-out for the switch stabilizer
    main_cutout = blender_cylinder(r=2.1, h=thickness * 2, fn=98)
    with blender_util.TransformContext(main_cutout) as ctx:
        ctx.rotate(90, "Z")
        ctx.translate(0, 0, -thickness)

    blender_util.difference(obj, leg_r_cutout)
    blender_util.difference(obj, leg_l_cutout)
    blender_util.difference(obj, main_cutout)

    return obj


def socket_holder() -> bpy.types.Object:
    obj = socket_holder_obj()
    bpy.context.view_layer.objects.active = obj
