"""Generate self-contained HTML review page for content calendar review.

Displays each calendar slot with banner image and platform content columns
for easy visual comparison before scheduling.
"""

import os
import sys

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; padding: 2rem; }
h1 { text-align: center; margin-bottom: 2rem; color: #1a1a1a; }
.slot { background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 2rem; overflow: hidden; }
.slot-header { background: #1a1a1a; color: #fff; padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; }
.slot-header h2 { font-size: 1.1rem; font-weight: 600; }
.slot-header .time { font-size: 0.95rem; opacity: 0.8; }
.slot-image { width: 100%; max-height: 400px; object-fit: cover; display: block; }
.slot-image-placeholder { width: 100%; height: 120px; background: #e0e0e0; display: flex; align-items: center; justify-content: center; color: #999; font-size: 0.9rem; }
.platforms { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1px; background: #e0e0e0; }
.platform-col { background: #fff; padding: 1.25rem; }
.platform-name { font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; }
.platform-name.twitter { color: #1da1f2; }
.platform-name.threads { color: #000; }
.platform-name.facebook { color: #1877f2; }
.platform-name.reddit { color: #ff4500; }
.char-count { font-size: 0.75rem; color: #999; margin-bottom: 0.75rem; }
.content { font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; }
"""


def _escape_html(text):
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _render_slot(slot):
    """Render a single calendar slot as HTML."""
    date = slot.get("date", "")
    day = slot.get("day", "")
    time_ = slot.get("time", "")
    topic = _escape_html(slot.get("topic", ""))

    parts = []
    parts.append('<div class="slot">')
    parts.append(f'<div class="slot-header">')
    parts.append(f'<h2>{date} ({day}) &mdash; {topic}</h2>')
    parts.append(f'<span class="time">{time_}</span>')
    parts.append('</div>')

    # Image
    image_file = slot.get("image_file", "")
    if image_file:
        parts.append(f'<img class="slot-image" src="../{_escape_html(image_file)}" alt="{topic}" onerror="this.style.display=\'none\'">')
    else:
        parts.append('<div class="slot-image-placeholder">Image will be generated</div>')

    # Platform columns
    drafts = slot.get("drafts", {})
    if drafts:
        parts.append('<div class="platforms">')
        for platform, content in drafts.items():
            escaped = _escape_html(content)
            char_count = len(content)
            parts.append(f'<div class="platform-col">')
            parts.append(f'<div class="platform-name {_escape_html(platform)}">{_escape_html(platform)}</div>')
            parts.append(f'<div class="char-count">{char_count} characters</div>')
            parts.append(f'<div class="content">{escaped}</div>')
            parts.append('</div>')
        parts.append('</div>')

    parts.append('</div>')
    return "\n".join(parts)


def generate_review_html(slots, output_path):
    """Generate a self-contained HTML review page.

    Args:
        slots: List of slot dicts. Each slot has date, day, time, topic,
               platforms, image, and a 'drafts' dict mapping platform
               name to content string. Optionally 'image_file'.
        output_path: Where to write the HTML file.
    """
    slot_html = "\n".join(_render_slot(s) for s in slots)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Content Calendar Review</title>
<style>{_CSS}</style>
</head>
<body>
<h1>Content Calendar Review</h1>
{slot_html}
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)


def main(argv=None):
    """CLI entry point: read calendar + draft files, generate HTML review page."""
    import argparse
    from scripts.calendar_utils import parse_calendar
    from scripts.utils.draft import parse_draft

    parser = argparse.ArgumentParser(description="Generate HTML review page from calendar")
    parser.add_argument("--calendar", required=True, help="Calendar file path")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    args = parser.parse_args(argv)

    _, slots = parse_calendar(args.calendar)

    review_slots = []
    for slot in slots:
        review_slot = {
            "date": slot["date"],
            "day": slot["day"],
            "time": slot["time"],
            "topic": slot["topic"],
            "platforms": slot["platforms"],
            "image": slot["image"],
            "image_file": slot.get("image_file", ""),
            "drafts": {},
        }

        for draft_path in slot.get("drafts", []):
            full_path = os.path.join(args.project_dir, draft_path)
            if os.path.exists(full_path):
                _, parts = parse_draft(full_path)
                if parts:
                    # Determine platform from filename (last segment before .md)
                    basename = os.path.basename(draft_path)
                    # Pattern: YYYY-MM-DD_slug_type_platform.md
                    platform = basename.rsplit("_", 1)[-1].replace(".md", "")
                    review_slot["drafts"][platform] = "\n\n".join(parts)

        review_slots.append(review_slot)

    generate_review_html(review_slots, args.output)


if __name__ == "__main__":
    main()
