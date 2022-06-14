#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

import bpy

from .blender_util import delete_all
from . import kbd_halves
from .key_socket_holder import socket_holder


def regenerate() -> None:
    delete_all()
    #kbd_halves.right_half()
    kbd_halves.right_socket_grid()

    bpy.ops.object.mode_set(mode="EDIT")
    # blender_util.set_shading_mode("WIREFRAME")
