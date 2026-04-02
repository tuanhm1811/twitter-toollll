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
        assert "<style>" in html
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

        assert "11 characters" in html
    finally:
        os.unlink(output_path)


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
