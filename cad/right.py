#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

"""Generate all parts for the right half of the keyboard.
To use, run "blender -P right.py"
"""

import os, sys

sys.path.insert(0, os.path.dirname(__file__))

from bcad import auto_update, blender_util

# Adjust the camera to better show the keyboard
blender_util.set_view_distance(350)

auto_update.main("mantyl.kbd_halves.right_full")
