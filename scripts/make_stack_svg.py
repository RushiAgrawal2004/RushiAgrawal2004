"""
Render the tech-stack panel as a terminal window full of chips: one row per
category, each chip fading + rising into place left-to-right, row after row,
then freezing. Same rule as the rest of the profile -- the big reveal happens
once, only the cursor keeps looping.

Deliberately not shields.io badges: every other panel here is a hand-rolled
dark terminal (intro.svg, avi-ascii.svg), and third-party badge PNGs would
read as a different website pasted into this one. Chips are drawn with the
same frame/dot chrome as make_boot_intro.py so the two stack visually.

Chip widths are computed from character count against a fixed monospace
advance (CELL), which is why the font stack must stay monospace -- swap in a
proportional font and every chip mis-sizes.

Usage: python scripts/make_stack_svg.py [out.svg]
"""
import html
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "stack.svg"

# (label, accent, [chips]) -- one accent per row so each category reads as a
# group without needing a legend.
ROWS = [
    ("languages", "#39d353", ["TypeScript", "Python", "JavaScript", "SQL", "Bash"]),
    ("frontend",  "#22d3ee", ["Next.js", "React", "Tailwind", "shadcn/ui", "Radix UI", "Framer Motion"]),
    ("backend",   "#a371f7", ["Node.js", "Hono", "Express", "FastAPI", "Drizzle ORM", "PostgreSQL"]),
    ("ai · agents", "#f2cc60", ["MCP", "Claude API", "OpenAI", "RAG", "llama.cpp", "evals"]),
    ("cloud · ops", "#ff7b72", ["AWS", "Docker", "NGINX", "GitHub Actions", "Vercel", "Supabase"]),
]

FOOTER = "focus: infrastructure for coding agents — memory, observability, local inference"

CANVAS_W = 860
PAD = 24
TITLEBAR_H = 34
LABEL_W = 152
CHIP_H = 27
CHIP_GAP = 9
CHIP_PAD_X = 11
ROW_GAP = 14
WRAP_GAP = 7

FONT = 12.5
CELL = 7.52            # monospace advance at FONT -- see module docstring
LABEL_FONT = 12.5

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
LABEL_INK = "#7d8590"
FOOTER_INK = "#8b949e"
RULE = "#21262d"

ROW_T = 0.30           # stagger between category rows
CHIP_T = 0.055         # stagger between chips inside a row
ROW_LEAD = 0.10        # label lands just before its own chips


def chip_w(text):
    return len(text) * CELL + CHIP_PAD_X * 2


def wrap(chips, avail):
    """Greedy-fill chips into lines; long rows spill instead of overflowing."""
    lines, line, used = [], [], 0.0
    for c in chips:
        w = chip_w(c)
        if line and used + CHIP_GAP + w > avail:
            lines.append(line)
            line, used = [c], w
        else:
            used += (CHIP_GAP + w) if line else w
            line.append(c)
    if line:
        lines.append(line)
    return lines


chips_x = PAD + LABEL_W
avail = CANVAS_W - chips_x - PAD

laid = [(label, accent, wrap(chips, avail)) for label, accent, chips in ROWS]

body_top = TITLEBAR_H + PAD * 0.9
y = body_top
row_geometry = []
for label, accent, lines in laid:
    h = len(lines) * CHIP_H + (len(lines) - 1) * WRAP_GAP
    row_geometry.append(y)
    y += h + ROW_GAP

rule_y = y + PAD * 0.25
canvas_h = rule_y + PAD * 1.5

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" '
    f'height="{canvas_h:.0f}" viewBox="0 0 {CANVAS_W} {canvas_h:.0f}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<defs><linearGradient id="sbg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
    '</linearGradient></defs>',
    '<style>'
    '.chip{opacity:0;animation:rise .42s cubic-bezier(.2,.8,.3,1) both}'
    '.lab{opacity:0;animation:fade .45s ease-out both}'
    '.cur{animation:blink 1s step-end infinite both}'
    '@keyframes rise{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}'
    '@keyframes fade{from{opacity:0}to{opacity:1}}'
    '@keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}'
    '@media (prefers-reduced-motion: reduce){'
    '.chip,.lab{opacity:1!important;animation:none!important}'
    '.cur{animation:none!important}}'
    '</style>',
    f'<rect width="{CANVAS_W}" height="{canvas_h:.0f}" rx="12" fill="url(#sbg)"/>',
    f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{canvas_h-1:.0f}" '
    f'rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(
    f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4:.0f}" fill="{TITLE_TEXT}" '
    f'font-size="12" text-anchor="middle">stack.txt — rushi@github</text>'
)

t_end = 0.0
for i, ((label, accent, lines), row_y) in enumerate(zip(laid, row_geometry)):
    begin = i * ROW_T

    # label column: a small accent square, then the category name -- the square
    # is the only place the row's accent appears outside its own chips.
    parts.append(
        f'<g class="lab" style="animation-delay:{begin:.3f}s">'
        f'<rect x="{PAD}" y="{row_y + CHIP_H/2 - 4:.1f}" width="8" height="8" rx="2" fill="{accent}"/>'
        f'<text x="{PAD + 17}" y="{row_y + CHIP_H/2 + 4.5:.1f}" fill="{LABEL_INK}" '
        f'font-size="{LABEL_FONT}">{html.escape(label)}</text></g>'
    )

    n = 0
    for li, line in enumerate(lines):
        x = chips_x
        cy = row_y + li * (CHIP_H + WRAP_GAP)
        for text in line:
            w = chip_w(text)
            delay = begin + ROW_LEAD + n * CHIP_T
            t_end = max(t_end, delay + 0.42)
            parts.append(
                f'<g class="chip" style="animation-delay:{delay:.3f}s">'
                f'<rect x="{x:.1f}" y="{cy:.1f}" width="{w:.1f}" height="{CHIP_H}" rx="7" '
                f'fill="{accent}" fill-opacity="0.10" stroke="{accent}" stroke-opacity="0.34"/>'
                f'<text x="{x + w/2:.1f}" y="{cy + CHIP_H/2 + 4.4:.1f}" fill="{accent}" '
                f'fill-opacity="0.92" font-size="{FONT}" text-anchor="middle">'
                f'{html.escape(text)}</text></g>'
            )
            x += w + CHIP_GAP
            n += 1

parts.append(
    f'<line x1="{PAD}" y1="{rule_y:.1f}" x2="{CANVAS_W-PAD}" y2="{rule_y:.1f}" stroke="{RULE}"/>'
)
foot_y = rule_y + PAD * 0.95
# The idle cursor is a tspan rather than a positioned rect: monospace advance
# varies by which font the viewer actually resolves (Consolas is 0.55em,
# SF Mono 0.6), so any x computed from len(FOOTER) drifts off the text end on
# half the machines. Riding inside the same <text> pins it exactly.
parts.append(
    f'<g class="lab" style="animation-delay:{t_end:.3f}s">'
    f'<text xml:space="preserve" x="{PAD}" y="{foot_y:.1f}" fill="{FOOTER_INK}" '
    f'font-size="12">{html.escape(FOOTER)} '
    f'<tspan class="cur" style="animation-delay:{t_end:.3f}s">█</tspan></text></g>'
)

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}  {len(svg)/1024:.1f} KB  {CANVAS_W}x{canvas_h:.0f}  reveal ends {t_end:.1f}s")
