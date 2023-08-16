#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from __future__ import annotations

from typing import List, Tuple

from bpycad import blender_util
from bpycad import cad

import bpy


def esp32s3_wroom_devkit_c() -> bpy.types.Object:
    # Dimensions datasheet:
    # https://dl.espressif.com/dl/DXF_ESP32-S3-DevKitC-1_V1_20210312CB.pdf
    #
    # Length = 70mm (including antenna)
    # Width = 25.5mm
    l = 63
    w = 25.5
    board_d = 1.57
    obj = blender_util.cube(w, l, board_d, "esp32s3_wroom_devkit_c")

    antenna_l = 7
    antenna_w = 18
    overlap_l = 2
    antenna = blender_util.cube(antenna_w, antenna_l + overlap_l, board_d)
    with blender_util.TransformContext(antenna) as ctx:
        ctx.translate(0, (l + antenna_l - overlap_l) * 0.5, 0)

    blender_util.union(obj, antenna)

    return obj


def numpad_pcb() -> cad.Mesh:
    board_d = 1.57

    mesh = cad.Mesh()
    perim_xy: List[Tuple[float, float]] = [
        (42, 47),
        (-42, 47),
        (-50, 30),
        (-50, -30),
        (-16, -69),
        (16, -69),
        (50, -30),
        (50, 30),
    ]
    perim: List[Tuple[cad.MeshPoint, cad.MeshPoint]] = []
    for x, y in perim_xy:
        t = mesh.add_xyz(x, y, 0)
        b = mesh.add_xyz(x, y, -board_d)
        perim.append((t, b))

    top_face_indices = [t.index for t, b in reversed(perim)]
    mesh.faces.append(top_face_indices)
    bottom_face_indices = [b.index for t, b in perim]
    mesh.faces.append(bottom_face_indices)

    for idx in range(len(perim)):
        mesh.add_quad(perim[idx - 1][0], perim[idx][0], perim[idx][1], perim[idx - 1][1])

    return mesh
