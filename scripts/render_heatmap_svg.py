"""Render data/contributions.json as the classic 53-week x 7-day GitHub
contribution calendar: rounded colored boxes that reveal in a diagonal wave.

Animation notes -- these matter for GitHub:
  * SMIL (<animate>) rather than CSS keyframes. Raw SVGs are served under
    `Content-Security-Policy: default-src 'none'; sandbox`, and SMIL is the
    most reliable thing to survive that in an <img> context. CSS
    `transform-box: fill-box` in particular is inconsistent there.
  * The grid reveals ONCE and then freezes (fill="freeze") -- no looping.
    It replays only when the page is refreshed.
  * Opaque background so the dark GitHub-green ramp reads on light theme.

Usage: python scripts/render_heatmap_svg.py
"""
import json

PALETTE = ["#161b22", "#0e4429", "#006d32",
           "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end, reserved for the
#          single best day of the year)

BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 34
TOP_PAD = 34
LEGEND_H = 24
FOOTER_H = 34
PAD = 14

BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"

STAGGER = 0.035
DUR = 0.5

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def build_grid(days: list[dict]) -> list[list[dict]]:
    weeks: list[list[dict]] = []
    for i, day in enumerate(days):
        week_idx, day_idx = divmod(i, 7)
        if day_idx == 0:
            weeks.append([])
        weeks[week_idx].append(day)
    return weeks


def month_labels(weeks: list[list[dict]]) -> list[tuple[int, str]]:
    labels = []
    last_month = None
    for w, week in enumerate(weeks):
        if not week:
            continue
        month = int(week[0]["date"][5:7])
        if month != last_month:
            labels.append((w, MONTH_NAMES[month - 1]))
            last_month = month
    return labels


def build_svg(data: dict) -> str:
    days = data["days"]
    stats = data["stats"]
    weeks = build_grid(days)
    n_weeks = len(weeks)
    best_day = stats.get("best_day")

    width = LEFT_PAD + n_weeks * CELL + PAD + 10
    height = TOP_PAD + 7 * CELL + LEGEND_H + FOOTER_H + PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        "<style>"
        "text{font-family:SFMono-Regular,Consolas,Menlo,monospace;"
        "fill:#8b949e;font-size:11px;}"
        "</style>",
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" '
        f'rx="8" fill="{BG_COLOR}" stroke="{BORDER_COLOR}"/>',
    ]

    for w, week in enumerate(weeks):
        for d, day in enumerate(week):
            x = LEFT_PAD + w * CELL
            y = TOP_PAD + d * CELL
            level = day.get("level", 0)
            if best_day and day["date"] == best_day:
                level = 5
            color = PALETTE[level]

            delay = (w + d) * STAGGER

            parts.append(
                f'<rect x="{x}" y="{y}" width="{BOX}" height="{BOX}" '
                f'rx="2" fill="{color}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'dur="{DUR}s" begin="{delay:.3f}s" fill="freeze"/>'
                f'<title>{day["count"]} contributions on {day["date"]}</title>'
                f"</rect>"
            )

    for w, name in month_labels(weeks):
        x = LEFT_PAD + w * CELL
        parts.append(f'<text x="{x}" y="{TOP_PAD - 8}">{name}</text>')

    for d, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = TOP_PAD + d * CELL + BOX - 1
        parts.append(f'<text x="{PAD - 8}" y="{y}">{name}</text>')

    legend_y = TOP_PAD + 7 * CELL + 18
    parts.append(f'<text x="{LEFT_PAD}" y="{legend_y}">Less</text>')
    for i, color in enumerate(PALETTE[:5]):
        x = LEFT_PAD + 34 + i * (BOX + 4)
        parts.append(
            f'<rect x="{x}" y="{legend_y - BOX + 2}" width="{BOX}" '
            f'height="{BOX}" rx="2" fill="{color}"/>'
        )
    parts.append(
        f'<text x="{LEFT_PAD + 34 + 5 * (BOX + 4) + 4}" y="{legend_y}">'
        f"More</text>"
    )

    footer_y = legend_y + 26
    total = stats.get("total_last_year")
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer = f"{total} contributions in the last year"
    if streak:
        footer += f"  ·  current streak {streak}d"
    footer += f"  ·  longest streak {longest}d"
    parts.append(f'<text x="{LEFT_PAD}" y="{footer_y}">{footer}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    with open("data/contributions.json", encoding="utf-8") as f:
        data = json.load(f)
    with open("contrib-heatmap.svg", "w", encoding="utf-8") as f:
        f.write(build_svg(data))
    print("wrote contrib-heatmap.svg")
