#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

"""A placeholder script to help do one-off testing of objects.
To use, run "blender -P test.py"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "bpycad"))
sys.path.insert(0, str(Path(__file__).parent))

from bpycad import auto_update, blender_util

blender_util.set_view_distance(350)
auto_update.main("mantyl.dev.test", ["bpycad", "mantyl"])
