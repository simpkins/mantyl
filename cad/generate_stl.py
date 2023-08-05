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

from bcad import blender_util
from mantyl import (
    i2c_conn,
    kbd_halves,
    oled_holder,
    screw_holes,
    sx1509_holder,
    wrist_rest,
    usb_cutout,
)

import bpy

import argparse
from pathlib import Path
from typing import Callable, Dict

out_dir: Path = Path(base_dir) / "_out"


def export_stl(name: str, obj_fn: Callable[[], bpy.types.Object]) -> None:
    print(f"Exporting {name}...")
    blender_util.delete_all()
    obj = obj_fn()

    out_path = out_dir / f"{name}.stl"
    bpy.ops.export_mesh.stl(filepath=str(out_path))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "models", metavar="MODEL", nargs="*", help="The models to export"
    )
    args = ap.parse_args(blender_util.get_script_args())

    out_dir.mkdir(parents=True, exist_ok=True)

    models: Dict[str, Callable[[], bpy.types.Object]] = {
        "right_shell": kbd_halves.right_shell,
        "right_underlay": kbd_halves.right_socket_underlay,
        "right_thumb_underlay": kbd_halves.right_thumb_underlay,
        "left_shell": kbd_halves.left_shell,
        "left_underlay": kbd_halves.left_socket_underlay,
        "left_thumb_underlay": kbd_halves.left_thumb_underlay,
        "oled_backplate": oled_holder.oled_backplate_left,
        "usb_backplate": usb_cutout.backplate,
        "right_wrist_rest": wrist_rest.right,
        "left_wrist_rest": wrist_rest.left,
        "cable_cap": i2c_conn.cable_cap,
    }

    if args.models:
        model_names = args.models
        unknown_names = [name for name in args.models if name not in models]
        if unknown_names:
            unknown_names_str = ", ".join(unknown_names)
            ap.error(f"unknown model: {unknown_names_str}")
    else:
        model_names = list(sorted(models.keys()))

    for name in model_names:
        export_stl(name, models[name])

    sys.exit(0)


main()
