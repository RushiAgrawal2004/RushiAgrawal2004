"""Convert a prepped grayscale photo into a self-typing monochrome ASCII SVG.

Downsamples the image to a character grid, maps brightness to a density
ramp, and wraps each row in a clip-path wipe (left-to-right, staggered top
to bottom) with a small block cursor riding the wipe edge. Prints once and
freezes -- no looping.

Usage: python scripts/make_ascii_svg.py [source-prepped.png] [out.svg]
"""
import sys

from PIL import Image

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#        ^ leading space clears the background to nothing

COLS = 100
ROWS = 53
CHAR_W = 7.2
CHAR_H = 14
FONT_SIZE = 13
FILL_COLOR = "#c9d1d9"          # single light-gray, monochrome on purpose
ROW_WIPE_DUR = 0.45              # seconds per row wipe
ROW_STAGGER = 0.045              # seconds between each row starting


def brightness_to_char(v: float) -> str:
    idx = int((1 - v / 255) * (len(RAMP) - 1))
    idx = max(0, min(len(RAMP) - 1, idx))
    return RAMP[idx]


def image_to_rows(path: str) -> list[str]:
    img = Image.open(path).convert("L").resize((COLS, ROWS), Image.LANCZOS)
    pixels = img.load()
    rows = []
    for y in range(ROWS):
        row = "".join(brightness_to_char(pixels[x, y]) for x in range(COLS))
        rows.append(row)
    return rows


def build_svg(rows: list[str]) -> str:
    width = COLS * CHAR_W
    height = ROWS * CHAR_H
    left_pad = 6

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">',
        "<style>"
        "text{font-family:SFMono-Regular,Consolas,Menlo,monospace;"
        f"font-size:{FONT_SIZE}px;fill:{FILL_COLOR};white-space:pre;}}"
        "</style>",
        f'<rect width="100%" height="100%" fill="none"/>',
        "<defs>",
    ]

    for i in range(ROWS):
        y_top = i * CHAR_H
        parts.append(
            f'<clipPath id="rowClip{i}"><rect x="0" y="{y_top}" width="0" '
            f'height="{CHAR_H}"><animate attributeName="width" from="0" '
            f'to="{width:.0f}" dur="{ROW_WIPE_DUR}s" '
            f'begin="{i * ROW_STAGGER:.3f}s" fill="freeze"/></rect></clipPath>'
        )
    parts.append("</defs>")

    for i, row in enumerate(rows):
        y_top = i * CHAR_H
        y_text = y_top + CHAR_H - 3
        begin = i * ROW_STAGGER
        parts.append(f'<g clip-path="url(#rowClip{i})">')
        parts.append(
            f'<text x="{left_pad}" y="{y_text:.1f}" xml:space="preserve">'
            f'{row}</text>'
        )
        parts.append(
            f'<rect x="0" y="{y_top}" width="{CHAR_W:.1f}" height="{CHAR_H}" '
            f'fill="{FILL_COLOR}">'
            f'<animate attributeName="x" from="0" to="{width:.0f}" '
            f'dur="{ROW_WIPE_DUR}s" begin="{begin:.3f}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="1;1;0" '
            f'keyTimes="0;0.9;1" dur="{ROW_WIPE_DUR}s" begin="{begin:.3f}s" '
            f'fill="freeze"/>'
            f'</rect>'
        )
        parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "avi-ascii.svg"
    rows = image_to_rows(src)
    svg = build_svg(rows)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out}")
