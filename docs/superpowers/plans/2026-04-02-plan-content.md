# `/plan-content` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/plan-content` slash command that plans a content calendar from the knowledge base, generates drafts + images, lets user review visually in the browser, and schedules automatic posting via Claude Code triggers.

**Architecture:** New command `plan-content.md` orchestrates the 3-phase flow (plan → generate → schedule). A new Python script `calendar_utils.py` handles calendar file parsing/updating. An HTML review page generator `review_page.py` creates a self-contained visual review. Existing commands (`/generate-content`, `/generate-image`, `/post`) are reused internally. The `post.py` script is updated to accept `status: scheduled` drafts.

**Tech Stack:** Python 3, PyYAML, inline HTML/CSS generation, Claude Code `/schedule` triggers, existing kie.ai and platform posting scripts.

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `plugin/commands/plan-content.md` | Slash command — orchestrates the 3-phase flow |
| Create | `plugin/scripts/calendar_utils.py` | Parse/update calendar markdown files |
| Create | `plugin/scripts/review_page.py` | Generate self-contained HTML review page from calendar + drafts |
| Create | `tests/test_calendar_utils.py` | Tests for calendar parsing and updating |
| Create | `tests/test_review_page.py` | Tests for HTML review page generation |
| Modify | `plugin/scripts/utils/draft.py` | No changes needed — `scheduled_at` and `calendar` fields pass through existing `update_frontmatter()` |
| Modify | `plugin/scripts/post.py:39` | Accept `status: scheduled` in addition to `status: draft` |

---

### Task 1: Update `post.py` to accept scheduled drafts

**Files:**
- Modify: `plugin/scripts/post.py:39`
- Modify: `tests/test_post.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_post.py`:

```python
@patch("scripts.platforms.twitter.tweepy")
@patch("scripts.utils.config.load_config")
def test_post_accepts_scheduled_status(mock_load_config, mock_tweepy):
    """post.py accepts drafts with status: scheduled (from /plan-content)."""
    mock_load_config.return_value = {
        "twitter": {"api_key": "k", "api_secret": "s", "access_token": "t", "access_secret": "a"}
    }
    mock_client = MagicMock()
    mock_client.create_tweet.return_value = MagicMock(data={"id": "222", "text": "Scheduled"})
    mock_tweepy.Client.return_value = mock_client

    content = """---
platform: twitter
type: tweet
topic: "Scheduled Test"
status: scheduled
scheduled_at: "2026-04-03 09:00"
calendar: calendar-2026-04-02.md
created_at: "2026-04-02 10:00"
posted_at: ""
post_ids: []
has_images: false
images: []
---

Scheduled tweet content.
"""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    f.write(content)
    f.close()

    try:
        from scripts.post import main
        result = main(["--file", f.name])
        assert result["success"] is True
        assert result["post_ids"] == ["222"]
    finally:
        os.unlink(f.name)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd plugin && python3 -m pytest ../tests/test_post.py::test_post_accepts_scheduled_status -v`
Expected: FAIL — `post.py` rejects anything that isn't `draft` (line 39 checks `status == "posted"` and returns error).

- [ ] **Step 3: Update post.py to accept scheduled status**

In `plugin/scripts/post.py`, change line 39 from:

```python
    if frontmatter.get("status") == "posted":
        return {"success": False, "error": f"Already posted: {file_path}"}
```

to:

```python
    if frontmatter.get("status") == "posted":
        return {"success": False, "error": f"Already posted: {file_path}"}
```

Wait — the current code only rejects `posted`, so `scheduled` should already pass through. Let me re-read. Yes, the check is `== "posted"` which means `scheduled` is already accepted. The test should pass already.

- [ ] **Step 2 (revised): Run test to verify it passes**

Run: `cd plugin && python3 -m pytest ../tests/test_post.py::test_post_accepts_scheduled_status -v`
Expected: PASS — `post.py` only blocks `status: posted`, so `scheduled` works.

- [ ] **Step 3: Run all existing tests to confirm no regression**

Run: `cd plugin && python3 -m pytest ../tests/ -v`
Expected: 46 passed (45 existing + 1 new).

- [ ] **Step 4: Commit**

```bash
git add tests/test_post.py
git commit -m "test: verify post.py accepts scheduled status drafts"
```

---

### Task 2: Create `calendar_utils.py` — calendar file parser

**Files:**
- Create: `plugin/scripts/calendar_utils.py`
- Create: `tests/test_calendar_utils.py`

- [ ] **Step 1: Write the failing test for `parse_calendar`**

