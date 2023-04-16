#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from __future__ import annotations

import bpy
from typing import List

from . import blender_util
from .cad import Mesh, Transform
from .keyboard import KeyHole


def test() -> bpy.types.Object:
    mesh = Mesh()

    offset = 19
    keys: List[KeyHole] = []
    for y_off in (-offset, 0, offset):
        for x_off in (-offset, 0, offset):
            kh = KeyHole(mesh, Transform().translate(x_off, y_off, 0))
            kh.inner_walls()
            keys.append(kh)

    kp1 = keys[0]
    kp2 = keys[1]
    kp3 = keys[2]
    kp4 = keys[3]
    kp5 = keys[4]
    kp6 = keys[5]
    kp7 = keys[6]
    kp8 = keys[7]
    kp9 = keys[8]

    kp7.join_bottom(kp4)
    kp4.join_bottom(kp1)
    kp8.join_bottom(kp5)
    kp5.join_bottom(kp2)
    kp9.join_bottom(kp6)
    kp6.join_bottom(kp3)

    kp7.join_right(kp8)
    kp8.join_right(kp9)
    kp4.join_right(kp5)
    kp5.join_right(kp6)
    kp1.join_right(kp2)
    kp2.join_right(kp3)

    blend_mesh = blender_util.blender_mesh("numpad_mesh", mesh)
    obj = blender_util.new_mesh_obj("numpad", blend_mesh)
    return obj
