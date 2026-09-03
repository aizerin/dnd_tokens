#!/usr/bin/env python3
"""Render FDM-friendly fantasy numeral style options for review."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/Users/lukas/dev/projects/dnd-tokens")
OUTPUT = ROOT / "initiative-markers" / "previews" / "initiative-font-options.png"
NUMBERS = ("1", "6", "10", "14", "20")
STYLES = (
    ("A — Luminari", "/System/Library/Fonts/Supplemental/Luminari.ttf", 0),
    ("B — Copperplate Bold", "/System/Library/Fonts/Supplemental/Copperplate.ttc", 2),
    ("C — Hoefler Black", "/System/Library/Fonts/Supplemental/Hoefler Text.ttc", 1),
    ("D — Herculanum", "/System/Library/Fonts/Supplemental/Herculanum.ttf", 0),
)

INK = (24, 25, 27)
ORANGE = (244, 102, 55)
PAPER = (232, 229, 222)
TOKEN = 190
ART_MAX = 132


def fit_font(path: str, index: int, text: str) -> ImageFont.FreeTypeFont:
    low, high = 12, 220
    probe = Image.new("L", (TOKEN, TOKEN), 0)
    draw = ImageDraw.Draw(probe)
    while low < high:
        size = (low + high + 1) // 2
        font = ImageFont.truetype(path, size, index=index)
        box = draw.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= ART_MAX and box[3] - box[1] <= ART_MAX:
            low = size
        else:
            high = size - 1
    return ImageFont.truetype(path, low, index=index)


def token(text: str, path: str, index: int) -> Image.Image:
    image = Image.new("RGBA", (TOKEN, TOKEN), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, TOKEN - 1, TOKEN - 1), fill=INK)
    draw.ellipse((11, 11, TOKEN - 12, TOKEN - 12), fill=ORANGE)
    font = fit_font(path, index, text)
    box = draw.textbbox((0, 0), text, font=font)
    width, height = box[2] - box[0], box[3] - box[1]
    x = (TOKEN - width) / 2 - box[0]
    y = (TOKEN - height) / 2 - box[1]
    draw.text((x, y), text, font=font, fill=INK)
    return image


def main() -> None:
    margin, row_gap, col_gap = 28, 34, 18
    label_w = 265
    width = margin * 2 + label_w + len(NUMBERS) * TOKEN + (len(NUMBERS) - 1) * col_gap
    height = 88 + len(STYLES) * (TOKEN + row_gap)
    canvas = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
    label_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 25)
    draw.text((margin, 24), "INITIATIVE MARKERS — FANTASY NUMERAL OPTIONS", font=title_font, fill=INK)
    for row, (label, path, index) in enumerate(STYLES):
        y = 82 + row * (TOKEN + row_gap)
        draw.text((margin, y + 76), label, font=label_font, fill=INK)
        for col, number in enumerate(NUMBERS):
            x = margin + label_w + col * (TOKEN + col_gap)
            piece = token(number, path, index)
            canvas.paste(piece, (x, y), piece)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
