"""Generate the contribution heatmap SVG matching GitHub's exact styling."""
import urllib.request
import re
import os
from datetime import datetime, timedelta

USERNAME = "Ankitjha9732"
OUTPUT_PATH = "assets/frontend-hero.svg"

# GitHub contribution calendar dimensions (matches their exact SVG)
CELL_SIZE = 10  # GitHub uses 10px squares
GAP = 2         # GitHub uses 2px gap between cells
WEEKS = 53      # 53 weeks in GitHub's contribution calendar
DAYS = 7        # Sunday to Saturday
TOP_PAD = 28    # Space for header text
LEFT_PAD = 72   # Space for weekday labels + padding
BOTTOM_PAD = 44 # Space for month labels + legend + padding
RIGHT_PAD = 12  # Right padding

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Exact opacity mapping from GitHub's contribution levels (0-4)
LEVEL_OPACITY = [0.0, 0.11, 0.31, 0.54, 1.0]  # GitHub's actual values
LEVEL_TO_COUNT = {0: 0, 1: 1, 2: 3, 3: 6, 4: 10}  # Approximate count mapping


def fetch_contributions(username):
    """Fetch contribution data from GitHub's contributions page."""
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        html = r.read().decode('utf-8')
    pattern = r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?data-level="(\d+)"'
    matches = re.findall(pattern, html)
    return {d: int(l) for d, l in matches}


