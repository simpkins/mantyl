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

from bpycad import dev_main

dev_main.main(["bpycad", "mantyl"], "mantyl.dev.test")
