#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

import logging
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import oukey2


def blender_mesh(mesh: Mesh) -> Shape:
    points = [(p.x, p.y, p.z) for p in mesh.points]
    faces = [tuple(reversed(f)) for f in mesh.faces]

    bmesh = bpy.data.meshes.new("keyboard_mesh")
    bmesh.from_pydata(points, edges=[], faces=faces)
    bmesh.update()
    return bmesh


def main() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    print("Generating keyboard...")
    grid = oukey2.KeyGrid()
    grid.gen_main_grid()
    grid.gen_main_grid_edges()
    #grid.gen_back_wall()
    #grid.gen_right_wall()

    bmesh = blender_mesh(grid.mesh)
    obj = bpy.data.objects.new("keyboard", bmesh)

    collection = bpy.data.collections.new("collection")
    bpy.context.scene.collection.children.link(collection)
    collection.objects.link(obj)
    print("done")


try:
    main()
except Exception as ex:
    logging.exception(f"unhandled exception: {ex}")
    sys.exit(1)
