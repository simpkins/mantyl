#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

"""
Generate JLCPCB production files from a Kicad project.
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Set

logger = logging.getLogger("export")


class Exporter:
    kicad_cli: str = "kicad-cli"

    def __init__(self, pcb: Path, output_dir: Path) -> None:
        self.pcb = pcb
        self.output_dir = output_dir
        self.gerber_dir = self.output_dir / "gerber"
        self.drill_dir = self.output_dir / "drill"

    def export(self) -> None:
        try:
            self.output_dir.mkdir()
        except FileExistsError:
            shutil.rmtree(self.output_dir)
            self.output_dir.mkdir()

        self._export_gerbers()
        self._export_drill_files()
        self._create_zipfile()

        # TODO: Export BOM
        # TODO: Export position files

        logger.info(f"Successfully exported {self.pcb} to {self.output_dir}")

    def _export_gerbers(self) -> None:
        logger.info(f"Exporting gerbers...")
        self.gerber_dir.mkdir()

        # Run the gerber export command
        # We don't know how many layers there are, so we just let it export all
        # layers to a temporary directory, and then afterwards we keep only the
        # layers we want.
        with TemporaryDirectory(
            dir=self.output_dir, prefix="gerber_tmp."
        ) as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            cmd = [
                self.kicad_cli,
                "pcb",
                "export",
                "gerbers",
                "--subtract-soldermask",
                "-o",
                tmpdir_str,
                str(self.pcb),
            ]
            subprocess.run(cmd, check=True)

            prefix = f"{self.pcb.stem}-"
            with os.scandir(tmpdir) as scan:
                for entry in scan:
                    name_parts = entry.name.rsplit(".", 1)
                    if len(name_parts) != 2:
                        raise Exception(
                            f"unexpected gerber output file: {entry.name}"
                        )
                    stem, ext = name_parts
                    if not entry.name.startswith(prefix):
                        raise Exception(
                            f"unexpected gerber output file: {entry.name}"
                        )
                    name = stem[len(prefix) :]
                    keep = self._should_keep_gerber(name, ext)
                    if keep:
                        (tmpdir / entry.name).rename(
                            self.gerber_dir / entry.name
                        )

    def _should_keep_gerber(self, name: str, ext: str) -> bool:
        include_extensions: Set[str] = {
            "gtl",  # Top copper layer
            "gto",  # Top silk layer
            "gtp",  # Top paste layer
            "gts",  # Top mask layer
            "gbl",  # Bottom copper layer
            "gbo",  # Bottom silk layer
            "gbp",  # Bottom paste layer
            "gbs",  # Bottom mask layer
        }
        exclude_extensions: Set[str] = {
            "gta",  # Top Adhesive
            "gba",  # Bottom Adhesive
            "gbrjob",  # Job file
        }

        if ext in include_extensions:
            return True
        if ext in exclude_extensions:
            return False

        def is_int(value: str) -> bool:
            try:
                int(value)
                return True
            except ValueError:
                return False

        # Inner copper layers: # g1, g2, g3, ...
        if ext.startswith("g") and is_int(ext[1:]):
            return True
        # Mechanical layers (e.g., edge cuts): # gm1, gm2, ...
        if ext.startswith("gm") and is_int(ext[2:]):
            return True

        # In general we don't need other layers
        # Most other layers just end in "gbr"
        # The other layers are typically User_N, User_EcoN, F_Fab, B_Fab,
        # F_Courtyard, B_Courtyard
        return False

    def _export_drill_files(self) -> None:
        logger.info(f"Exporting drill files...")
        self.drill_dir.mkdir()

        # Note: JLCPCB also recommends the older (G85) method of emitting oval
        # holes, rather than Kicad's newer "recommended" way of routing with a
        # G00 command.
        #
        # kicad-cli 7.0 does not currently have a way to control this setting,
        # but fortunately it defaults to the behavior we want.
        #
        # https://gitlab.com/kicad/code/kicad/-/merge_requests/1697
        # is a merge request to add a --excellon-oval-format option
        # to control this behavior.
        cmd = [
            self.kicad_cli,
            "pcb",
            "export",
            "drill",
            "--format",
            "excellon",
            "--drill-origin",
            "absolute",
            "--excellon-separate-th",
            "--excellon-units",
            "mm",
            "--excellon-zeros-format",
            "decimal",
            "--generate-map",
            "--map-format",
            "gerberx2",
            "-o",
            # kicad-cli 7.0 requires that the output path ends in a slash.
            # https://gitlab.com/kicad/code/kicad/-/issues/14438
            f"{self.drill_dir}/",
            str(self.pcb),
        ]
        subprocess.run(cmd, check=True)

    def _create_zipfile(self) -> None:
        logger.info(f"Zipping gerber and drill files...")
        zip_path = self.output_dir / f"{self.pcb.stem}.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for path in (self.gerber_dir, self.drill_dir):
                with os.scandir(path) as scan:
                    for entry in scan:
                        entry_path = path / entry.name
                        zf.write(entry_path, entry.name)


def main() -> None:
    ap = argparse.ArgumentParser()
    args = ap.parse_args()

    log_format = "%(asctime)s: %(message)s"
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO, format=log_format
    )

    curdir = Path(".")
    pcb = curdir / "v2_controller/v2_controller.kicad_pcb"
    output_dir = curdir / "production"

    exporter = Exporter(pcb, output_dir)
    exporter.export()


if __name__ == "__main__":
    main()
