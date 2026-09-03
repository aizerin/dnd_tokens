#!/usr/bin/env python3
"""Build and validate one four-token MMU category from its manifest and PNGs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from make_prusaslicer3_8t import centered_positions


PYTHON = Path("/Users/lukas/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3")
VECTORIZER = Path("/Users/lukas/Documents/Codex/2026-07-19/referenced-chatgpt-conversation-this-is-untrusted/outputs/slavic-token-collection-31/pipeline/vectorize_token.py")
SCAD = Path("/Users/lukas/Documents/Codex/2026-07-19/referenced-chatgpt-conversation-this-is-untrusted/outputs/slavic-token-collection-31/pipeline/token_mmu.scad")
BUILDER = Path("/Users/lukas/Documents/Codex/2026-07-19/referenced-chatgpt-conversation-this-is-untrusted/outputs/slavic-token-collection-31/pipeline/build_collection_3mf.py")
RENDERER = Path("/Users/lukas/dev/projects/dnd-tokens/tools/render_category_preview.py")
OPENSCAD = Path("/opt/homebrew/bin/openscad")
SLICER = Path("/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer")
WORK_ROOT = Path("/Users/lukas/Documents/Codex/2026-07-19/referenced-chatgpt-conversation-this-is-untrusted/work/dnd-tokens")


def run(command: list[str], *, quiet: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.DEVNULL if quiet else subprocess.PIPE,
        stderr=subprocess.DEVNULL if quiet else subprocess.STDOUT,
    )


def slicer_info(path: Path) -> str:
    return run([str(SLICER), "--info", str(path)]).stdout


def render_stls(svg: Path, base: Path, inlay: Path) -> None:
    for part, output in (("base", base), ("inlay", inlay)):
        run(
            [
                str(OPENSCAD),
                "--export-format",
                "asciistl",
                "-o",
                str(output),
                "-D",
                f'icon_file="{svg}"',
                "-D",
                f'part="{part}"',
                str(SCAD),
            ],
            quiet=True,
        )


def trace(
    source: Path,
    svg: Path,
    title: str,
    size: int,
    threshold: int,
    simplify: float,
    art_mm: float,
) -> None:
    run(
        [
            str(PYTHON),
            str(VECTORIZER),
            str(source),
            str(svg),
            "--title",
            title,
            "--trace-size",
            str(size),
            "--threshold",
            str(threshold),
            "--sturdy-px",
            "0",
            "--min-island-px",
            "1",
            "--min-hole-px",
            "0",
            "--simplify",
            str(simplify),
            "--art-mm",
            str(art_mm),
            "--canvas-mm",
            "20.0",
        ],
        quiet=True,
    )


def build_token(
    source: Path,
    svg: Path,
    base: Path,
    inlay: Path,
    title: str,
    search: Path,
    art_mm: float,
) -> tuple[int, int, float]:
    candidates = [(512, 150, 0.25)]
    candidates.extend(
        (size, threshold, simplify)
        for size in (256, 320, 384, 448, 512, 640, 768, 896, 1024)
        for threshold in (100, 115, 130, 145, 160, 175, 190, 205)
        for simplify in (0.10, 0.20, 0.35, 0.50, 0.75, 1.00)
        if (size, threshold, simplify) != (512, 150, 0.25)
    )
    for size, threshold, simplify in candidates:
        trial_svg = search / f"{source.stem}-{size}-{threshold}-{simplify:.2f}.svg"
        trial_base = search / f"{source.stem}-base.stl"
        trial_inlay = search / f"{source.stem}-inlay.stl"
        trace(source, trial_svg, title, size, threshold, simplify, art_mm)
        render_stls(trial_svg, trial_base, trial_inlay)
        base_info = slicer_info(trial_base)
        inlay_info = slicer_info(trial_inlay)
        if "manifold = yes" in base_info and "manifold = yes" in inlay_info:
            svg.write_bytes(trial_svg.read_bytes())
            base.write_bytes(trial_base.read_bytes())
            inlay.write_bytes(trial_inlay.read_bytes())
            return size, threshold, simplify
    raise RuntimeError(f"No manifold trace found for {source.name}")


def validate_3mf(path: Path, expected_count: int) -> None:
    info = slicer_info(path)
    if "manifold = no" in info or info.count("manifold = yes") != expected_count:
        raise RuntimeError(f"3MF validation failed for {path}")
    for key, expected in (("size_x", "25.000000"), ("size_y", "25.000000"), ("size_z", "1.000000")):
        values = re.findall(rf"{key} = ([0-9.]+)", info)
        if values != [expected] * expected_count:
            raise RuntimeError(f"Unexpected {key} values in {path}: {values}")
    with ZipFile(path) as archive:
        model = archive.read("3D/3dmodel.model").decode()
        config = archive.read("Metadata/Slic3r_PE_model.config").decode()
    checks = {
        "objects": len(re.findall(r'<object id="', model)),
        "placements": len(re.findall(r'<item objectid="', model)),
        "extruder 2 volumes": len(re.findall(r'key="extruder" value="2"', config)),
        "extruder 1 volumes": len(re.findall(r'key="extruder" value="1"', config)),
    }
    if any(value != expected_count for value in checks.values()):
        raise RuntimeError(f"3MF metadata validation failed: {checks}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("category", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--art-mm", type=float, default=18.2)
    args = parser.parse_args()

    category = args.category.resolve()
    entries = json.loads((category / "manifest.json").read_text(encoding="utf-8"))
    if not entries:
        raise SystemExit("The manifest must contain at least one entry")

    svg_dir = category / "svg"
    three_mf_dir = category / "3mf"
    preview_dir = category / "previews"
    work = WORK_ROOT / category.name
    stl_dir = work / "stl"
    search = work / "search"
    for directory in (svg_dir, three_mf_dir, preview_dir, stl_dir, search):
        directory.mkdir(parents=True, exist_ok=True)

    settings: dict[str, dict[str, int | float]] = {}
    for entry in entries:
        slug, name = entry["slug"], entry["name"]
        size, threshold, simplify = build_token(
            category / "source" / f"{slug}.png",
            svg_dir / f"{slug}.svg",
            stl_dir / f"{slug}-base.stl",
            stl_dir / f"{slug}-inlay.stl",
            name,
            search,
            args.art_mm,
        )
        settings[slug] = {"trace_size": size, "threshold": threshold, "simplify": simplify}
        print(f"{name}: trace_size={size}, threshold={threshold}, simplify={simplify}")

    count = len(entries)
    output = three_mf_dir / f"{category.name}-{count}-tokens.3mf"
    command = [str(PYTHON), str(BUILDER), str(output), "--title", f"{args.title.title()} — 1 mm"]
    positions = centered_positions(count)
    for entry, (x, y) in zip(entries, positions):
        slug = entry["slug"]
        command.extend(
            [
                "--token",
                entry["name"],
                str(stl_dir / f"{slug}-base.stl"),
                str(stl_dir / f"{slug}-inlay.stl"),
                str(x),
                str(y),
            ]
        )
    run(command, quiet=True)
    validate_3mf(output, count)

    preview = preview_dir / f"{category.name}-{count}-tokens.png"
    preview_maximum = round(184 * args.art_mm / 18.2)
    run(
        [
            str(PYTHON),
            str(RENDERER),
            str(category),
            "--title",
            args.title.upper(),
            "--output",
            str(preview),
            "--maximum",
            str(preview_maximum),
        ],
        quiet=True,
    )
    (category / "trace-settings.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(output)
    print(preview)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        if error.stdout:
            print(error.stdout, file=sys.stderr)
        raise
