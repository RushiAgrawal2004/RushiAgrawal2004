"""Convert a prepped grayscale photo into a self-typing monochrome ASCII SVG.

Downsamples the image to a character grid, maps brightness to a density
ramp, and wraps each row in a clip-path wipe (left-to-right, staggered top
to bottom) with a small block cursor riding the wipe edge.

Animation notes -- these matter for GitHub:
  * SMIL (<animate>) is used rather than CSS keyframes. Raw SVGs are served
    under `Content-Security-Policy: default-src 'none'; sandbox`, and SMIL
    is the most reliable thing to survive that in an <img> context.
  * The cycle LOOPS. A play-once-then-freeze animation finishes before the
    image has even decoded, so a visitor only ever sees the frozen frame.
  * The background is opaque, not transparent -- light-gray glyphs on
    GitHub's light theme would otherwise be invisible.

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
PAD = 16

FILL_COLOR = "#c9d1d9"          # single light-gray, monochrome on purpose
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
CURSOR_COLOR = "#39d353"

ROW_WIPE_DUR = 0.45              # seconds per row wipe
ROW_STAGGER = 0.045              # seconds between each row starting
HOLD = 3.0                       # seconds the finished portrait rests


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
    content_w = COLS * CHAR_W
    content_h = ROWS * CHAR_H
    width = content_w + PAD * 2
    height = content_h + PAD * 2
    x_end = PAD + content_w

    # One full cycle: last row finishes, portrait holds, then resets.
    cycle = ROWS * ROW_STAGGER + ROW_WIPE_DUR + HOLD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">',
        "<style>"
        "text{font-family:SFMono-Regular,Consolas,Menlo,monospace;"
        f"font-size:{FONT_SIZE}px;fill:{FILL_COLOR};white-space:pre;}}"
        "</style>",
        f'<rect x="0.5" y="0.5" width="{width - 1:.0f}" '
        f'height="{height - 1:.0f}" rx="8" fill="{BG_COLOR}" '
        f'stroke="{BORDER_COLOR}"/>',
        "<defs>",
    ]

    for i in range(ROWS):
        y_top = PAD + i * CHAR_H
        t0 = (i * ROW_STAGGER) / cycle
        t1 = (i * ROW_STAGGER + ROW_WIPE_DUR) / cycle
        parts.append(
            f'<clipPath id="rowClip{i}">'
            f'<rect x="{PAD}" y="{y_top:.0f}" width="0" height="{CHAR_H}">'
            f'<animate attributeName="width" '
            f'values="0;0;{content_w:.0f};{content_w:.0f};0" '
            f'keyTimes="0;{t0:.4f};{t1:.4f};0.97;1" '
            f'dur="{cycle:.2f}s" repeatCount="indefinite"/>'
            f"</rect></clipPath>"
        )
    parts.append("</defs>")

    for i, row in enumerate(rows):
        y_top = PAD + i * CHAR_H
        y_text = y_top + CHAR_H - 3
        t0 = (i * ROW_STAGGER) / cycle
        t1 = (i * ROW_STAGGER + ROW_WIPE_DUR) / cycle
        t1b = t1 + 0.006
        keytimes = f"0;{t0:.4f};{t1:.4f};{t1b:.4f};1"

        parts.append(f'<g clip-path="url(#rowClip{i})">')
        parts.append(
            f'<text x="{PAD}" y="{y_text:.1f}" xml:space="preserve">'
            f"{row}</text>"
        )
        parts.append("</g>")

        # Block cursor rides the wipe edge, hidden outside its own row's pass.
        parts.append(
            f'<rect y="{y_top:.0f}" width="{CHAR_W:.1f}" height="{CHAR_H}" '
            f'fill="{CURSOR_COLOR}" opacity="0">'
            f'<animate attributeName="x" '
            f'values="{PAD};{PAD};{x_end:.0f};{x_end:.0f};{PAD}" '
            f'keyTimes="{keytimes}" dur="{cycle:.2f}s" '
            f'repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;0;0" '
            f'keyTimes="{keytimes}" dur="{cycle:.2f}s" '
            f'repeatCount="indefinite"/>'
            f"</rect>"
        )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "avi-ascii.svg"
    rows = image_to_rows(src)
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_svg(rows))
    print(f"wrote {out}")
