#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#
from __future__ import annotations

import sys
from typing import TextIO


class Key:
    key_size = 19
    global_y_offset = -12

    def __init__(
        self, name: str, index: int, x: float, y: float, cap: str
    ) -> None:
        self.name = name
        self.index = index
        self.x = x
        self.y = y
        self.cap = cap

    def write(self, out: TextIO) -> None:
        sw_x = (self.key_size * 1.5) - self.x * self.key_size
        sw_y = self.global_y_offset - (self.y * self.key_size)

        led_x = sw_x
        led_y = sw_y + 5.08

        d_x = sw_x - 5.75
        d_y = sw_y

        cap_x = led_x - 4.75
        cap_y = led_y + 0.75

        out.write(f"    SW{self.index}: # {self.name}\n")
        out.write(f"        location: [{sw_x}, {sw_y}]\n")
        out.write("        flip: True\n")
        out.write("        rotation: 180\n")
        out.write(f"    D{self.index + 20}: # {self.name} diode\n")
        out.write(f"        location: [{d_x}, {d_y}]\n")
        out.write("        rotation: 270\n")

        out.write(f"    D{self.index}: # {self.name} LED\n")
        out.write(f"        location: [{led_x}, {led_y}]\n")
        out.write(f"    {self.cap}: # {self.name} LED capacitor\n")
        out.write(f"        location: [{cap_x}, {cap_y}]\n")


def main() -> None:
    out = sys.stdout
    out.write("origin: [90, 98]\n")
    keys = [
        Key("KP1", 3, 0, -1, "C22"),
        Key("KP2", 4, 1, -1, "C27"),
        Key("KP3", 5, 2, -1, "C31"),
        Key("KP4", 7, 0, 0, "C21"),
        Key("KP5", 8, 1, 0, "C26"),
        Key("KP6", 9, 2, 0, "C30"),
        Key("KP7", 10, 0, 1, "C20"),
        Key("KP8", 11, 1, 1, "C25"),
        Key("KP9", 12, 2, 1, "C29"),
        Key("KP_Extra", 14, 0, 2, "C19"),
        Key("KP_Slash", 15, 1, 2, "C24"),
        Key("KP_Star", 16, 2, 2, "C28"),
        Key("KP_Minus", 17, 3, 2, "C33"),
        Key("KP0", 1, 0.5, -2, "C23"),
        Key("KP_Dot", 2, 2, -2, "C32"),
        Key("KP_Plus", 13, 3, 0.5, "C34"),
        Key("KP_Enter", 6, 3, -1.5, "C35"),
    ]

    out.write("components:\n")
    for key in keys:
        key.write(out)

    esp32_pos = (-37.25, 9.5)
    esp32_y = esp32_pos[1] + Key.global_y_offset
    out.write("    U1:\n")
    out.write(f"        location: [{esp32_pos[0]}, {esp32_y}]")


if __name__ == "__main__":
    main()
