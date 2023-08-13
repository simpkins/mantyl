#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from __future__ import annotations

from bpycad import blender_util

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


def numpad_board() -> bpy.types.Object:
    l = 94
    w = 80
    board_d = 1.57
    obj = blender_util.cube(w, l, board_d, "controller")

    soc_l = 15
    soc_w = 40
    overlap_l = 2
    soc = blender_util.cube(soc_w, soc_l + overlap_l, board_d)
    with blender_util.TransformContext(soc) as ctx:
        ctx.translate(0, -(l + soc_l - overlap_l) * 0.5, 0)

    blender_util.union(obj, soc)

    return obj
