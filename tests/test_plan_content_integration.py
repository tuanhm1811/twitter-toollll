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
