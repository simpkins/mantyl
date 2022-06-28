#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

import bpy

from . import kbd_halves
from . import key_socket_holder


def test() -> None:
    # kbd_halves.right_half()
    # kbd_halves.right_socket_underlay()
    kbd_halves.right_thumb_underlay()
    # key_socket_holder.socket_holder()
    # key_socket_holder.cad_top_socket_holder()

    bpy.ops.object.mode_set(mode="EDIT")
    # blender_util.set_shading_mode("WIREFRAME")
