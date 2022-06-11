#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

import bpy

from .blender_util import delete_all
from .kbd_halves import right_half
from .key_socket_holder import socket_holder


def regenerate() -> None:
    delete_all()
    #right_half()
    socket_holder()

    bpy.ops.object.mode_set(mode="EDIT")
    # blender_util.set_shading_mode("WIREFRAME")
