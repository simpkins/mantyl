#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

"""
Command-line script to generate JLCPCB production files from a Kicad project.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import re
import shutil
import subprocess
import sys
import xml.dom.minidom
import yaml
import zipfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger("export")


@dataclass
class Component:
    ref: str
    value: str
    footprint: str
    properties: Dict[str, str]


class BOM:
    def __init__(self, components: List[Component]) -> None:
        self.components = components
        self.by_part: Dict[str, Component] = {}
        self.by_ref: Dict[str, Component] = {}

        # Build the dictionary by ref
        for comp in self.components:
            if not comp.ref:
                raise Exception("component present with no ref")
            if comp.ref in self.by_ref:
                raise Exception(
                    f"multiple components present with ref {comp.ref}"
                )
            self.by_ref[comp.ref] = comp

    def process_part_numbers(self) -> None:
        # Build the dictionary grouping components together by part number
        for component in self.components:
            part = component.properties.get("LCSC Part #")
            if not part:
                raise Exception(
                    f"LCSC Part number not specified for {comp.ref}"
                )
            comp_list = self.by_part.setdefault(part, [])
            comp_list.append(component)

        # Warn about components that share the same part number but different
        # values.  This likely indicates an incorrect part number if there are
        # capacitors/resistors/etc with mismatched values but the same part
        # number.
        #
        # We ignore this check for switches and headers that may use the value
        # simply as a label.
        for part, components in self.by_part.items():
            values = set([comp.value for comp in components])
            if len(values) == 1:
                continue

            # Ignore this warning for switches and headers, where the value
            # might be used simply as a label
            for comp in components:
                if not re.match("^(SW|J)[0-9]+$", comp.ref):
                    break
            else:
                # All components were switches or headers
                continue

            refs = ",".join(sorted(comp.ref for comp in components))
            logger.warning(
                f"mismatched component values: {refs} all "
                f"have the same part number ({part}), but different values:"
            )
            for comp in components:
                logger.warning(f"  {comp.ref}: {comp.value}")

    @classmethod
    def load(cls, kicad_cli: str, sch: Path) -> BOM:
        components = cls._read_bom(kicad_cli, sch)
        return cls(components)

    @classmethod
    def _read_bom(cls, kicad_cli: str, sch: Path) -> BOM:
        # Kicad 7.0 only has a "python-bom" export command.
        # Newer development versions also have a "bom" export that allows
        # exporting the BOM in a CSV format, with a custom list of fields.
        #
        # For now we use python-bom since it is available in stable released
        # versions of Kicad.
        with TemporaryDirectory(prefix="kicad_bom") as tmpdir:
            out_path = Path(tmpdir) / "kicad.bom"
            cmd = [
                kicad_cli,
                "sch",
                "export",
                "python-bom",
                "-o",
                str(out_path),
                str(sch),
            ]
            subprocess.run(cmd, check=True)
            return cls._parse_bom(out_path)

    @classmethod
    def _parse_bom(cls, path: Path) -> List[Component]:
        with path.open("rb") as f:
            doc = xml.dom.minidom.parse(f)

        for child in doc.childNodes:
            if child.nodeName == "export":
                export_node = child
                break
        else:
            raise Exception("unable to find export node in BOM")

        for child in export_node.childNodes:
            if child.nodeName == "components":
                components_node = child
                break
        else:
            raise Exception("unable to find components node in BOM")

        bom: List[Component] = []
        for child in components_node.childNodes:
            if child.nodeName != "comp":
                continue

            bom.append(cls._parse_component(child))

        return bom

    @classmethod
    def _parse_component(cls, node: xml.dom.minidom.Element) -> Component:
        props: Dict[str, str] = {}
        ref_attr = node.attributes.get("ref")
        assert ref_attr is not None, "BOM component present without a ref"

        value: str = ""
        footprint: str = ""

        for child in node.childNodes:
            if child.nodeName == "value":
                assert (
                    len(child.childNodes) == 1
                ), "component value has unexpected number of children"
                value = child.childNodes[0].data
            elif child.nodeName == "footprint":
                assert (
                    len(child.childNodes) == 1
                ), "component footprint has unexpected number of children"
                footprint = child.childNodes[0].data
            elif child.nodeName == "property":
                name_attr = child.attributes.get("name")
                value_attr = child.attributes.get("value")
                assert (
                    name_attr is not None
                ), "BOM component property present without a name"
                assert (
                    value_attr is not None
                ), "BOM component property present without a value"
                props[name_attr.value] = value_attr.value

        return Component(
            ref=ref_attr.value,
            value=value,
            footprint=footprint,
            properties=props,
        )


@dataclass
class JlcPcbFootprint:
    footprint: str
    rotation: float = 0.0  # In degrees
    center_x: float = 0.0
    center_y: float = 0.0

    def dump(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"footprint": self.footprint}
        if self.rotation != 0.0:
            data["rotation"] = self.rotation
        if (self.center_x, self.center_y) != (0.0, 0.0):
            data["center_x"] = self.center_x
            data["center_y"] = self.center_y

        return data

    @classmethod
    def load(
        self, path: Path, identifier: str, data: Dict[str, Any]
    ) -> JlcPcbFootprint:
        fp: Optional[str] = None
        rot = 0.0
        cx = 0.0
        cy = 0.0
        for name, value in data.items():
            if name == "footprint":
                fp = value
            elif name == "rotation":
                rot = float(value)
            elif name == "center_x":
                cx = float(value)
            elif name == "center_y":
                cy = float(value)
            else:
                logger.warning(
                    f"{path}: unexpected field in footprint mapping info for "
                    f"{identifier}: {name}"
                )

        if fp is None:
            raise Exception("missing JLCPCB footprint name")

        return JlcPcbFootprint(
            footprint=fp, rotation=rot, center_x=cx, center_y=cy
        )


@dataclass
class JlcPcbPart:
    part: str
    footprint: JlcPcbFootprint


@dataclass
class JlcPcbSymbolInfo:
    part: Optional[str]
    footprint: Optional[JlcPcbFootprint]

    def dump(self) -> Union[str, Dict[str, Any]]:
        if self.footprint is None:
            part = self.part
            if part is None:
                # This normally shouldn't happen.  We expect to have at least
                # some info present in each component entry.
                return {}
            return self.part

    @classmethod
    def load(
        self, path: Path, ref: str, data: Union[str, Dict[str, Any]]
    ) -> JlcPcbSymbolInfo:
        if isinstance(data, str):
            return JlcPcbSymbolInfo(part=data, footprint=None)

        part: Optional[str] = None
        footprint_info: Dict[str, Any] = {}
        for name, value in data.items():
            if name == "part":
                part = data.get("part", None)
            elif name in ("footprint", "rotation", "center_x", "center_y"):
                footprint_info[name] = value
            else:
                logger.warning(
                    f"{path}: unexpected field in mapping info for component "
                    f"{ref}: {name}"
                )

        if footprint_info:
            footprint = JlcPcbFootprint.load(path, ref, data)
            return JlcPcbSymbolInfo(part=part, footprint=footprint)
        else:
            return JlcPcbSymbolInfo(part=data, footprint=None)


class JlcPcbMapper:
    def __init__(self) -> None:
        self.by_ref: Dict[str, JlcPcbSymbolInfo] = {}
        self.by_footprint: Dict[str, JlcPcbFootprint] = {}

    def get_info(self, component: Component) -> JlcPcbPart:
        sym_info = self.by_ref.get(component.ref, None)

        part: Optional[str] = None
        if sym_info is not None:
            part = sym_info.part
        if part is None:
            part = component.properties.get("LCSC Part #")
        if not part:
            raise Exception(
                f"no LCSC part number specified for {component.ref}: "
                "specify one in the mapping file or in an 'LCSC Part #' "
                "field on the symbol"
            )

        if sym_info is not None and sym_info.footprint is not None:
            footprint = sym_info.footprint
        else:
            footprint = self.by_footprint.get(component.footprint, None)
            if footprint is None:
                footprint = self._default_footprint_info(component.footprint)
                # Update our by_footprint map so that if we dump our
                # information later in includes all mapping info that we used.
                self.by_footprint[component.footprint] = footprint

        return JlcPcbPart(part=part, footprint=footprint)

    def dump(self) -> Dict[str, Any]:
        footprints = {
            kicad_footprint: fp.dump()
            for kicad_footprint, fp in self.by_footprint.items()
        }
        data: Dict[str, Any] = {"footprints": footprints}
        if self.by_ref:
            # data["components"] = {ref: info.dump() for ref, info in self.by_ref.items()}
            comp_info: Dict[str, Any] = {}
            data["components"] = comp_info
            for ref, info in self.by_ref.items():
                comp_info[ref] = info.dump()

        return data

    @classmethod
    def load(cls, path: Path, data: Dict[str, Any]) -> JlcPcbMapper:
        mapper = cls()

        for name, value in data.items():
            if name == "footprints":
                for kicad_footprint, fp_data in value.items():
                    fp_info = JlcPcbFootprint.load(
                        path, kicad_footprint, fp_data
                    )
                    mapper.by_footprint[kicad_footprint] = fp_info
            elif name == "components":
                for ref, comp_data in value.items():
                    comp_info = JlcPcbSymbolInfo.load(path, ref, comp_data)
                    mapper.by_ref[ref] = comp_info
            else:
                logger.warning(
                    f"{path}: unexpected field in JLCPCB mapping file"
                )

        return mapper

    def _default_footprint_info(self, footprint: str) -> JlcPcbFootprint:
        name_parts = footprint.split(":", 1)
        library, name = name_parts
        return JlcPcbFootprint(name)


class Exporter:
    kicad_cli: str = "kicad-cli"

    def __init__(
        self,
        project: Path,
        mapping_file: Path,
        kicad_cli: Optional[str] = None,
    ) -> None:
        self.project_name = project.name
        self.pcb = project / f"{project.name}.kicad_pcb"
        self.sch = project / f"{project.name}.kicad_sch"
        self._bom: Optional[BOM] = None

        self.mapping_file = mapping_file
        self.mapper = self._load_mapper(mapping_file)

        if kicad_cli is not None:
            self.kicad_cli = kicad_cli

    def get_bom(self) -> BOM:
        bom = self._bom
        if bom is None:
            bom = BOM.load(self.kicad_cli, self.sch)
            self._bom = bom
        return bom

    def _load_mapper(self, path: Path) -> JlcPcbMapper:
        try:
            in_file = path.open("r")
        except FileNotFoundError:
            return JlcPcbMapper()

        with in_file:
            data = yaml.load(in_file, Loader=yaml.SafeLoader)
        return JlcPcbMapper.load(path, data)

    def save_mapping_file(self, output_path: Path) -> None:
        """
        Write a default mapping file to map KiCad components and footprints to
        JLCPCB part and footprint information.

        This helps initialize the file so it can be manually edited as desired
        afterwards.
        """
        bom = self.get_bom()

        by_footprint: Dict[str, List[Component]] = {}
        for comp in bom.components:
            # Call get_info() just so the mapper will keep track of all
            # footprints that were used in the BOM
            self.mapper.get_info(comp)

        data = self.mapper.dump()
        with output_path.open("w") as out_file:
            yaml.dump(data, stream=out_file)

    def export(self, output_dir: Path) -> None:
        self.get_bom().process_part_numbers()

        try:
            output_dir.mkdir()
        except FileExistsError:
            shutil.rmtree(output_dir)
            output_dir.mkdir()

        gerber_dir = output_dir / "gerber"
        drill_dir = output_dir / "drill"

        # Export the gerber and drill files
        self._export_gerbers(gerber_dir)
        self._export_drill_files(drill_dir)
        zip_path = output_dir / f"{self.project_name}.zip"
        self._create_zipfile(zip_path, gerber_dir, drill_dir)

        # Export the BOM and CPL files
        self._export_bom(output_dir)
        self._export_pos(output_dir)

        logger.info(f"Successfully exported {self.pcb} to {output_dir}")

    def _export_gerbers(self, gerber_dir: Path) -> None:
        logger.info(f"Exporting gerbers...")
        gerber_dir.mkdir()

        # Run the gerber export command
        # We don't know how many layers there are, so we just let it export all
        # layers to a temporary directory, and then afterwards we keep only the
        # layers we want.
        with TemporaryDirectory(dir=gerber_dir) as tmpdir_str:
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
                        (tmpdir / entry.name).rename(gerber_dir / entry.name)

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

    def _export_drill_files(self, drill_dir: Path) -> None:
        logger.info(f"Exporting drill files...")
        drill_dir.mkdir()

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
            f"{drill_dir}/",
            str(self.pcb),
        ]
        subprocess.run(cmd, check=True)

    def _create_zipfile(
        self, zip_path: Path, gerber_dir: Path, drill_dir: Path
    ) -> None:
        logger.info(f"Zipping gerber and drill files...")
        with zipfile.ZipFile(zip_path, "x", zipfile.ZIP_DEFLATED) as zf:
            for path in (gerber_dir, drill_dir):
                with os.scandir(path) as scan:
                    for entry in scan:
                        entry_path = path / entry.name
                        zf.write(entry_path, entry.name)

    def _export_bom(self, output_dir: Path) -> None:
        path = output_dir / f"{self.project_name}.bom"
        bom = self.get_bom()

        dialect = "excel"
        header = ["Comment", "Designator", "Footprint", "LCSC"]
        with path.open("w", newline="") as out_file:
            writer = csv.writer(out_file, dialect=dialect)
            writer.writerow(header)

            for part, components in sorted(bom.by_part.items()):
                footprint = self._bom_jlc_footprint(components[0])
                comment = components[0].value
                refs = ",".join(sorted(comp.ref for comp in components))
                row = [comment, refs, footprint, part]
                writer.writerow(row)

    def _bom_jlc_footprint(self, component: Component) -> None:
        # The Kicad footprint name is in the format LIBRARY:FOOTPRINT
        parts = component.footprint.split(":", 1)
        return parts[-1]

    def _bom_jlc_comment(self, component: Component) -> None:
        return component.value

    def _export_pos(self, output_dir: Path) -> None:
        kicad_pos = output_dir / f"kicad.pos"
        cmd = [
            self.kicad_cli,
            "pcb",
            "export",
            "pos",
            "--format",
            "csv",
            "--units",
            "mm",
            "-o",
            str(kicad_pos),
            str(self.pcb),
        ]
        subprocess.run(cmd, check=True)

        try:
            self._process_kicad_pos(kicad_pos, output_dir)
        finally:
            kicad_pos.unlink()

    def _process_kicad_pos(self, kicad_pos: Path, output_dir: Path) -> None:
        rows_by_side: Dict[str, List[List[str]]] = {}
        kicad_header = ["Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side"]
        with kicad_pos.open("r", newline="") as in_file:
            seen_header = False
            for row in csv.reader(in_file):
                if not seen_header:
                    seen_header = True
                    assert (
                        row == kicad_header
                    ), "Unexpected position CSV format"
                    continue

                ref, value, footprint, pos_x, pos_y, rot, side = row
                side_rows = rows_by_side.setdefault(side, [])
                side_rows.append(row)

        jlcpcb_header = [
            "Designator",
            "Val",
            "Package",
            "Mid X",
            "Mid Y",
            "Rotation",
            "Layer",
        ]
        for side, rows in rows_by_side.items():
            jlcpcb_cpl = output_dir / f"{side}.cpl"
            with jlcpcb_cpl.open("w", newline="") as out_file:
                writer = csv.writer(out_file, dialect="unix")
                writer.writerow(jlcpcb_header)

                for row in rows:
                    jlc_row = self._adjust_pos_row(row)
                    writer.writerow(jlc_row)

    def _adjust_pos_row(self, row: List[str]) -> List[str]:
        ref, value, footprint, pos_x, pos_y, rot, side = row

        # TODO
        return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--kicad-cli",
        metavar="PATH",
        help="The path to the kicad-cli program.",
    )
    ap.add_argument(
        "--mapping-file",
        metavar="PATH",
        help="The path to the file with information on how to map KiCad "
        "components and footprints to JLCPCB parts and footprints.",
    )
    ap.add_argument(
        "--save-mapping-file",
        action="store_true",
        help="Save the JLCPCB part info mapping file.",
    )
    ap.add_argument(
        "project", metavar="PROJECT", help="The path to the project directory."
    )
    args = ap.parse_args()

    log_format = "%(asctime)s: %(message)s"
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO, format=log_format
    )

    project_dir = Path(args.project)
    if args.mapping_file is not None:
        mapping_file = Path(args.mapping_file)
    else:
        mapping_file = project_dir / f"{project_dir.name}.jlcpcb.yaml"

    exporter = Exporter(project_dir, mapping_file, kicad_cli=args.kicad_cli)
    if False:
        output_dir = project_dir / "production"
        exporter.export(output_dir)

    if args.save_mapping_file:
        exporter.save_mapping_file(mapping_file)
        logger.info(f"Saved JLCPCB mapping info at {mapping_file}")


if __name__ == "__main__":
    main()
