#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

"""Generate the holder for the SX1509 breakout board.
To use, run "blender -P sx1509_holder.py"
"""

import os, sys

sys.path.insert(0, os.path.dirname(__file__))

from mantyl import auto_update, blender_util

# Adjust the camera to better show the keyboard
blender_util.set_view_distance(350)

auto_update.main("mantyl.sx1509_holder.upside_down")
