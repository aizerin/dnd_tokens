#!/usr/bin/env python3
"""Convert a PrusaSlicer 2.9 multi-volume 3MF into the 3.0 project schema."""

from __future__ import annotations

import argparse
import copy
import json
from datetime import date
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET


CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
ET.register_namespace("", CORE)
NS = {"m": CORE}


def metadata_value(element: ET.Element, key: str, default: str = "") -> str:
    for item in element.findall("metadata"):
        if item.get("key") == key:
            return item.get("value", default)
    return default


def package_parts(template: Path) -> tuple[bytes, bytes, dict]:
    with ZipFile(template) as archive:
        content_types = archive.read("[Content_Types].xml")
        relationships = archive.read("_rels/.rels")
        project = json.loads(archive.read("Metadata/PrusaSlicer3_project.json"))
    return content_types, relationships, project


def convert(source: Path, output: Path, template: Path) -> None:
    content_types, relationships, project = package_parts(template)
    with ZipFile(source) as archive:
        model_root = ET.fromstring(archive.read("3D/3dmodel.model"))
        old_config = ET.fromstring(archive.read("Metadata/Slic3r_PE_model.config"))

    old_resources = model_root.find("m:resources", NS)
    old_build = model_root.find("m:build", NS)
    if old_resources is None or old_build is None:
        raise ValueError(f"Missing 3MF resources or build section in {source}")

    old_meshes = {
        int(obj.get("id")): obj
        for obj in old_resources.findall("m:object", NS)
        if obj.find("m:mesh", NS) is not None
    }
    old_items = {
        int(item.get("objectid")): item
        for item in old_build.findall("m:item", NS)
    }
    old_configs = {
        int(obj.get("id")): obj
        for obj in old_config.findall("object")
    }
    if set(old_configs) != set(old_meshes):
        raise ValueError(f"Object mismatch between model and configuration in {source}")

    new_root = ET.Element(
        f"{{{CORE}}}model",
        {"unit": "millimeter", "{http://www.w3.org/XML/1998/namespace}lang": "en-US"},
    )
    today = date.today().isoformat()
    ET.SubElement(new_root, f"{{{CORE}}}metadata", {"name": "CreationDate"}).text = today
    ET.SubElement(new_root, f"{{{CORE}}}metadata", {"name": "ModificationDate"}).text = today
    ET.SubElement(new_root, f"{{{CORE}}}metadata", {"name": "Application"}).text = (
        "Codex PrusaSlicer 3.0 project converter"
    )
    new_resources = ET.SubElement(new_root, f"{{{CORE}}}resources")
    new_build = ET.SubElement(new_root, f"{{{CORE}}}build")

    next_id = 1
    json_objects: list[dict] = []

    for old_id in sorted(old_meshes):
        old_object = old_meshes[old_id]
        old_object_config = old_configs[old_id]
        old_mesh = old_object.find("m:mesh", NS)
        vertices = old_mesh.find("m:vertices", NS)
        triangles = list(old_mesh.find("m:triangles", NS))
        volume_refs: list[tuple[int, str, int]] = []

        volumes = old_object_config.findall("volume")
        if len(volumes) != 2:
            raise ValueError(f"Expected two volumes for object {old_id} in {source}")

        for volume_index, volume in enumerate(volumes):
            first = int(volume.get("firstid"))
            last = int(volume.get("lastid"))
            if first < 0 or last >= len(triangles) or first > last:
                raise ValueError(f"Invalid triangle range {first}..{last} in {source}")

            mesh_id = next_id
            next_id += 1
            mesh_object = ET.SubElement(new_resources, f"{{{CORE}}}object", {"id": str(mesh_id)})
            mesh = ET.SubElement(mesh_object, f"{{{CORE}}}mesh")
            mesh.append(copy.deepcopy(vertices))
            split_triangles = ET.SubElement(mesh, f"{{{CORE}}}triangles")
            split_triangles.extend(copy.deepcopy(triangles[first : last + 1]))

            volume_id = next_id
            next_id += 1
            volume_name = metadata_value(volume, "name", f"Volume {volume_index + 1}")
            volume_object = ET.SubElement(
                new_resources,
                f"{{{CORE}}}object",
                {"id": str(volume_id), "name": volume_name},
            )
            components = ET.SubElement(volume_object, f"{{{CORE}}}components")
            ET.SubElement(components, f"{{{CORE}}}component", {"objectid": str(mesh_id)})
            extruder = int(metadata_value(volume, "extruder", "0"))
            volume_refs.append((volume_id, volume_name, extruder))

        top_id = next_id
        next_id += 1
        object_name = metadata_value(old_object_config, "name", f"Object {old_id}")
        top_object = ET.SubElement(
            new_resources,
            f"{{{CORE}}}object",
            {"id": str(top_id), "name": object_name},
        )
        top_components = ET.SubElement(top_object, f"{{{CORE}}}components")
        for volume_id, _, _ in volume_refs:
            ET.SubElement(top_components, f"{{{CORE}}}component", {"objectid": str(volume_id)})

        item_attrs = {"objectid": str(top_id)}
        old_item = old_items.get(old_id)
        if old_item is not None and old_item.get("transform"):
            item_attrs["transform"] = old_item.get("transform")
        ET.SubElement(new_build, f"{{{CORE}}}item", item_attrs)

        json_objects.append(
            {
                "id": top_id,
                "name": object_name,
                "volumes": [
                    {
                        "id": volume_id,
                        "name": volume_name,
                        "type": "ModelPart",
                        "source": {"objectIdx": -1, "volumeIdx": -1},
                        "volume_settings": {
                            "extruder": extruder,
                            "wipe_into_infill": False,
                        },
                    }
                    for volume_id, volume_name, extruder in volume_refs
                ],
                "object_settings": {
                    "extruder": 0,
                    "wipe_into_objects": False,
                },
            }
        )

    project["objects"] = json_objects
    project.setdefault("project", {})["version"] = 1
    model_bytes = ET.tostring(new_root, encoding="utf-8", xml_declaration=True)
    project_bytes = (json.dumps(project, indent=2, ensure_ascii=False) + "\n").encode()

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("3D/3dmodel.model", model_bytes)
        archive.writestr("Metadata/PrusaSlicer3_project.json", project_bytes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--template", type=Path, required=True)
    args = parser.parse_args()
    convert(args.source.resolve(), args.output.resolve(), args.template.resolve())
    print(args.output.resolve())


if __name__ == "__main__":
    main()
