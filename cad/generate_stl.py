#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

"""Export STL files for all of the parts.
To use, run "blender -b -P generate_stl.py"
"""

from __future__ import annotations

import os, sys

base_dir: str = os.path.dirname(__file__)
sys.path.insert(0, base_dir)

from mantyl import (
    blender_util,
    i2c_conn,
    kbd_halves,
    oled_holder,
    screw_holes,
    sx1509_holder,
    wrist_rest,
    usb_cutout,
)

import bpy

from pathlib import Path
from typing import Callable

out_dir: Path = Path(base_dir) / "_out"


def export_stl(name: str, obj_fn: Callable[[], bpy.types.Object]) -> None:
    print(f"Exporting {name}...")
    blender_util.delete_all()
    obj = obj_fn()

    out_path = out_dir / f"{name}.stl"
    bpy.ops.export_mesh.stl(filepath=str(out_path))


def main() -> None:
    blender_util.set_view_distance(350)

    out_dir.mkdir(parents=True, exist_ok=True)

    export_stl("right_shell", kbd_halves.right_shell)
    export_stl("right_underlay", kbd_halves.right_socket_underlay)
    export_stl("right_thumb_underlay", kbd_halves.right_thumb_underlay)
    export_stl("left_shell", kbd_halves.left_shell)
    export_stl("left_underlay", kbd_halves.left_socket_underlay)
    export_stl("left_thumb_underlay", kbd_halves.left_thumb_underlay)
    export_stl("oled_backplate", oled_holder.oled_backplate_left)
    export_stl("usb_backplate", usb_cutout.backplate)
    export_stl("right_wrist_rest", wrist_rest.right)
    export_stl("left_wrist_rest", wrist_rest.left)
    export_stl("cable_cap", i2c_conn.cable_cap)

    sys.exit(0)


main()
