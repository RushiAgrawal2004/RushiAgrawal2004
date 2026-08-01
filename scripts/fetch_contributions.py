"""Fetch a public GitHub contribution calendar with no token/API needed.

GitHub serves the calendar as public HTML at
https://github.com/users/<username>/contributions -- the same fragment the
profile page itself uses. Parses the day cells and writes
data/contributions.json with raw days plus derived stats.

Usage: python scripts/fetch_contributions.py [username]
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "RushiAgrawal2004"
TOOLTIP_COUNT_RE = re.compile(r"^(\d+|No) contributions?")


def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": "profile-readme-bot"})
    resp.raise_for_status()
    return resp.text


def parse_days(soup: BeautifulSoup) -> list[dict]:
    tooltip_by_id = {
        tt.get("for"): tt.get_text(strip=True)
        for tt in soup.select("tool-tip[for]")
    }

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        date = cell["data-date"]
        level = int(cell.get("data-level", 0))
        count = level
        tooltip = tooltip_by_id.get(cell.get("id"))
        if tooltip:
            m = TOOLTIP_COUNT_RE.match(tooltip)
            if m:
                count = 0 if m.group(1) == "No" else int(m.group(1))
        days.append({"date": date, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def parse_total(soup: BeautifulSoup) -> int | None:
    heading = soup.select_one("#js-contribution-activity-description")
    if not heading:
        return None
    m = re.search(r"([\d,]+)\s*\ncontributions", heading.get_text())
    if not m:
        m = re.search(r"([\d,]+)", heading.get_text())
    return int(m.group(1).replace(",", "")) if m else None


def compute_stats(days: list[dict], total: int | None) -> dict:
    by_month: dict[str, int] = defaultdict(int)
    for d in days:
        by_month[d["date"][:7]] += d["count"]

    current_streak = 0
    longest_streak = 0
    running = 0
    best_day = None
    best_count = -1
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0
        if d["count"] > best_count:
            best_count = d["count"]
            best_day = d["date"]

    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "best_day_count": best_count if best_count >= 0 else None,
        "monthly_totals": dict(by_month),
    }


def main() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    soup = BeautifulSoup(fetch_html(username), "html.parser")
    days = parse_days(soup)
    total = parse_total(soup)
    stats = compute_stats(days, total)
    payload = {"username": username, "days": days, "stats": stats}
    with open("data/contributions.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"wrote data/contributions.json ({len(days)} days, total={total})")


if __name__ == "__main__":
    main()
