#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from . import cover
from . import i2c_conn
from . import foot
from . import kbd_halves
from . import keyboard
from . import numpad
from . import oled_holder
from . import soc
from . import sx1509_holder
from . import usb_cutout
from . import wrist_rest

from bpycad import blender_util

import bpy


def test() -> None:
    settings = kbd_halves.GenSettings()
    # settings.simple_shells = True
    # settings.show_right = False
    # settings.show_left = False
    # settings.show_cover = False
    # settings.show_wrist_rests = False
    # settings.show_keycaps = True
    # settings.show_controller = True

    # kbd_halves.generate_all(settings)
    kbd = keyboard.Keyboard()
    kbd.gen_mesh()
    kbd_halves.right_shell_obj(kbd)

    # cover.test()

    # soc.numpad_pcb()
    # kbd_halves.right_full()
    # shell = kbd_halves.right_shell()
    # cover.gen_cover(shell)
    # kbd_halves.right_socket_underlay()
    # kbd_halves.right_thumb_underlay()

    # kbd_halves.left_full()
    # kbd_halves.left_shell()
    # kbd_halves.left_socket_underlay()
    # kbd_halves.left_thumb_underlay()
    # kbd_halves.left_oled_backplate()

    bpy.ops.object.mode_set(mode="EDIT")
    #blender_util.set_shading_mode("WIREFRAME")
