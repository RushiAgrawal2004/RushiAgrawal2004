"""Hand-authored neofetch-style info card SVG: title bar + colored key/value
rows that fade + slide in on a short stagger.

Set STATIC=1 to emit a frozen frame (all rows already visible) for local
Quick Look previews.

Usage: python scripts/make_info_card.py
"""
import os

WIDTH = 490
ROW_H = 34
TOP_PAD = 56
LEFT_PAD = 20
STATIC = os.environ.get("STATIC") == "1"

TITLE = "avi@github"
ROWS = [
    ("Now", "Software Engineer", "#39d353"),
    ("Prev", "Full-stack + creative dev", "#58a6ff"),
    ("Stack", "TypeScript, Python, React, Node", "#e3b341"),
    ("Highlights", "Building small tools that ship", "#f778ba"),
]

HEIGHT = TOP_PAD + ROW_H * len(ROWS) + 24


def build_svg() -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        "<style>"
        "text{font-family:SFMono-Regular,Consolas,Menlo,monospace;}"
        ".label{font-size:13px;fill:#8b949e;}"
        ".value{font-size:13px;fill:#c9d1d9;}"
        ".title{font-size:14px;fill:#c9d1d9;font-weight:600;}"
        "</style>",
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" '
        f'rx="8" fill="#0d1117" stroke="#30363d"/>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="32" rx="8" '
        f'fill="#161b22"/>',
        f'<rect x="0.5" y="24.5" width="{WIDTH - 1}" height="8" '
        f'fill="#161b22"/>',
        '<circle cx="20" cy="16" r="6" fill="#ff5f56"/>',
        '<circle cx="40" cy="16" r="6" fill="#ffbd2e"/>',
        '<circle cx="60" cy="16" r="6" fill="#27c93f"/>',
        f'<text x="{WIDTH / 2:.0f}" y="20" text-anchor="middle" '
        f'class="title">{TITLE}</text>',
    ]

    for i, (label, value, color) in enumerate(ROWS):
        y = TOP_PAD + i * ROW_H
        begin = 0.15 + i * 0.12

        parts.append(f'<g opacity="{1 if STATIC else 0}" '
                      f'transform="translate({0 if STATIC else -12},0)">')
        if not STATIC:
            parts.append(
                f'<animate attributeName="opacity" from="0" to="1" '
                f'dur="0.35s" begin="{begin:.2f}s" fill="freeze"/>'
            )
            parts.append(
                f'<animateTransform attributeName="transform" '
                f'type="translate" from="-12,0" to="0,0" dur="0.35s" '
                f'begin="{begin:.2f}s" fill="freeze"/>'
            )
        parts.append(
            f'<rect x="{LEFT_PAD - 8}" y="{y - 14}" width="4" height="16" '
            f'rx="2" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{LEFT_PAD + 4}" y="{y}" class="label">{label}</text>'
        )
        parts.append(
            f'<text x="{LEFT_PAD + 110}" y="{y}" class="value">{value}</text>'
        )
        parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    svg = build_svg()
    with open("info-card.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote info-card.svg")
