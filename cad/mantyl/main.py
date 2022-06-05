#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

import bpy

from .blender_util import delete_all
from .kbd_halves import right_half


def regenerate() -> None:
    print("=" * 60)
    print("Generating keyboard...")

    delete_all()
    right_half()

    bpy.ops.object.mode_set(mode="EDIT")
    print("done")
