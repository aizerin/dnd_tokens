#!/usr/bin/env python3
"""Create a centered native PrusaSlicer 3 project for CORE One INDX 8T."""

from __future__ import annotations

import argparse
import json
import math
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
ET.register_namespace("", CORE)
NS = {"m": CORE}

BED_WIDTH = 248.0
BED_DEPTH = 205.0
TOKEN_DIAMETER = 25.0
PITCH = 30.0


def centered_positions(count: int) -> list[tuple[float, float]]:
    """Return a compact grid of token centers centered on the INDX bed."""
    candidates: list[tuple[float, int, int]] = []
    for columns in range(1, 9):
        rows = math.ceil(count / columns)
        width = TOKEN_DIAMETER + PITCH * (columns - 1)
        height = TOKEN_DIAMETER + PITCH * (rows - 1)
        if width <= BED_WIDTH and height <= BED_DEPTH:
            # Prefer a grid whose footprint has roughly the same aspect as the bed.
            score = abs(width / height - BED_WIDTH / BED_DEPTH) + 0.01 * (columns * rows - count)
            candidates.append((score, columns, rows))
    if not candidates:
        raise ValueError(f"Cannot fit {count} 25 mm tokens on the INDX bed")
    _, columns, rows = min(candidates)

    actual_last_row = count - columns * (rows - 1)
    y0 = BED_DEPTH / 2 - PITCH * (rows - 1) / 2
    positions: list[tuple[float, float]] = []
    for index in range(count):
        row = index // columns
        items_in_row = columns if row < rows - 1 else actual_last_row
        x0 = BED_WIDTH / 2 - PITCH * (items_in_row - 1) / 2
        positions.append((x0 + PITCH * (index % columns), y0 + PITCH * row))
    return positions


def transform_model(model_data: bytes, count: int) -> bytes:
    root = ET.fromstring(model_data)
    items = root.findall(".//m:build/m:item", NS)
    if len(items) != count:
        raise ValueError(f"Model has {len(items)} build items, project has {count} objects")
    for item, (x, y) in zip(items, centered_positions(count)):
        item.set("transform", f"1 0 0 0 1 0 0 0 1 {x:g} {y:g} 0")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build(source: Path, output: Path, template: Path, base_tool: int = 2) -> None:
    with ZipFile(source) as source_zip, ZipFile(template) as template_zip:
        project = json.loads(source_zip.read("Metadata/PrusaSlicer3_project.json"))
        template_project = json.loads(template_zip.read("Metadata/PrusaSlicer3_project.json"))
        template_containers = template_project.get("config_containers", [])
        if len(template_containers) != 1:
            raise ValueError("The template must contain one printer configuration")
        hardware = template_containers[0]["preset"]["hw_config"]
        if hardware.get("legacy_printer_model") != "COREONE_INDX8T" or hardware.get("tool_count") != 8:
            raise ValueError("The template is not a native CORE One INDX 8T project")
        objects = project.get("objects", [])
        if not objects:
            raise ValueError(f"No objects in {source}")
        for obj in objects:
            extruders = [v.get("volume_settings", {}).get("extruder") for v in obj.get("volumes", [])]
            if extruders not in ([4, 1], [2, 1]):
                raise ValueError(f"Unexpected tools {extruders} in object {obj.get('id')}")
            obj["volumes"][0]["volume_settings"]["extruder"] = base_tool
            obj["volumes"][1]["volume_settings"]["extruder"] = 1

        project["project"] = {
            "id": str(uuid.uuid4()),
            "version": template_project.get("project", {}).get("version", 1),
        }
        project["config_containers"] = template_containers
        model = transform_model(source_zip.read("3D/3dmodel.model"), len(objects))

        replacements = {
            "3D/3dmodel.model": model,
            "Metadata/PrusaSlicer3_project.json": (json.dumps(project, indent=2) + "\n").encode(),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output, "w", ZIP_DEFLATED) as result:
            for info in source_zip.infolist():
                result.writestr(info.filename, replacements.get(info.filename, source_zip.read(info.filename)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--base-tool", type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.base_tool <= 8:
        parser.error("--base-tool must be between 1 and 8")
    build(args.source.resolve(), args.output.resolve(), args.template.resolve(), args.base_tool)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
