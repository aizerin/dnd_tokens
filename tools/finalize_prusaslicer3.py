#!/usr/bin/env python3
"""Round-trip generated 3.0 projects through PrusaSlicer 3 itself."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile


ROOT = Path("/Users/lukas/dev/projects/dnd-tokens")
SLICER = Path("/Applications/PrusaSlicer-3.0.0-alpha11.app/Contents/MacOS/PrusaSlicer")


def expected_count(category: Path) -> int:
    data = json.loads((category / "manifest.json").read_text(encoding="utf-8"))
    return len(data if isinstance(data, list) else data.get("items", data.get("tokens", [])))


def validate(path: Path, count: int) -> None:
    with ZipFile(path) as archive:
        project = json.loads(archive.read("Metadata/PrusaSlicer3_project.json"))
    objects = project.get("objects", [])
    if len(objects) != count:
        raise RuntimeError(f"{path}: {len(objects)} objects, expected {count}")
    for obj in objects:
        volumes = obj.get("volumes", [])
        extruders = [volume.get("volume_settings", {}).get("extruder") for volume in volumes]
        if len(volumes) != 2 or extruders != [2, 1]:
            raise RuntimeError(f"{path}: invalid volume assignment in {obj.get('name', obj.get('id'))}")


def finalize(path: Path) -> str:
    category_name = re.sub(r"-\d+-tokens-prusaslicer-3\.0\.3mf$", "", path.name)
    category = ROOT / category_name
    count = expected_count(category)
    temporary = path.with_name(path.stem + ".native-tmp.3mf")
    result = subprocess.run(
        [
            str(SLICER),
            "--export-3mf",
            "--dont-arrange",
            "-o",
            str(temporary),
            str(path),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        raise RuntimeError(f"{path}: PrusaSlicer returned {result.returncode}\n{result.stdout}")
    validate(temporary, count)
    temporary.replace(path)
    return category_name


def main() -> None:
    paths = sorted((ROOT / "3mf-slicer-3.0").glob("*-tokens-prusaslicer-3.0.3mf"))
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {pool.submit(finalize, path): path for path in paths}
        for job in as_completed(jobs):
            try:
                print(job.result(), flush=True)
            except Exception as error:
                failures.append(str(error))
    print(f"FINALIZED={len(paths) - len(failures)}/{len(paths)}")
    for failure in failures:
        print(failure)
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
