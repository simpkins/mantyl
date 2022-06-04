#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

"""A script to generate the keyboard mesh in Blender.
To use, run "blender -P blender.py"
"""

from __future__ import annotations

import bpy

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from mantyl.blender_util import delete_all
from mantyl.kbd_halves import right_half


def do_main() -> None:
    print("=" * 60)
    print("Generating keyboard...")

    delete_all()

    right_half()

    bpy.ops.object.mode_set(mode="EDIT")
    print("done")


def command_line_main() -> None:
    try:
        do_main()

        # Adjust the camera to better show the keyboard
        layout = bpy.data.screens["Layout"]
        view_areas = [a for a in layout.areas if a.type == "VIEW_3D"]
        for a in view_areas:
            region = a.spaces.active.region_3d
            region.view_distance = 350
    except Exception as ex:
        import logging

        logging.exception(f"unhandled exception: {ex}")
        sys.exit(1)


def main() -> None:
    # If we are being run as a script on the command line,
    # then exit on error rather than let blender finish opening even though we
    # didn't run correctly.  We don't want this behavior when being run
    # on-demand in an existing blender session, though.
    for arg in sys.argv:
        if arg == "-P" or arg == "--python":
            command_line_main()
            return

    do_main()


if __name__ == "__main__":
    main()
