#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy
import bmesh

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import oukey2


def blender_mesh(mesh: Mesh) -> Shape:
    points = [(p.x, p.y, p.z) for p in mesh.points]
    faces = [tuple(reversed(f)) for f in mesh.faces]

    blender_mesh = bpy.data.meshes.new("keyboard_mesh")
    blender_mesh.from_pydata(points, edges=[], faces=faces)
    blender_mesh.update()
    return blender_mesh


def main() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    print("Generating keyboard...")
    kbd = oukey2.Keyboard()
    kbd.gen_mesh()

    mesh = blender_mesh(kbd.mesh)
    obj = bpy.data.objects.new("keyboard", mesh)

    collection = bpy.data.collections.new("collection")
    bpy.context.scene.collection.children.link(collection)
    collection.objects.link(obj)

    # Select the keyboard
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

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
    bevel = obj.modifiers.new(name="BevelCorners", type='BEVEL')
    bevel.width = 2.0
    bevel.limit_method = "WEIGHT"
    bevel.segments = 8

    # Adjust the camera to better show the keyboard
    layout = bpy.data.screens["Layout"]
    view_areas = [a for a in layout.areas if a.type == "VIEW_3D"]
    for a in view_areas:
        region = a.spaces.active.region_3d
        region.view_distance = 350

    # Enter edit mode
    bpy.ops.object.mode_set(mode="EDIT")

    print("done")


try:
    main()
except Exception as ex:
    logging.exception(f"unhandled exception: {ex}")
    sys.exit(1)