Create `tests/test_calendar_utils.py`:

```python
import os
import sys
import tempfile

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_parse_calendar_basic():
    """parse_calendar extracts frontmatter and list of slots from calendar file."""
    content = """---
created_at: "2026-04-02 10:00"
period: "2026-04-03 → 2026-04-09"
posts_per_day: 1
status: draft
---

## 2026-04-03 (Thu) — 09:00
**Topic:** Artemis II mission update
**Platforms:** twitter, threads, facebook
**Image:** ai

## 2026-04-04 (Fri) — 18:30
**Topic:** AI regulation in EU
**Platforms:** twitter, threads
**Image:** ai
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        from scripts.calendar_utils import parse_calendar

        meta, slots = parse_calendar(path)
        assert meta["status"] == "draft"
        assert meta["posts_per_day"] == 1
        assert len(slots) == 2

        assert slots[0]["date"] == "2026-04-03"
        assert slots[0]["day"] == "Thu"
        assert slots[0]["time"] == "09:00"
        assert slots[0]["topic"] == "Artemis II mission update"
        assert slots[0]["platforms"] == ["twitter", "threads", "facebook"]
        assert slots[0]["image"] == "ai"

        assert slots[1]["date"] == "2026-04-04"
        assert slots[1]["time"] == "18:30"
        assert slots[1]["platforms"] == ["twitter", "threads"]
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd plugin && python3 -m pytest ../tests/test_calendar_utils.py::test_parse_calendar_basic -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.calendar_utils'`

- [ ] **Step 3: Implement `parse_calendar`**

Create `plugin/scripts/calendar_utils.py`:

```python
"""Calendar file parsing and updating for /plan-content.

Calendar files live in contents/calendar-YYYY-MM-DD.md with YAML frontmatter
and ## date-time heading slots.
"""

import os
import re
import sys

import yaml

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def parse_calendar(file_path):
    """Parse a calendar markdown file into metadata and slot list.

    Returns:
        (metadata_dict, list_of_slot_dicts)
        Each slot dict has: date, day, time, topic, platforms, image,
        and optionally: drafts, image_file.
    """
    with open(file_path, "r") as f:
        raw = f.read()

    fm_match = re.match(r"^---\n(.*?)\n---\n(.*)", raw, re.DOTALL)
    if not fm_match:
        return {}, []

    metadata = yaml.safe_load(fm_match.group(1)) or {}
    body = fm_match.group(2).strip()

    slots = []
    # Split by ## headings: "## 2026-04-03 (Thu) — 09:00"
    slot_pattern = re.compile(
        r"^## (\d{4}-\d{2}-\d{2}) \((\w+)\) — (\d{2}:\d{2})\s*$",
        re.MULTILINE,
    )
    matches = list(slot_pattern.finditer(body))

    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        block = body[start:end].strip()

        slot = {
            "date": m.group(1),
            "day": m.group(2),
            "time": m.group(3),
            "topic": "",
            "platforms": [],
            "image": "ai",
        }

        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("**Topic:**"):
                slot["topic"] = line.replace("**Topic:**", "").strip()
            elif line.startswith("**Platforms:**"):
                raw_platforms = line.replace("**Platforms:**", "").strip()
                slot["platforms"] = [p.strip() for p in raw_platforms.split(",")]
            elif line.startswith("**Image:**"):
                slot["image"] = line.replace("**Image:**", "").strip()
            elif line.startswith("**Image file:**"):
                slot["image_file"] = line.replace("**Image file:**", "").strip()
            elif line.startswith("- contents/") or line.startswith("- images/"):
                # Collect draft file references
                if "drafts" not in slot:
                    slot["drafts"] = []
                slot["drafts"].append(line.lstrip("- ").strip())

        slots.append(slot)

    return metadata, slots


def write_calendar(file_path, metadata, slots):
    """Write a calendar file from metadata and slot list.

    Args:
        file_path: Output file path.
        metadata: Dict with created_at, period, posts_per_day, status.
        slots: List of slot dicts from parse_calendar format.
    """
    yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False).strip()
    lines = [f"---\n{yaml_str}\n---\n"]

    for slot in slots:
        lines.append(f"## {slot['date']} ({slot['day']}) — {slot['time']}")
        lines.append(f"**Topic:** {slot['topic']}")
        lines.append(f"**Platforms:** {', '.join(slot['platforms'])}")
        lines.append(f"**Image:** {slot['image']}")

        if "drafts" in slot:
            lines.append("**Drafts:**")
            for d in slot["drafts"]:
                lines.append(f"- {d}")

        if "image_file" in slot:
            lines.append(f"**Image file:** {slot['image_file']}")

        lines.append("")  # blank line between slots

    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with open(file_path, "w") as f:
        f.write("\n".join(lines))


def update_calendar_status(file_path, new_status):
    """Update the status field in a calendar file's frontmatter.

    Args:
        file_path: Path to the calendar file.
        new_status: New status string (draft, generated, scheduled).
    """
    metadata, slots = parse_calendar(file_path)
    metadata["status"] = new_status
    write_calendar(file_path, metadata, slots)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd plugin && python3 -m pytest ../tests/test_calendar_utils.py::test_parse_calendar_basic -v`
