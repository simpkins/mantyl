#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

"""Generate the underlay that holds the switch sockets for the right half.
To use, run "blender -P right_underlay.py"
"""

import os, sys

sys.path.insert(0, os.path.dirname(__file__))

from mantyl import auto_update, blender_util

# Adjust the camera to better show the keyboard
blender_util.set_view_distance(350)

auto_update.main("mantyl.kbd_halves.right_thumb_underlay")
