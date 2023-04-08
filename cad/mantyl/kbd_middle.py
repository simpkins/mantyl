#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from . import blender_util
from . import kbd_halves


def middle() -> None:
    x_separation = 150

    print("=" * 60)
    print("Right half...")
    right = kbd_halves.right_shell_simple()
    with blender_util.TransformContext(right) as ctx:
        ctx.translate(x_separation, 0, 0)

    print("=" * 60)
    print("Left half...")
    left = kbd_halves.left_shell_simple()
    with blender_util.TransformContext(left) as ctx:
        ctx.translate(-x_separation, 0, 0)