Expected: PASS

- [ ] **Step 5: Write test for `write_calendar`**

Add to `tests/test_calendar_utils.py`:

```python
def test_write_calendar_roundtrip():
    """write_calendar produces a file that parse_calendar can read back."""
    from scripts.calendar_utils import write_calendar, parse_calendar

    metadata = {
        "created_at": "2026-04-02 10:00",
        "period": "2026-04-03 → 2026-04-05",
        "posts_per_day": 1,
        "status": "draft",
    }
    slots = [
        {
            "date": "2026-04-03",
            "day": "Thu",
            "time": "09:00",
            "topic": "Topic A",
            "platforms": ["twitter", "threads"],
            "image": "ai",
        },
        {
            "date": "2026-04-04",
            "day": "Fri",
            "time": "18:30",
            "topic": "Topic B",
            "platforms": ["twitter", "facebook"],
            "image": "web",
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = f.name

    try:
        write_calendar(path, metadata, slots)
        meta_out, slots_out = parse_calendar(path)

        assert meta_out["status"] == "draft"
        assert meta_out["posts_per_day"] == 1
        assert len(slots_out) == 2
        assert slots_out[0]["topic"] == "Topic A"
        assert slots_out[0]["platforms"] == ["twitter", "threads"]
        assert slots_out[1]["topic"] == "Topic B"
        assert slots_out[1]["image"] == "web"
    finally:
        os.unlink(path)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd plugin && python3 -m pytest ../tests/test_calendar_utils.py::test_write_calendar_roundtrip -v`
Expected: PASS

- [ ] **Step 7: Write test for `update_calendar_status`**

Add to `tests/test_calendar_utils.py`:

```python
def test_update_calendar_status():
    """update_calendar_status changes frontmatter status, preserves slots."""
    from scripts.calendar_utils import write_calendar, parse_calendar, update_calendar_status

    metadata = {
        "created_at": "2026-04-02 10:00",
        "period": "2026-04-03 → 2026-04-04",
        "posts_per_day": 1,
        "status": "draft",
    }
    slots = [
        {
            "date": "2026-04-03",
            "day": "Thu",
            "time": "09:00",
            "topic": "Topic A",
            "platforms": ["twitter"],
            "image": "ai",
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = f.name

    try:
        write_calendar(path, metadata, slots)
        update_calendar_status(path, "generated")

        meta_out, slots_out = parse_calendar(path)
        assert meta_out["status"] == "generated"
        assert len(slots_out) == 1
        assert slots_out[0]["topic"] == "Topic A"
    finally:
        os.unlink(path)
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd plugin && python3 -m pytest ../tests/test_calendar_utils.py::test_update_calendar_status -v`
Expected: PASS

- [ ] **Step 9: Write test for parsing calendar with drafts and image_file fields**

Add to `tests/test_calendar_utils.py`:

```python
def test_parse_calendar_with_drafts():
    """parse_calendar reads Drafts and Image file fields from generated calendar."""
    content = """---
created_at: "2026-04-02 10:00"
period: "2026-04-03 → 2026-04-04"
posts_per_day: 1
status: generated
---

## 2026-04-03 (Thu) — 09:00
**Topic:** Topic A
**Platforms:** twitter, threads
**Image:** ai
**Drafts:**
- contents/2026-04-03_topic-a_tweet_twitter.md
- contents/2026-04-03_topic-a_post_threads.md
**Image file:** images/2026-04-03_topic-a_banner.png
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        from scripts.calendar_utils import parse_calendar

        meta, slots = parse_calendar(path)
        assert meta["status"] == "generated"
        assert len(slots) == 1
        assert slots[0]["drafts"] == [
            "contents/2026-04-03_topic-a_tweet_twitter.md",
            "contents/2026-04-03_topic-a_post_threads.md",
        ]
        assert slots[0]["image_file"] == "images/2026-04-03_topic-a_banner.png"
    finally:
        os.unlink(path)
```

