import os
import tempfile
import pytest
import yaml


def test_parse_draft_twitter_thread():
    """parse_draft returns frontmatter and list of tweet texts from ## Tweet N headings."""
    content = """---
platform: twitter
type: thread
topic: "AI Trends"
status: draft
created_at: "2026-03-30 14:00"
posted_at: ""
post_ids: []
has_images: false
images: []
---

## Tweet 1
First tweet content here.

## Tweet 2
Second tweet content here.

## Tweet 3
Third tweet content here.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        from scripts.utils.draft import parse_draft

        frontmatter, parts = parse_draft(path)
        assert frontmatter["platform"] == "twitter"
        assert frontmatter["type"] == "thread"
        assert frontmatter["status"] == "draft"
        assert len(parts) == 3
        assert parts[0] == "First tweet content here."
        assert parts[1] == "Second tweet content here."
        assert parts[2] == "Third tweet content here."
    finally:
        os.unlink(path)


def test_parse_draft_single_tweet():
    """parse_draft with no headings returns entire body as single item."""
    content = """---
platform: twitter
type: tweet
topic: "Quick update"
status: draft
created_at: "2026-03-30 14:00"
posted_at: ""
post_ids: []
has_images: false
images: []
---

Just a single tweet with no headings.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        from scripts.utils.draft import parse_draft

        frontmatter, parts = parse_draft(path)
        assert frontmatter["type"] == "tweet"
        assert len(parts) == 1
        assert parts[0] == "Just a single tweet with no headings."
    finally:
        os.unlink(path)


def test_parse_draft_invalid_format():
    """parse_draft returns None frontmatter for files without --- delimiters."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("No frontmatter here, just text.")
        path = f.name

    try:
        from scripts.utils.draft import parse_draft

        frontmatter, parts = parse_draft(path)
        assert frontmatter is None
        assert parts == []
    finally:
        os.unlink(path)


def test_parse_draft_reddit_submission():
    """parse_draft handles Reddit submission with ## Body heading."""
    content = """---
platform: reddit
type: submission
topic: "AI Trends"
status: draft
created_at: "2026-03-30 14:00"
posted_at: ""
post_ids: []
has_images: false
images: []
subreddit: "artificial"
title: "AI Trends 2026: What Changed"
---

## Body
A detailed analysis of how AI has evolved in 2026.

### Multi-modal Models
Long paragraph explaining the changes.

### Coding Agents
Another paragraph about coding agents.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        from scripts.utils.draft import parse_draft

        frontmatter, parts = parse_draft(path)
        assert frontmatter["platform"] == "reddit"
        assert frontmatter["subreddit"] == "artificial"
        assert frontmatter["title"] == "AI Trends 2026: What Changed"
        # Reddit body is returned as a single part
        assert len(parts) == 1
        assert "Multi-modal Models" in parts[0]
    finally:
        os.unlink(path)


def test_update_frontmatter():
    """update_frontmatter merges updates into existing YAML frontmatter."""
    content = """---
platform: twitter
type: thread
status: draft
post_ids: []
---

## Tweet 1
Hello world.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        from scripts.utils.draft import update_frontmatter, parse_draft

        update_frontmatter(path, {
            "status": "posted",
            "posted_at": "2026-03-30 15:00",
            "post_ids": ["123456"],
        })

        frontmatter, parts = parse_draft(path)
        assert frontmatter["status"] == "posted"
        assert frontmatter["posted_at"] == "2026-03-30 15:00"
        assert frontmatter["post_ids"] == ["123456"]
        assert frontmatter["platform"] == "twitter"  # preserved
        assert len(parts) == 1
        assert parts[0] == "Hello world."
    finally:
        os.unlink(path)


def test_resolve_image_paths_relative():
    """resolve_image_paths converts relative paths to absolute and preserves url."""
    from scripts.utils.draft import resolve_image_paths

    frontmatter = {
        "has_images": True,
        "images": [
            {"path": "images/banner.png", "url": "https://kie.ai/img/abc.png", "description": "A banner"},
        ],
    }
    draft_dir = "/project/contents"
    result = resolve_image_paths(frontmatter, draft_dir)
    assert len(result) == 1
    assert result[0]["path"] == "/project/images/banner.png"
    assert result[0]["url"] == "https://kie.ai/img/abc.png"


def test_resolve_image_paths_no_url():
    """resolve_image_paths returns empty url when image has no url field."""
    from scripts.utils.draft import resolve_image_paths

    frontmatter = {
        "has_images": True,
        "images": [
            {"path": "images/banner.png", "description": "A banner"},
        ],
    }
    draft_dir = "/project/contents"
    result = resolve_image_paths(frontmatter, draft_dir)
    assert len(result) == 1
    assert result[0]["path"] == "/project/images/banner.png"
    assert result[0]["url"] == ""


def test_resolve_image_paths_no_images():
    """resolve_image_paths returns empty list when no images."""
    from scripts.utils.draft import resolve_image_paths

    frontmatter = {"has_images": False, "images": []}
    result = resolve_image_paths(frontmatter, "/project/contents")
    assert result == []
