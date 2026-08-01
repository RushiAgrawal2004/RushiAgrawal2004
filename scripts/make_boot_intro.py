"""
Render a fake terminal login/boot sequence as a self-typing SVG: each line
wipes in left-to-right at a speed proportional to its own length (so it
reads like actual typing, not a uniform metronome), with a small cursor
block riding the wipe edge -- same trick as make_ascii_svg.py's row reveal,
just per-line instead of per-row.

Sits above the whoami panel in the README and hands off into it: the last
line ("./portrait.sh") is what the panel below is titled, so the two read
as one continuous session instead of two unrelated widgets. The cursor on
that last line keeps blinking forever once typing finishes -- an idle
shell prompt, waiting -- matching the rest of the profile's "small things
loop forever, the big reveal happens once" rule.

Usage: python scripts/make_boot_intro.py [out.svg]
"""
import html
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "intro.svg"

LINES = [
    "rushi@github:~$ ssh rushi@github.com",
    "Connecting to github.com (140.82.112.3)... done",
    "Authenticating with public key... accepted",
    "Last login: today from Pune, India",
    "",
    "Welcome to RUSHI-OS",
    "uptime: since 2004  ·  status: shipping",
    "",
    "rushi@github:~$ ./portrait.sh",
]

FONT_SIZE = 14
CELL_W = 8.3          # monospace advance width at this font-size
LINE_H = 22
PAD = 20
TITLEBAR_H = 30

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
DIM = "#5b6673"        # connection/auth chatter -- present but not shouting
CURSOR = "#c9d1d9"

CHAR_DUR = 0.045       # seconds per character typed
LINE_GAP = 0.28        # pause between one line finishing and the next starting
BLANK_GAP = 0.12       # blank lines pass through fast, they're just spacing

longest = max(len(line) for line in LINES)
art_w = longest * CELL_W
canvas_w = art_w + PAD * 2
canvas_h = TITLEBAR_H + PAD * 0.8 + len(LINES) * LINE_H + PAD * 0.6

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w:.0f}" '
    f'height="{canvas_h:.0f}" viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<defs><linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
    '</linearGradient></defs>',
    f'<rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" rx="12" fill="url(#ibg)"/>',
    f'<rect x="0.5" y="0.5" width="{canvas_w-1:.0f}" height="{canvas_h-1:.0f}" '
    f'rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w:.0f}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(f'<text x="{canvas_w/2:.0f}" y="{TITLEBAR_H/2 + 4:.0f}" fill="{TITLE_TEXT}" '
             f'font-size="12" text-anchor="middle">rushi@github: ~$ ssh connect</text>')

art_top = TITLEBAR_H + PAD * 0.8
t = 0.0
for i, line in enumerate(LINES):
    y_top = art_top + i * LINE_H
    y_text = y_top + LINE_H * 0.72
    is_last = i == len(LINES) - 1

    if not line:
        t += BLANK_GAP
        continue

    line_w = len(line) * CELL_W
    dur = max(len(line) * CHAR_DUR, 0.18)
    begin = t

    # connection/auth chatter reads dim + muted; the two shell prompts (this
    # box's own username line and the handoff line) read full-bright, since
    # those are "you", not the system talking back.
    color = INK if line.startswith("rushi@github") else DIM
    safe = html.escape(line)

    parts.append(
        f'<clipPath id="l{i}"><rect x="{PAD}" y="{y_top:.1f}" height="{LINE_H}" '
        f'width="0"><animate attributeName="width" from="0" to="{line_w:.1f}" '
        f'begin="{begin:.3f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
    )
    parts.append(
        f'<g clip-path="url(#l{i})"><text xml:space="preserve" x="{PAD}" '
        f'y="{y_text:.1f}" fill="{color}" font-size="{FONT_SIZE}">{safe}</text></g>'
    )

    cursor_x_end = PAD + line_w
    if is_last:
        # typing finishes, then the cursor blinks forever -- an idle shell
        # waiting for input, same "small loop" the portrait's status bar uses.
        parts.append(
            f'<rect x="{cursor_x_end:.1f}" y="{y_top+3:.1f}" width="{CELL_W*0.9:.1f}" '
            f'height="{LINE_H-6}" fill="{CURSOR}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{begin+dur:.3f}s"/>'
            f'<animate attributeName="opacity" values="1;1;0;0" '
            f'keyTimes="0;0.5;0.51;1" dur="1s" begin="{begin+dur:.3f}s" '
            f'repeatCount="indefinite"/></rect>'
        )
    else:
        # a cursor rides this line's own wipe edge, then hands off -- same
        # look as the ascii portrait's per-row cursor.
        parts.append(
            f'<rect y="{y_top+3:.1f}" width="{CELL_W*0.9:.1f}" height="{LINE_H-6}" '
            f'fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{cursor_x_end:.1f}" '
            f'begin="{begin:.3f}s" dur="{dur:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{begin:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{begin+dur:.3f}s"/></rect>'
        )

    t = begin + dur + LINE_GAP

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}  {len(svg)/1024:.1f} KB  {canvas_w:.0f}x{canvas_h:.0f}  total type time {t:.1f}s")
