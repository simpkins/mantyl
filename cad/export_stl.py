#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

"""Export STL files for all of the parts.
To use, run "blender -b -P generate_stl.py"
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "bpycad"))
sys.path.insert(0, str(Path(__file__).parent))

from bpycad import export_stl

from mantyl import (
    i2c_conn,
    kbd_halves,
    oled_holder,
    screw_holes,
    sx1509_holder,
    wrist_rest,
    usb_cutout,
)

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

export_stl.main(models)