- [ ] **Step 10: Run all calendar tests**

Run: `cd plugin && python3 -m pytest ../tests/test_calendar_utils.py -v`
Expected: 4 passed

- [ ] **Step 11: Run full test suite**

Run: `cd plugin && python3 -m pytest ../tests/ -v`
Expected: 50 passed (45 existing + 1 post + 4 calendar)

- [ ] **Step 12: Commit**

```bash
git add plugin/scripts/calendar_utils.py tests/test_calendar_utils.py
git commit -m "feat: add calendar_utils.py for parsing and writing calendar files"
```

---

### Task 3: Create `review_page.py` — HTML review page generator

**Files:**
- Create: `plugin/scripts/review_page.py`
- Create: `tests/test_review_page.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_review_page.py`:

```python
import os
import sys
import tempfile

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_generate_review_html_basic():
    """generate_review_html creates a self-contained HTML file with slot content."""
    from scripts.review_page import generate_review_html

    slots = [
        {
            "date": "2026-04-03",
            "day": "Thu",
            "time": "09:00",
            "topic": "Topic A",
            "platforms": ["twitter", "threads"],
            "image": "ai",
            "image_file": "images/2026-04-03_topic-a_banner.png",
            "drafts": {
                "twitter": "Tweet 1 content here.\n\nWith a second line.",
                "threads": "Threads post content here.",
            },
        },
    ]

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        output_path = f.name

    try:
        generate_review_html(slots, output_path)

        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            html = f.read()

        assert "<!DOCTYPE html>" in html
        assert "Topic A" in html
        assert "2026-04-03" in html
        assert "09:00" in html
        assert "Tweet 1 content here." in html
        assert "Threads post content here." in html
        assert "topic-a_banner.png" in html
        assert "<style>" in html  # inline CSS
    finally:
        os.unlink(output_path)


def test_generate_review_html_multiple_slots():
    """generate_review_html handles multiple slots."""
    from scripts.review_page import generate_review_html

    slots = [
        {
            "date": "2026-04-03",
            "day": "Thu",
            "time": "09:00",
            "topic": "Topic A",
            "platforms": ["twitter"],
            "image": "ai",
            "drafts": {"twitter": "Content A"},
        },
        {
            "date": "2026-04-04",
            "day": "Fri",
            "time": "18:30",
            "topic": "Topic B",
            "platforms": ["threads", "facebook"],
            "image": "ai",
            "drafts": {
                "threads": "Content B threads",
                "facebook": "Content B facebook",
            },
        },
    ]

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        output_path = f.name

    try:
        generate_review_html(slots, output_path)

        with open(output_path, "r") as f:
            html = f.read()

        assert "Topic A" in html
        assert "Topic B" in html
        assert "Content A" in html
        assert "Content B threads" in html
        assert "Content B facebook" in html
    finally:
        os.unlink(output_path)


def test_generate_review_html_char_count():
    """generate_review_html includes character count per platform."""
    from scripts.review_page import generate_review_html

    slots = [
        {
            "date": "2026-04-03",
            "day": "Thu",
            "time": "09:00",
            "topic": "Test",
            "platforms": ["twitter"],
            "image": "ai",
            "drafts": {"twitter": "Hello world"},  # 11 chars
        },
    ]

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        output_path = f.name

    try:
        generate_review_html(slots, output_path)

        with open(output_path, "r") as f:
            html = f.read()

        assert "11" in html  # character count displayed
    finally:
        os.unlink(output_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd plugin && python3 -m pytest ../tests/test_review_page.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.review_page'`

- [ ] **Step 3: Implement `review_page.py`**

Create `plugin/scripts/review_page.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugin && python3 -m pytest ../tests/test_review_page.py -v`
Expected: 3 passed

- [ ] **Step 5: Run full test suite**

Run: `cd plugin && python3 -m pytest ../tests/ -v`
Expected: 53 passed

- [ ] **Step 6: Commit**

```bash
git add plugin/scripts/review_page.py tests/test_review_page.py
git commit -m "feat: add review_page.py for HTML content calendar review"
```

---

### Task 4: Create `plan-content.md` slash command

**Files:**
- Create: `plugin/commands/plan-content.md`

- [ ] **Step 1: Write the command file**

Create `plugin/commands/plan-content.md`:

