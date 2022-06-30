#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

import bpy

from . import kbd_halves
from . import key_socket_holder


def test() -> None:
    #kbd_halves.right_half()
    #kbd_halves.right_socket_underlay()
    #kbd_halves.right_thumb_underlay()

    #kbd_halves.left_half()
    #kbd_halves.left_socket_underlay()
    #kbd_halves.left_thumb_underlay()

    from . import i2c_conn
    i2c_conn.test()

    bpy.ops.object.mode_set(mode="EDIT")
    # blender_util.set_shading_mode("WIREFRAME")