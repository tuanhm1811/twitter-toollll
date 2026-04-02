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