````markdown
---
description: Plan a content calendar and schedule posts for an upcoming period
argument-hint: [duration] [--posts-per-day N]
---

Plan social media content for an upcoming period. AI proposes a calendar from the knowledge base, generates drafts and images, and schedules automatic posting.

## Setup

1. Check that `./contents/` and `./images/` directories exist. If not, tell user: "Missing directories. Run `/setup` or `/init` first."
2. Read `./summary.md`. If it doesn't exist, tell user: "No summary.md found. Run `/summarize` first."
3. Read `.social-agent.yaml` to determine which platforms are configured. If no platforms configured, tell user: "No platforms configured. Run `/setup` first."

## Arguments

- `duration`: How far ahead to plan. Examples: `7 days`, `2 weeks`, `30 days`. Default: `7 days`.
- `--posts-per-day N`: Number of posts per day. Default: `1`.

## Phase 1: Calendar Proposal

1. Read `./summary.md` to extract available topics.
2. Select the most compelling and diverse topics from the knowledge base. Spread variety — avoid consecutive similar topics.
3. Create a calendar with 1 slot per post:
   - Assign varied posting times across days (e.g., mornings, afternoons, evenings). If multiple posts/day, times must differ.
   - Default ALL configured platforms for every slot.
   - Default `Image: ai` for every slot (knowledge base content is project-related).
4. Write the calendar to `./contents/calendar-YYYY-MM-DD.md` with this format:

```markdown
---
created_at: "YYYY-MM-DD HH:MM"
period: "YYYY-MM-DD → YYYY-MM-DD"
posts_per_day: N
status: draft
---

## YYYY-MM-DD (Day) — HH:MM
**Topic:** Topic name
**Platforms:** twitter, threads, facebook
**Image:** ai
```

5. Display the full calendar in terminal.
6. Ask user: "Review the calendar above. Tell me what to change, or say **approve** to start generating content."
7. **Review loop:** If user requests changes (edit topic, remove/add platform, change time, change image source), update the calendar file and display again. Repeat until user approves.

## Phase 2: Content & Image Generation

Triggered after calendar approval.

1. Parse the approved calendar using:

```python
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar_utils.py parse --file <calendar-path>
```

This is for reference — the command orchestrates generation directly.

2. **For each slot in the calendar, sequentially:**
   a. Generate platform-specific drafts using the same logic as `/generate-content`:
      - For each platform in the slot, generate a draft following platform-specific formatting rules and character limits from `/generate-content`.
      - Each draft includes extra frontmatter fields:
        ```yaml
        scheduled_at: "YYYY-MM-DD HH:MM"
        calendar: calendar-YYYY-MM-DD.md
        ```
      - Save to `./contents/` with naming: `YYYY-MM-DD_<topic-slug>_<type>_<platform>.md`
   b. Generate image for this slot's topic:
      - If `Image: ai` → Run `/generate-image` with the draft (uses kie.ai).
      - If `Image: web` → Run `/generate-image` with the draft (uses web search).
      - 1 image per topic, shared across all platforms for that topic.
   c. Update the calendar slot with draft file paths and image file path.

3. After all slots are generated, update calendar status to `generated`.

4. **Build review data** for each slot:
   - Read each draft file's content body.
   - Collect into a structure: `{date, time, topic, image_file, drafts: {platform: content}}`.

5. **Generate HTML review page:**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_page.py \
  --calendar <calendar-path> \
  --output ./contents/calendar-YYYY-MM-DD-review.html
```

Or build the review data in-command and call the script. The review page shows:
- Each slot: date, time, topic
- Banner image (full width)
- Platform columns side by side with character counts

6. Open the HTML file in the user's browser:

```bash
open ./contents/calendar-YYYY-MM-DD-review.html
```

7. Tell user: "Review page opened in browser. Check the content and images. Tell me what to change, or say **approve all** to schedule."

8. **Review loop:** If user requests changes, edit the relevant draft files, regenerate the HTML review page, and reload. Repeat until user approves all.

## Phase 3: Scheduling

Triggered after user approves all content.

1. **For each slot in the calendar:**
   - Collect all draft files for this slot (from the calendar's `Drafts:` list).
   - Use Claude Code `/schedule` to create ONE scheduled trigger for this slot:
     - Trigger time: the slot's datetime (e.g., "2026-04-03 09:00")
     - Trigger action: For each draft file in this slot, run `/post <draft-file>`
   - This means: 1 trigger per slot, each trigger posts to all platforms for that topic.

2. **Update statuses:**
   - Update each draft file: `status: scheduled`
   - Update calendar file: `status: scheduled`

3. **Cleanup:**
   - Delete `./contents/calendar-YYYY-MM-DD-review.html`

4. **Display summary:**

```
Content calendar scheduled!