def compute_stats(contribs, sorted_dates):
    """Calculate total contributions, active days, and current streak."""
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
    """Build SVG matching GitHub's exact contribution calendar styling."""
    sorted_dates = sorted(contribs.keys())

    # Find grid start (Sunday before first contribution date)
    start_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
    days_back = (start_date.weekday() + 1) % 7  # Days back to Sunday
    grid_start = start_date - timedelta(days=days_back)

    # Calculate dimensions
    grid_w = WEEKS * CELL_SIZE + (WEEKS - 1) * GAP
    grid_h = DAYS * CELL_SIZE + (DAYS - 1) * GAP
    view_w = LEFT_PAD + grid_w + RIGHT_PAD
    # Increase bottom padding to fit grid (100 cells) + month labels + legend (4 rows + text)
    view_h = TOP_PAD + grid_h + 50  # 50px bottom zone for month labels + legend

    # Initialize SVG parts
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} {view_h}" width="{view_w}" height="{view_h}" role="img" aria-label="Contribution heatmap">']

    # Definitions
    o.append('  <defs>')
    o.append('    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">')
    o.append('      <stop offset="0%" stop-color="#0d1117"/><stop offset="100%" stop-color="#161b22"/>')
    o.append('    </linearGradient>')
    o.append('    <filter id="glow"><feGaussianBlur stdDeviation="1" result="coloredBlur"/><feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    o.append('  </defs>')

    # Background
    o.append(f'  <rect width="{view_w}" height="{view_h}" rx="3" fill="url(#bg)"/>')

    # Header section (top-left: total contributions)
    o.append(f'  <text x="14" y="17" font-size="12" fill="#8b949e" font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji">{total}</text>')
    o.append(f'  <text x="14" y="30" font-size="10" fill="#8b949e" font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji">contributions</text>')

    # Header section (top-right: days and streak separated horizontally)
    days_label_x = view_w - 90   # "21 days" ends here
    streak_label_x = view_w - 10  # "15 streak" ends here

    o.append(f'  <text x="{days_label_x}" y="17" font-size="10" fill="#e6edf3" font-weight="600" font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji" text-anchor="end">{active}</text>')
    o.append(f'  <text x="{days_label_x}" y="30" font-size="8" fill="#6e7681" font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji" text-anchor="end">days</text>')
    o.append(f'  <text x="{streak_label_x}" y="17" font-size="10" fill="#e6edf3" font-weight="600" font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji" text-anchor="end">{streak}</text>')
    o.append(f'  <text x="{streak_label_x}" y="30" font-size="8" fill="#6e7681" font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji" text-anchor="end">streak</text>')

    # Month labels - find first occurrence of each month in chronological order
    month_positions = {}
    for date_str in sorted_dates:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        # Create a key that includes year to handle year-wrapping correctly
        month_key = (dt.year, dt.month)
        if dt.day <= 7 and month_key not in month_positions:
            days_from_start = (dt - grid_start).days
            week_num = days_from_start // 7
            x = LEFT_PAD + week_num * (CELL_SIZE + GAP) + CELL_SIZE // 2
            month_positions[month_key] = (x, dt.month)

    # Sort by year then month to get correct chronological order
    month_y = TOP_PAD + grid_h + 16  # Month labels below grid
    for month_key in sorted(month_positions.keys()):
        x, month_num = month_positions[month_key]
        o.append(f'  <text x="{x}" y="{month_y}" font-size="10" fill="#6e7681" font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji" text-anchor="middle">{MONTHS[month_num-1]}</text>')

    # Day labels (left side: Sun, Tue, Thu, Sat) - centered on cell rows 0, 2, 4, 6
    day_labels = [('Sun', 0), ('Tue', 2), ('Thu', 4), ('Sat', 6)]
    for label, row_index in day_labels:
        y = TOP_PAD + row_index * (CELL_SIZE + GAP) + CELL_SIZE - 5  # Align with cell vertical center
        o.append(f'  <text x="{LEFT_PAD - 6}" y="{y}" font-size="9" fill="#6e7681" font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji" text-anchor="end">{label}</text>')

    # Contribution grid cells
    for date_str in sorted_dates:
        level = contribs[date_str]
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        days_from_start = (dt - grid_start).days
        col = days_from_start // 7  # Week column
        row = days_from_start % 7   # Day row (0=Sun, 6=Sat)

        x = LEFT_PAD + col * (CELL_SIZE + GAP)
        y = TOP_PAD + row * (CELL_SIZE + GAP)

        if level == 0:
            # No contribution - dark background
            o.append(f'  <rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2" fill="#21262d"/>')
        else:
            # Has contribution - purple with varying opacity
            opacity = LEVEL_OPACITY[level]
            extra_attrs = ' filter="url(#glow)"' if level >= 3 else ''  # Glow for high activity
            o.append(f'  <rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2" fill="#8b5cf6" opacity="{opacity}"{extra_attrs}/>')

    # Legend (bottom-left) - matches GitHub's exact legend
    legend_y = TOP_PAD + grid_h + 34  # Below month labels
    legend_x = LEFT_PAD

    # "Less" label
    o.append(f'  <text x="{legend_x}" y="{legend_y}" font-size="10" fill="#6e7681" font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji">Less</text>')

    # Legend squares (0 to 4)
    legend_square_size = 9
    legend_square_spacing = 12
    legend_start_x = legend_x + 32
    square_y = legend_y - 8

    for i, opacity in enumerate([0.0, 0.11, 0.31, 0.54, 1.0]):
        square_x = legend_start_x + i * legend_square_spacing
        o.append(f'  <rect x="{square_x}" y="{square_y}" width="{legend_square_size}" height="{legend_square_size}" rx="2" fill="#8b5cf6" opacity="{opacity}"/>')

    # "More" label (after squares)
    more_x = legend_start_x + 4 * legend_square_spacing + 10
    o.append(f'  <text x="{more_x}" y="{legend_y}" font-size="10" fill="#6e7681" font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji">More</text>')

    o.append('</svg>')
    return '\n'.join(o)


def main():
    """Main execution function."""
    contribs = fetch_contributions(USERNAME)
    if not contribs:
        print("No contribution data found")
        return 1

    sorted_dates = sorted(contribs.keys())
    total, active, streak = compute_stats(contribs, sorted_dates)
    svg = build_svg(contribs, total, active, streak)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Write SVG file
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(svg)

    print(f"Updated {OUTPUT_PATH}: {total} contributions, {active} days active, {streak} day streak")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())