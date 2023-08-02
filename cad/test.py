#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

"""A placeholder script to help do one-off testing of objects.
To use, run "blender -P test.py"
"""

import os, sys

sys.path.insert(0, os.path.dirname(__file__))

from bcad import auto_update, blender_util

blender_util.set_view_distance(350)
auto_update.main("mantyl.testing.test", ["bcad", "mantyl"])