Period: 2026-04-03 → 2026-04-09
Total posts: 21 (7 topics × 3 platforms)
Triggers: 7

Upcoming:
  2026-04-03 09:00 — Topic A → twitter, threads, facebook
  2026-04-04 18:30 — Topic B → twitter, threads, facebook
  ...

Use `/schedule list` to view or cancel scheduled triggers.
```
````

- [ ] **Step 2: Verify the command is well-formed**

Run: `head -5 plugin/commands/plan-content.md` to verify YAML frontmatter is valid.

- [ ] **Step 3: Run full test suite to confirm no regressions**

Run: `cd plugin && python3 -m pytest ../tests/ -v`
Expected: 53 passed (no change — command files are markdown, not tested by pytest)

- [ ] **Step 4: Commit**

```bash
git add plugin/commands/plan-content.md
git commit -m "feat: add /plan-content slash command for content calendar planning"
```

---

### Task 5: Make `calendar_utils.py` callable as CLI

**Files:**
- Modify: `plugin/scripts/calendar_utils.py`
- Create: `tests/test_calendar_utils_cli.py`

The `/plan-content` command needs to parse calendar files from the command line. Add a CLI entry point.

- [ ] **Step 1: Write the failing test**

Create `tests/test_calendar_utils_cli.py`:

```python
import json
import os
import sys
import tempfile

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_cli_parse():
    """calendar_utils CLI parse action outputs JSON with metadata and slots."""
    content = """---
created_at: "2026-04-02 10:00"
period: "2026-04-03 → 2026-04-04"
posts_per_day: 1
status: draft
---

## 2026-04-03 (Thu) — 09:00
**Topic:** Topic A
**Platforms:** twitter, threads
**Image:** ai
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        from scripts.calendar_utils import main
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["parse", "--file", path])

        output = json.loads(buf.getvalue())
        assert output["metadata"]["status"] == "draft"
        assert len(output["slots"]) == 1
        assert output["slots"][0]["topic"] == "Topic A"
    finally:
        os.unlink(path)


def test_cli_update_status():
    """calendar_utils CLI update-status action changes the calendar status."""
    content = """---
created_at: "2026-04-02 10:00"
period: "2026-04-03 → 2026-04-04"
posts_per_day: 1
status: draft
---

## 2026-04-03 (Thu) — 09:00
**Topic:** Topic A
**Platforms:** twitter
**Image:** ai
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        from scripts.calendar_utils import main, parse_calendar

        main(["update-status", "--file", path, "--status", "generated"])

        meta, slots = parse_calendar(path)
        assert meta["status"] == "generated"
        assert len(slots) == 1
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd plugin && python3 -m pytest ../tests/test_calendar_utils_cli.py -v`
Expected: FAIL — `AttributeError: module 'scripts.calendar_utils' has no attribute 'main'`

- [ ] **Step 3: Add CLI entry point to `calendar_utils.py`**

Append to the bottom of `plugin/scripts/calendar_utils.py`:

```python
def main(argv=None):
    """CLI entry point for calendar operations."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Calendar file utilities")
    sub = parser.add_subparsers(dest="action", required=True)

    parse_cmd = sub.add_parser("parse", help="Parse calendar file to JSON")
    parse_cmd.add_argument("--file", required=True, help="Calendar file path")

    update_cmd = sub.add_parser("update-status", help="Update calendar status")
    update_cmd.add_argument("--file", required=True, help="Calendar file path")
    update_cmd.add_argument("--status", required=True, help="New status")

    args = parser.parse_args(argv)

    if args.action == "parse":
        metadata, slots = parse_calendar(args.file)
        print(json.dumps({"metadata": metadata, "slots": slots}))
    elif args.action == "update-status":
        update_calendar_status(args.file, args.status)
        print(json.dumps({"success": True, "status": args.status}))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugin && python3 -m pytest ../tests/test_calendar_utils_cli.py -v`
Expected: 2 passed

- [ ] **Step 5: Run full test suite**

Run: `cd plugin && python3 -m pytest ../tests/ -v`
Expected: 55 passed

- [ ] **Step 6: Commit**

```bash
git add plugin/scripts/calendar_utils.py tests/test_calendar_utils_cli.py
git commit -m "feat: add CLI entry point to calendar_utils.py"
```

---

### Task 6: Make `review_page.py` callable as CLI

**Files:**
- Modify: `plugin/scripts/review_page.py`
- Modify: `tests/test_review_page.py`

The `/plan-content` command needs to generate the HTML review page from the command line by passing a calendar file path.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_review_page.py`:

```python
def test_cli_generate_from_calendar(tmp_path):
    """review_page CLI reads calendar + draft files and generates HTML."""
    # Create a calendar file
    calendar_content = """---
