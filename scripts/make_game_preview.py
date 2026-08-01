"""
Build game/preview.svg: the dino-game panel used as a clickable preview in
the README. Combines a real screenshot of the live game (background/
foreground pixels keyed to the profile's ink color, embedded as a base64
PNG) with a vector terminal frame (titlebar dots, border) drawn directly in
SVG, plus an animated "eternally loading" progress bar + rotating joke
status lines in the panel's blank space -- a bit for a game that's
literally about having no internet connection.

The loading bar and status lines LOOP forever (repeatCount=indefinite) on
purpose: it's a joke that the game never finishes loading, not a bug.

Usage: python scripts/make_game_preview.py <screenshot.png> [out.svg]
"""
import base64
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "dino-tight.png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "game/preview.svg"

PAD = 14
TITLEBAR_H = 32
RADIUS = 10
BG = "#0d1117"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
GREEN = "#39d353"
DIM = "#5b6673"

STATUS_LINES = [
    "downloading more RAM...",
    "searching for wifi... not found",
    "compiling excuses...",
    "asking ChatGPT for help...",
    "reticulating splines...",
    "still not connected. trying again.",
]
LINE_DUR = 1.8  # seconds each status line is shown


def make_ink_png(src_path: str) -> tuple[str, int, int]:
    shot = Image.open(src_path).convert("RGB")
    if shot.size[1] > 145:
        shot = shot.crop((0, 8, shot.size[0], 150))
    arr = np.array(shot).astype(np.float32)
    lum = arr.mean(axis=2)
    alpha = np.clip(255 - lum, 0, 255).astype(np.uint8)
    ink_rgb = (201, 209, 217)  # #c9d1d9
    rgb = np.zeros((*alpha.shape, 3), dtype=np.uint8)
    rgb[:, :] = ink_rgb
    rgba = np.dstack([rgb, alpha])
    img = Image.fromarray(rgba, mode="RGBA")

    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return b64, img.size[0], img.size[1]


def build_svg(b64: str, sw: int, sh: int) -> str:
    canvas_w = sw + PAD * 2
    bar_area_h = 56
    canvas_h = TITLEBAR_H + sh + bar_area_h + PAD

    total_loop = len(STATUS_LINES) * LINE_DUR
    bar_y = TITLEBAR_H + sh + 30
    bar_x = PAD
    bar_w = canvas_w - PAD * 2 - 46
    bar_h = 10

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" '
        f'height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="{RADIUS+2}" fill="{BG}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
    parts.append(
        f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" '
        f'font-size="13" text-anchor="middle">rushi@github: ~$ ./no-wifi.exe</text>'
    )

    parts.append(
        f'<image x="{PAD}" y="{TITLEBAR_H}" width="{sw}" height="{sh}" '
        f'href="data:image/png;base64,{b64}"/>'
    )

    # --- eternally-loading progress bar (loops forever, the joke is that
    # it never reaches 100 and stays) ---
    parts.append(
        f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="{bar_h/2}" '
        f'fill="none" stroke="{FRAME}"/>'
    )
    parts.append(
        f'<rect x="{bar_x}" y="{bar_y}" width="0" height="{bar_h}" rx="{bar_h/2}" fill="{GREEN}">'
        f'<animate attributeName="width" values="0;{bar_w*0.97:.1f};0" '
        f'keyTimes="0;0.92;1" dur="{total_loop:.2f}s" repeatCount="indefinite"/>'
        f"</rect>"
    )
    def visibility_animate(t0: float, t1: float) -> str:
        """Sharp on/off (no crossfade) between fractions t0 and t1 of the
        loop. Needs 6 keyframe points, not 4: duplicating a keyTime makes
        SMIL jump instantly instead of ramping, which is what keeps two
        rotating lines/labels from ever being partially visible at once."""
        keytimes = f"0;{t0:.4f};{t0:.4f};{t1:.4f};{t1:.4f};1"
        return (
            f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
            f'keyTimes="{keytimes}" dur="{total_loop:.2f}s" repeatCount="indefinite"/>'
        )

    # a handful of discrete percentage readouts, each shown while the bar is
    # roughly in that range -- SMIL can animate attributes, not text content,
    # so a ticking counter needs one <text> per value with opacity toggling.
    pct_x = bar_x + bar_w + 10
    pct_checkpoints = [(0.0, "0"), (0.35, "34"), (0.65, "61"), (0.92, "97")]
    for i, (t0, label) in enumerate(pct_checkpoints):
        t1 = pct_checkpoints[i + 1][0] if i + 1 < len(pct_checkpoints) else 0.94
        parts.append(
            f'<text x="{pct_x}" y="{bar_y+bar_h-1}" fill="{DIM}" font-size="11" opacity="0">'
            f'{visibility_animate(t0, t1)}{label}%</text>'
        )

    # --- rotating joke status lines under the bar ---
    status_y = bar_y + 26
    for i, line in enumerate(STATUS_LINES):
        t0 = i * LINE_DUR / total_loop
        t1 = (i + 1) * LINE_DUR / total_loop
        parts.append(
            f'<text x="{bar_x}" y="{status_y}" fill="{DIM}" font-size="12" opacity="0">'
            f'{visibility_animate(t0, t1)}{line}</text>'
        )

    parts.append(
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" '
        f'rx="{RADIUS+2}" fill="none" stroke="{FRAME}"/>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    b64, sw, sh = make_ink_png(SRC)
    svg = build_svg(b64, sw, sh)
    Path(OUT).write_text(svg, encoding="utf-8")
    print(f"wrote {OUT}  ({len(svg)/1024:.1f} KB)")
