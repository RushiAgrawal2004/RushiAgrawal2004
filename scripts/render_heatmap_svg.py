"""Render data/contributions.json as the classic 53-week x 7-day GitHub
contribution calendar, as rounded colored boxes that reveal once with a
diagonal slide-down (CSS keyframes that play on load, then freeze -- no
looping). Adds a Less->More legend and a stats footer.

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
LEFT_PAD = 24
TOP_PAD = 20
LEGEND_H = 24
FOOTER_H = 34
STAGGER = 0.012
DUR = 0.45

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

    width = LEFT_PAD + n_weeks * CELL + 20
    height = TOP_PAD + 7 * CELL + LEGEND_H + FOOTER_H + 20

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text{font-family:SFMono-Regular,Consolas,Menlo,monospace;"
        "fill:#8b949e;font-size:11px;}",
        ".day{opacity:0;transform-box:fill-box;transform-origin:center;"
        "animation:reveal " + f"{DUR}s" + " ease-out forwards;}",
        "@keyframes reveal{"
        "0%{opacity:0;transform:translate(-6px,-6px) scale(.4);}"
        "100%{opacity:1;transform:translate(0,0) scale(1);}}",
        "</style>",
        f'<rect width="100%" height="100%" fill="none"/>',
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
                f'<rect class="day" x="{x}" y="{y}" width="{BOX}" '
                f'height="{BOX}" rx="2" fill="{color}" '
                f'style="animation-delay:{delay:.3f}s">'
                f'<title>{day["count"]} contributions on {day["date"]}</title>'
                f'</rect>'
            )

    for w, name in month_labels(weeks):
        x = LEFT_PAD + w * CELL
        parts.append(f'<text x="{x}" y="{TOP_PAD - 6}">{name}</text>')

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
        f'More</text>'
    )

    footer_y = legend_y + 26
    total = stats.get("total_last_year")
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer_text = f"{total} contributions in the last year"
    if streak:
        footer_text += f"  ·  current streak {streak}d"
    footer_text += f"  ·  longest streak {longest}d"
    parts.append(f'<text x="{LEFT_PAD}" y="{footer_y}">{footer_text}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    with open("data/contributions.json", encoding="utf-8") as f:
        data = json.load(f)
    svg = build_svg(data)
    with open("contrib-heatmap.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote contrib-heatmap.svg")