created_at: "2026-04-02 10:00"
period: "2026-04-03 → 2026-04-04"
posts_per_day: 1
status: generated
---

## 2026-04-03 (Thu) — 09:00
**Topic:** Topic A
**Platforms:** twitter, threads
**Image:** ai
**Drafts:**
- contents/2026-04-03_topic-a_tweet_twitter.md
- contents/2026-04-03_topic-a_post_threads.md
**Image file:** images/2026-04-03_topic-a_banner.png
"""
    contents_dir = tmp_path / "contents"
    contents_dir.mkdir()
    cal_path = contents_dir / "calendar-2026-04-02.md"
    cal_path.write_text(calendar_content)

    # Create draft files
    twitter_draft = """---
platform: twitter
type: tweet
topic: "Topic A"
status: draft
scheduled_at: "2026-04-03 09:00"
calendar: calendar-2026-04-02.md
created_at: "2026-04-02 10:00"
posted_at: ""
post_ids: []
has_images: true
images: []
---

Twitter content here.
"""
    (contents_dir / "2026-04-03_topic-a_tweet_twitter.md").write_text(twitter_draft)

    threads_draft = """---
platform: threads
type: post
topic: "Topic A"
status: draft
scheduled_at: "2026-04-03 09:00"
calendar: calendar-2026-04-02.md
created_at: "2026-04-02 10:00"
posted_at: ""
post_ids: []
has_images: true
images: []
---

Threads content here.
"""
    (contents_dir / "2026-04-03_topic-a_post_threads.md").write_text(threads_draft)

    output_path = str(contents_dir / "review.html")

    from scripts.review_page import main
    main(["--calendar", str(cal_path), "--output", output_path, "--project-dir", str(tmp_path)])

    assert os.path.exists(output_path)
    with open(output_path, "r") as f:
        html = f.read()

    assert "Topic A" in html
    assert "Twitter content here." in html
    assert "Threads content here." in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd plugin && python3 -m pytest ../tests/test_review_page.py::test_cli_generate_from_calendar -v`
Expected: FAIL — `AttributeError: module 'scripts.review_page' has no attribute 'main'`

- [ ] **Step 3: Add CLI entry point to `review_page.py`**

Append to the bottom of `plugin/scripts/review_page.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd plugin && python3 -m pytest ../tests/test_review_page.py::test_cli_generate_from_calendar -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `cd plugin && python3 -m pytest ../tests/ -v`
Expected: 56 passed

- [ ] **Step 6: Commit**

```bash
git add plugin/scripts/review_page.py tests/test_review_page.py
git commit -m "feat: add CLI entry point to review_page.py for calendar-based HTML generation"
```

---

### Task 7: Integration test — full plan-content flow

**Files:**
- Create: `tests/test_plan_content_integration.py`

- [ ] **Step 1: Write integration test**

Create `tests/test_plan_content_integration.py`:

```python
"""Integration test: calendar creation → draft parsing → review page generation.

Tests the full data flow without network calls. Verifies that calendar_utils,
draft parsing, and review_page work together correctly.
"""

import os
import sys
import tempfile

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_full_flow_calendar_to_review(tmp_path):
    """Full flow: write calendar → create drafts → generate review HTML."""
    from scripts.calendar_utils import write_calendar, parse_calendar, update_calendar_status
    from scripts.utils.draft import parse_draft, update_frontmatter
    from scripts.review_page import generate_review_html

    # Step 1: Create calendar
    metadata = {
        "created_at": "2026-04-02 10:00",
        "period": "2026-04-03 → 2026-04-04",
        "posts_per_day": 1,
        "status": "draft",
    }
    slots = [
        {
            "date": "2026-04-03",
            "day": "Thu",
            "time": "09:00",
            "topic": "Topic A",
            "platforms": ["twitter", "threads"],
            "image": "ai",
        },
    ]

    contents_dir = tmp_path / "contents"
    contents_dir.mkdir()
    cal_path = str(contents_dir / "calendar-2026-04-02.md")
    write_calendar(cal_path, metadata, slots)

    # Verify calendar was written correctly
    meta_check, slots_check = parse_calendar(cal_path)
    assert meta_check["status"] == "draft"
    assert len(slots_check) == 1

    # Step 2: Create draft files (simulating /generate-content)
    twitter_draft = """---
