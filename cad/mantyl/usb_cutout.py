#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from . import blender_util

import bpy


def test() -> bpy.types.Object:
    return blender_util.range_cube((-10, 10), (0.0, 4.0), (0.0, 10.0))
