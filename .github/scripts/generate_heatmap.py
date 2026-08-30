"""Generate the contribution heatmap SVG from live GitHub data."""
import urllib.request
import re
import os
from datetime import datetime, timedelta

USERNAME = "Ankitjha9732"
OUTPUT_PATH = "assets/frontend-hero.svg"

CELL = 11
GAP = 3
COLS = 53
ROWS = 7
TOP_PAD = 60
LEFT_PAD = 40
BOTTOM_PAD = 50
RIGHT_PAD = 20

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

LEVEL_OPACITY = {1: 0.25, 2: 0.45, 3: 0.7, 4: 1.0}
LEVEL_TO_COUNT = {0: 0, 1: 1, 2: 3, 3: 6, 4: 12}


def fetch_contributions(username):
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        html = r.read().decode('utf-8')
    pattern = r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?data-level="(\d+)"'
    matches = re.findall(pattern, html)
    return {d: int(l) for d, l in matches}


def compute_stats(contribs, sorted_dates):
    total = sum(LEVEL_TO_COUNT[contribs[d]] for d in sorted_dates if contribs[d] > 0)
    active = sum(1 for d in sorted_dates if contribs[d] > 0)
    streak = 0
    for i in range(len(sorted_dates) - 1, -1, -1):
        if contribs[sorted_dates[i]] > 0:
            streak += 1
        else:
            break
    return total, active, streak


def build_svg(contribs, total, active, streak):
    sorted_dates = sorted(contribs.keys())
    start_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
    days_back = (start_date.weekday() + 1) % 7
    grid_start = start_date - timedelta(days=days_back)

    grid_w = COLS * CELL + (COLS - 1) * GAP
    grid_h = ROWS * CELL + (ROWS - 1) * GAP
    view_w = LEFT_PAD + grid_w + RIGHT_PAD
    view_h = TOP_PAD + grid_h + BOTTOM_PAD

    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} {view_h}" width="{view_w}" height="{view_h}" role="img">')
    o.append('  <defs>')
    o.append('    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">')
    o.append('      <stop offset="0%" stop-color="#0d1117"/><stop offset="100%" stop-color="#161b22"/>')
    o.append('    </linearGradient>')
    o.append('    <filter id="g"><feGaussianBlur stdDeviation="1.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    o.append('  </defs>')
    o.append('  <style>.m{font-family:ui-monospace,SFMono,Menlo,monospace}</style>')
    o.append(f'  <rect width="{view_w}" height="{view_h}" rx="12" fill="url(#bg)"/>')

    # Header
    o.append(f'  <text class="m" x="20" y="24" font-size="14" fill="#e6edf3" font-weight="bold">{total} contributions</text>')
    o.append(f'  <text class="m" x="180" y="24" font-size="10" fill="#8b949e">in the last year</text>')
    o.append(f'  <text class="m" x="{view_w-200}" y="24" font-size="11" fill="#e6edf3" font-weight="bold">{active}</text>')
    o.append(f'  <text class="m" x="{view_w-200}" y="40" font-size="8" fill="#6e7681">days active</text>')
    o.append(f'  <text class="m" x="{view_w-90}" y="24" font-size="11" fill="#e6edf3" font-weight="bold">{streak}</text>')
    o.append(f'  <text class="m" x="{view_w-90}" y="40" font-size="8" fill="#6e7681">day streak</text>')

    # Month labels
    month_x = {}
    for d_str in sorted_dates:
        d = datetime.strptime(d_str, '%Y-%m-%d')
        if d.day <= 7 and d.month not in month_x:
            week_idx = (d - grid_start).days // 7
            month_x[d.month] = LEFT_PAD + week_idx * (CELL + GAP)
    for m in sorted(month_x.keys()):
        o.append(f'  <text class="m" x="{month_x[m]}" y="56" font-size="8" fill="#6e7681">{MONTHS[m-1]}</text>')

    # Day labels
    for row, label in [(0, 'Sun'), (2, 'Tue'), (4, 'Thu'), (6, 'Sat')]:
        y = TOP_PAD + row * (CELL + GAP) + CELL * 0.7
        o.append(f'  <text class="m" x="32" y="{y}" font-size="7" fill="#6e7681" text-anchor="end">{label}</text>')

    # Cells
    for d_str in sorted_dates:
        level = contribs[d_str]
        d = datetime.strptime(d_str, '%Y-%m-%d')
        days_from_start = (d - grid_start).days
        col = days_from_start // 7
        row = days_from_start % 7
        x = LEFT_PAD + col * (CELL + GAP)
        y = TOP_PAD + row * (CELL + GAP)
        if level == 0:
            o.append(f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="#21262d"/>')
        else:
            extra = ' filter="url(#g)"' if level >= 3 else ''
            o.append(f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="#a855f7" opacity="{LEVEL_OPACITY[level]}"{extra}/>')

    # Legend
    lx = view_w - 140
    ly = view_h - 20
    o.append(f'  <text class="m" x="{lx}" y="{ly}" font-size="8" fill="#6e7681">Less</text>')
    for i, op in enumerate([0, 0.25, 0.45, 0.7, 1.0]):
        o.append(f'  <rect x="{lx+32+i*12}" y="{ly-9}" width="9" height="9" rx="2" fill="#a855f7" opacity="{op}"/>')
    o.append(f'  <text class="m" x="{lx+96}" y="{ly}" font-size="8" fill="#6e7681">More</text>')
    o.append('</svg>')
    return '\n'.join(o)


def main():
    contribs = fetch_contributions(USERNAME)
    if not contribs:
        print("No contribution data found")
        return 1
    sorted_dates = sorted(contribs.keys())
    total, active, streak = compute_stats(contribs, sorted_dates)
    svg = build_svg(contribs, total, active, streak)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f"Updated {OUTPUT_PATH}: {total} contributions, {active} days active, {streak} day streak")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