platform: twitter
type: tweet
topic: "Topic A"
status: draft
scheduled_at: "2026-04-03 09:00"
calendar: calendar-2026-04-02.md
created_at: "2026-04-02 10:00"
posted_at: ""
post_ids: []
has_images: false
images: []
---

A tweet about Topic A for testing.
"""
    twitter_path = str(contents_dir / "2026-04-03_topic-a_tweet_twitter.md")
    with open(twitter_path, "w") as f:
        f.write(twitter_draft)

    threads_draft = """---
platform: threads
type: post
topic: "Topic A"
status: draft
scheduled_at: "2026-04-03 09:00"
calendar: calendar-2026-04-02.md
created_at: "2026-04-02 10:00"
posted_at: ""
post_ids: []
has_images: false
images: []
---

A threads post about Topic A for testing.
"""
    threads_path = str(contents_dir / "2026-04-03_topic-a_post_threads.md")
    with open(threads_path, "w") as f:
        f.write(threads_draft)

    # Step 3: Update calendar with draft references
    slots[0]["drafts"] = [
        "contents/2026-04-03_topic-a_tweet_twitter.md",
        "contents/2026-04-03_topic-a_post_threads.md",
    ]
    slots[0]["image_file"] = "images/2026-04-03_topic-a_banner.png"
    metadata["status"] = "generated"
    write_calendar(cal_path, metadata, slots)

    # Step 4: Build review data and generate HTML
    _, gen_slots = parse_calendar(cal_path)
    review_slots = []
    for slot in gen_slots:
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
        for draft_ref in slot.get("drafts", []):
            full_path = str(tmp_path / draft_ref)
            if os.path.exists(full_path):
                _, parts = parse_draft(full_path)
                platform = os.path.basename(draft_ref).rsplit("_", 1)[-1].replace(".md", "")
                review_slot["drafts"][platform] = "\n\n".join(parts)
        review_slots.append(review_slot)

    review_path = str(contents_dir / "calendar-2026-04-02-review.html")
    generate_review_html(review_slots, review_path)

    # Verify HTML
    assert os.path.exists(review_path)
    with open(review_path, "r") as f:
        html = f.read()
    assert "Topic A" in html
    assert "A tweet about Topic A for testing." in html
    assert "A threads post about Topic A for testing." in html

    # Step 5: Simulate scheduling — update statuses
    update_calendar_status(cal_path, "scheduled")
    update_frontmatter(twitter_path, {"status": "scheduled"})
    update_frontmatter(threads_path, {"status": "scheduled"})

    # Verify final states
    meta_final, _ = parse_calendar(cal_path)
    assert meta_final["status"] == "scheduled"

    fm_tw, _ = parse_draft(twitter_path)
    assert fm_tw["status"] == "scheduled"
    assert fm_tw["scheduled_at"] == "2026-04-03 09:00"
    assert fm_tw["calendar"] == "calendar-2026-04-02.md"

    fm_th, _ = parse_draft(threads_path)
    assert fm_th["status"] == "scheduled"

    # Step 6: Cleanup review HTML
    os.unlink(review_path)
    assert not os.path.exists(review_path)
    # Calendar and drafts still exist
    assert os.path.exists(cal_path)
    assert os.path.exists(twitter_path)
    assert os.path.exists(threads_path)
```

- [ ] **Step 2: Run integration test**

Run: `cd plugin && python3 -m pytest ../tests/test_plan_content_integration.py -v`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `cd plugin && python3 -m pytest ../tests/ -v`
Expected: 57 passed

- [ ] **Step 4: Commit**

```bash
git add tests/test_plan_content_integration.py
git commit -m "test: add integration test for full plan-content flow"
```

---

## Summary

| Task | What | Tests Added |
|------|------|-------------|
| 1 | `post.py` accepts `scheduled` status | 1 |
| 2 | `calendar_utils.py` — parse, write, update | 4 |
| 3 | `review_page.py` — HTML generation | 3 |
| 4 | `plan-content.md` — slash command | 0 (markdown) |
| 5 | `calendar_utils.py` CLI | 2 |
| 6 | `review_page.py` CLI | 1 |
| 7 | Integration test | 1 |
| **Total** | | **12 new tests** |

Final expected test count: **57** (45 existing + 12 new).
