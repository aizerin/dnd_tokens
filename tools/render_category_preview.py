#!/usr/bin/env python3
"""Render a consistent labelled grid preview from a category manifest."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


TOKEN_SIZE = 230
BACKGROUND = (226, 223, 216)
ORANGE = (244, 102, 55)
INK = (24, 25, 27)
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def fitted_mask(path: Path, maximum: int = 184) -> Image.Image:
    with Image.open(path) as source:
        if "A" in source.getbands():
            rgba = source.convert("RGBA")
            white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            white.alpha_composite(rgba)
            gray = white.convert("L")
        else:
            gray = source.convert("L")
    mask = gray.point(lambda value: 255 if value < 150 else 0)
    bounds = mask.getbbox()
    if bounds is None:
        raise ValueError(f"No black artwork found in {path}")
    mask = mask.crop(bounds)
    scale = min(maximum / mask.width, maximum / mask.height)
    size = (max(1, round(mask.width * scale)), max(1, round(mask.height * scale)))
    return mask.resize(size, Image.Resampling.LANCZOS)


def token_image(source: Path, maximum: int = 184) -> Image.Image:
    token = Image.new("RGBA", (TOKEN_SIZE, TOKEN_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(token)
    draw.ellipse((0, 0, TOKEN_SIZE - 1, TOKEN_SIZE - 1), fill=INK)
    inset = 13
    draw.ellipse((inset, inset, TOKEN_SIZE - 1 - inset, TOKEN_SIZE - 1 - inset), fill=ORANGE)

    mask = fitted_mask(source, maximum)
    x = (TOKEN_SIZE - mask.width) // 2
    y = (TOKEN_SIZE - mask.height) // 2
    artwork = Image.new("RGBA", mask.size, INK + (255,))
    token.alpha_composite(Image.composite(artwork, Image.new("RGBA", mask.size), mask), (x, y))
    return token


def centered_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.FreeTypeFont) -> None:
    bounds = draw.textbbox((0, 0), text, font=font)
    width = bounds[2] - bounds[0]
    draw.text((xy[0] - width / 2, xy[1]), text, font=font, fill=INK)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("category", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--maximum", type=int, default=184)
    args = parser.parse_args()

    entries = json.loads((args.category / "manifest.json").read_text(encoding="utf-8"))
    columns = 2 if len(entries) <= 4 else 3
    rows = math.ceil(len(entries) / columns)

    width = columns * 280
    height = 74 + rows * 301

    canvas = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(FONT, 34)
    label_font = ImageFont.truetype(FONT, 22)
    centered_text(draw, (width // 2, 23), args.title, title_font)

    positions = [
        (25 + column * 280, 84 + row * 301)
        for row in range(rows)
        for column in range(columns)
    ]
    label_y = [334 + row * 301 for row in range(rows) for _ in range(columns)]
    for entry, (x, y), text_y in zip(entries, positions, label_y):
        token = token_image(args.category / "source" / f"{entry['slug']}.png", args.maximum)
        shadow = Image.new("RGBA", (TOKEN_SIZE + 24, TOKEN_SIZE + 24), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse((7, 7, TOKEN_SIZE + 6, TOKEN_SIZE + 6), fill=(0, 0, 0, 105))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        canvas.paste(shadow, (x + 1, y + 4), shadow)
        canvas.paste(token, (x, y), token)
        centered_text(draw, (x + TOKEN_SIZE // 2, text_y), entry["name"], label_font)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output, optimize=True)
    print(args.output)


if __name__ == "__main__":
    main()
