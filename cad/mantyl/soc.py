#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from __future__ import annotations

from .numpad import NumpadSection

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


def esp32s3_wroom_1() -> bpy.types.Object:
    l = 25.5
    w = 18
    pcb_d = 0.8
    antenna_len = 6
    obj = blender_util.cube(w, l, pcb_d, "ESP32-S3-WROOM-1")
    with blender_util.TransformContext(obj) as ctx:
        ctx.translate(0, antenna_len * 0.5, pcb_d * 0.5)

    mod_w = 15.8
    mod_l = 17.6
    mod_d = 3.1 - pcb_d
    d_overlap = pcb_d * 0.5
    module = blender_util.cube(mod_w, mod_l, mod_d + d_overlap)
    with blender_util.TransformContext(module) as ctx:
        ctx.translate(0, 0, pcb_d + (mod_d - d_overlap) * 0.5)

    blender_util.union(obj, module)
    return obj


def esp32s3_wroom_1u() -> bpy.types.Object:
    l = 19.2
    w = 18
    pcb_d = 0.8
    obj = blender_util.cube(w, l, pcb_d, "ESP32-S3-WROOM-1")

    mod_w = 15.65
    mod_l = 17.5
    mod_d = 3.2 - pcb_d
    d_overlap = pcb_d * 0.5
    module = blender_util.cube(mod_w, mod_l, mod_d + d_overlap)
    with blender_util.TransformContext(module) as ctx:
        ctx.translate(0, 0, pcb_d + (mod_d - d_overlap) * 0.5)

    blender_util.union(obj, module)
    return obj


PCB_THICKNESS = 1.6


def numpad_pcb_mesh() -> cad.Mesh:
    mesh = cad.Mesh()
    perim_xy: List[Tuple[float, float]] = [
        (16, -57),
        (53, -16),
        (53, 33),
        (44, 59),
        (-44, 59),
        (-47, 50),
        (-47, -22),
        (-16, -57),
    ]
    perim: List[Tuple[cad.MeshPoint, cad.MeshPoint]] = []
    for x, y in perim_xy:
        t = mesh.add_xyz(x, y, PCB_THICKNESS)
        b = mesh.add_xyz(x, y, 0)
        perim.append((t, b))

    top_face_indices = [t.index for t, b in reversed(perim)]
    # pyre-fixme[6]: we are letting blender deal with a polygon face here,
    #     but we did not declare typing in cad.Mesh to allow polygon faces
    mesh.faces.append(top_face_indices)
    bottom_face_indices = [b.index for t, b in perim]
    # pyre-fixme[6]: we are letting blender deal with a polygon face here,
    #     but we did not declare typing in cad.Mesh to allow polygon faces
    mesh.faces.append(bottom_face_indices)

    for idx in range(len(perim)):
        mesh.add_quad(
            perim[idx - 1][0], perim[idx][0], perim[idx][1], perim[idx - 1][1]
        )

    return mesh


def numpad_pcb() -> bpy.types.Object:
    mesh = numpad_pcb_mesh()
    bmesh = blender_util.blender_mesh(f"pcb_mesh", mesh)
    obj = blender_util.new_mesh_obj("numpad_pcb", bmesh)

    esp32 = esp32s3_wroom_1()
    esp32_x = -37.25
    esp32_y = 3.5
    #y_offset = NumpadSection.global_y_offset - (0.5 * NumpadSection.key_size) + 2
    with blender_util.TransformContext(esp32) as ctx:
        ctx.rotate(90, "Z")
        ctx.translate(esp32_x, esp32_y, PCB_THICKNESS)
    blender_util.union(obj, esp32)

    key_positions = [
        (28.5, 6),  # KP1
        (9.5, 6),  # KP2
        (-9.5, 6),  # KP3
        (28.5, -13),  # KP4
        (9.5, -13),  # KP5
        (-9.5, -13),  # KP6
        (28.5, -32),  # KP7
        (9.5, -32),  # KP8
        (-9.5, -32),  # KP9

        (28.5, -51),  # KP_Extra
        (9.5, -51),  # KP_Slash
        (-9.5, -51),  # KP_Star
        (-28.5, -51),  # KP_Minus

        (19.0, 25),  # KP0
        (-9.5, 25),  # KP_Dot

        (-28.5, -22.5),  # KP_Plus
        (-28.5, 15.5),  # KP_Enter
    ]
    d = 6.75
    for x, y in key_positions:
        c = blender_util.range_cube((-d, d), (-d, d), (-10, 10))
        with blender_util.TransformContext(c) as ctx:
            ctx.translate(x, -y, 0.0)
        blender_util.union(obj, c)

    return obj
