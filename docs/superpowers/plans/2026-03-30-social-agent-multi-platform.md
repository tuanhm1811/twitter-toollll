# Social Agent Multi-Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the twitter-agent Claude Code plugin into social-agent supporting Twitter, Reddit, Threads, and Facebook with platform-specific content formatting and a unified `/post` command.

**Architecture:** Shared base + platform modules. Shared logic (parse draft, update frontmatter) in `utils/draft.py`. Each platform implements only its posting logic in `platforms/<name>.py`. Single entry point `post.py` routes by `platform` field in draft frontmatter.

**Tech Stack:** Python 3, tweepy (Twitter), praw (Reddit), requests (Threads/Facebook Meta API), pyyaml, Claude Code plugin system (markdown commands + Python scripts)

**Spec:** `docs/superpowers/specs/2026-03-30-social-agent-multi-platform-design.md`

---

## File Map

### Files to Create

| File | Responsibility |
|------|---------------|
| `plugin/scripts/utils/draft.py` | `parse_draft()`, `update_frontmatter()`, `resolve_image_paths()` — extracted from `post_twitter.py` |
| `plugin/scripts/post.py` | Unified entry point: reads draft, routes to platform module, updates frontmatter |
| `plugin/scripts/platforms/__init__.py` | Platform registry: maps platform name → module |
| `plugin/scripts/platforms/base.py` | `validate_platform_config()`, `format_result()` |
| `plugin/scripts/platforms/twitter.py` | `post()`, `validate_config()` — Twitter posting via tweepy |
| `plugin/scripts/platforms/reddit.py` | `post()`, `validate_config()` — Reddit posting via praw |
| `plugin/scripts/platforms/threads.py` | `post()`, `validate_config()` — Threads posting via Meta API |
| `plugin/scripts/platforms/facebook.py` | `post()`, `validate_config()` — Facebook posting via Graph API |
| `plugin/commands/post.md` | Unified `/post` command replacing `/post-twitter` |
| `tests/test_draft.py` | Tests for `utils/draft.py` |
| `tests/test_post.py` | Tests for `post.py` routing |
| `tests/test_platform_twitter.py` | Tests for Twitter platform module |
| `tests/test_platform_reddit.py` | Tests for Reddit platform module |
| `tests/test_platform_threads.py` | Tests for Threads platform module |
| `tests/test_platform_facebook.py` | Tests for Facebook platform module |
| `tests/test_config.py` | Tests for updated config loader |

### Files to Modify

| File | Changes |
|------|---------|
| `plugin/.claude-plugin/plugin.json` | name → `social-agent`, description updated |
| `plugin/scripts/utils/config.py` | Config path `.twitter-agent.yaml` → `.social-agent.yaml` |
| `plugin/scripts/generate_image.py` | Config default comment update |
| `plugin/scripts/requirements.txt` | Add `praw>=7.7.0` |
| `plugin/config.template.yaml` | New nested config structure with platform sections |
| `plugin/hooks/hooks.json` | All references `.twitter-agent.yaml` → `.social-agent.yaml`, check per-platform |
| `plugin/commands/setup.md` | Multi-platform setup flow with credential guides |
| `plugin/commands/init.md` | References update |
| `plugin/commands/summarize.md` | "Twitter" → "Social media" |
| `plugin/commands/generate-content.md` | Add `--platform` flag, platform-specific format rules |
| `plugin/commands/generate-image.md` | Minor reference update |
| `plugin/commands/import.md` | Reference update (if any) |
| `CLAUDE.md` | Update all references |

### Files to Delete

| File | Reason |
|------|--------|
| `plugin/scripts/post_twitter.py` | Replaced by `post.py` + `platforms/twitter.py` + `utils/draft.py` |
| `plugin/commands/post-twitter.md` | Replaced by `post.md` |

---

## Phase 0: Refactor & Rename

### Task 1: Extract `utils/draft.py` from `post_twitter.py`

**Files:**
- Create: `plugin/scripts/utils/draft.py`
- Test: `tests/test_draft.py`

- [ ] **Step 1: Write failing tests for `parse_draft`**

Create `tests/test_draft.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugin && python -m pytest ../tests/test_draft.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.utils.draft'`

- [ ] **Step 3: Write `utils/draft.py`**

Create `plugin/scripts/utils/draft.py`:

```python
"""Shared draft file parsing and frontmatter management.

Extracted from post_twitter.py to be reused across all platform modules.
"""

import os
import re

import yaml


def parse_draft(file_path):
    """Parse a draft markdown file into frontmatter dict and content parts.

    Content parts are split differently based on platform:
    - Twitter: split by "## Tweet N" headings
    - Threads: split by "## Post N" headings
    - Reddit: body after "## Body" heading returned as single part
    - Facebook: entire body returned as single part

    Returns:
        (frontmatter_dict, list_of_content_strings)
        Returns (None, []) if the file has no valid frontmatter.
    """
    with open(file_path, "r") as f:
        raw = f.read()

    match = re.match(r"^---\n(.*?)\n---\n(.*)", raw, re.DOTALL)
    if not match:
        return None, []

    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()

    if not body:
        return frontmatter, []

    platform = frontmatter.get("platform", "")

    if platform == "twitter":
        parts = re.split(r"^## Tweet \d+\s*\n", body, flags=re.MULTILINE)
        parts = [p.strip() for p in parts if p.strip()]
        if not parts:
            parts = [body]
    elif platform == "threads":
        parts = re.split(r"^## Post \d+\s*\n", body, flags=re.MULTILINE)
        parts = [p.strip() for p in parts if p.strip()]
        if not parts:
            parts = [body]
    elif platform == "reddit":
        body_match = re.split(r"^## Body\s*\n", body, flags=re.MULTILINE)
        if len(body_match) > 1:
            parts = [body_match[1].strip()]
        else:
            parts = [body]
    else:
        # Facebook and any unknown platform: entire body as one part
        parts = [body]

    return frontmatter, parts


def update_frontmatter(file_path, updates):
    """Update specific frontmatter fields in a draft file, preserving the body.

    Args:
        file_path: Path to the draft markdown file.
        updates: Dict of field names and new values to merge into frontmatter.
    """
    with open(file_path, "r") as f:
        raw = f.read()

    match = re.match(r"^---\n(.*?)\n---\n(.*)", raw, re.DOTALL)
    if not match:
        return

    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)

    frontmatter.update(updates)

    new_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip()
    with open(file_path, "w") as f:
        f.write(f"---\n{new_yaml}\n---\n{body}")


def resolve_image_paths(frontmatter, draft_dir):
    """Resolve image paths from frontmatter relative to the project root.

    Args:
        frontmatter: Parsed frontmatter dict.
        draft_dir: Absolute path to the directory containing the draft file.

    Returns:
        List of absolute image file paths.
    """
    project_dir = os.path.dirname(draft_dir)  # contents/ -> project root
    image_paths = []

    if frontmatter.get("has_images") and frontmatter.get("images"):
        for img in frontmatter["images"]:
            p = img.get("path", "") if isinstance(img, dict) else str(img)
            if p:
                if not os.path.isabs(p):
                    p = os.path.join(project_dir, p)
                image_paths.append(p)

    return image_paths
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugin && python -m pytest ../tests/test_draft.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Write tests for `update_frontmatter` and `resolve_image_paths`**

Append to `tests/test_draft.py`:

```python
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
    """resolve_image_paths converts relative paths to absolute using project root."""
    from scripts.utils.draft import resolve_image_paths

    frontmatter = {
        "has_images": True,
        "images": [
            {"path": "images/banner.png", "description": "A banner"},
        ],
    }
    # Simulate draft in /project/contents/
    draft_dir = "/project/contents"
    paths = resolve_image_paths(frontmatter, draft_dir)
    assert paths == ["/project/images/banner.png"]


def test_resolve_image_paths_no_images():
    """resolve_image_paths returns empty list when no images."""
    from scripts.utils.draft import resolve_image_paths

    frontmatter = {"has_images": False, "images": []}
    paths = resolve_image_paths(frontmatter, "/project/contents")
    assert paths == []
```

- [ ] **Step 6: Run all draft tests**

Run: `cd plugin && python -m pytest ../tests/test_draft.py -v`
Expected: All 7 tests PASS

- [ ] **Step 7: Commit**

```bash
git add plugin/scripts/utils/draft.py tests/test_draft.py
git commit -m "feat: extract draft parsing utils from post_twitter.py"
```

---

### Task 2: Create `platforms/twitter.py` — extract Twitter posting logic

**Files:**
- Create: `plugin/scripts/platforms/__init__.py`
- Create: `plugin/scripts/platforms/base.py`
- Create: `plugin/scripts/platforms/twitter.py`
- Test: `tests/test_platform_twitter.py`

- [ ] **Step 1: Write failing tests for Twitter platform module**

Create `tests/test_platform_twitter.py`:

```python
import os
import sys
from unittest.mock import MagicMock, patch

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_validate_config_valid():
    """validate_config returns None when all Twitter keys are present."""
    from scripts.platforms.twitter import validate_config

    config = {
        "twitter": {
            "api_key": "key",
            "api_secret": "secret",
            "access_token": "token",
            "access_secret": "asecret",
        }
    }
    assert validate_config(config) is None


def test_validate_config_missing_section():
    """validate_config returns error when twitter section is missing."""
    from scripts.platforms.twitter import validate_config

    assert validate_config({}) is not None
    assert "twitter" in validate_config({}).lower()


def test_validate_config_missing_key():
    """validate_config returns error when a key is empty."""
    from scripts.platforms.twitter import validate_config

    config = {
        "twitter": {
            "api_key": "key",
            "api_secret": "",
            "access_token": "token",
            "access_secret": "asecret",
        }
    }
    error = validate_config(config)
    assert error is not None
    assert "api_secret" in error


@patch("scripts.platforms.twitter.tweepy")
def test_post_single_tweet(mock_tweepy):
    """post() with a single content part posts one tweet."""
    from scripts.platforms.twitter import post

    mock_client = MagicMock()
    mock_client.create_tweet.return_value = MagicMock(
        data={"id": "111", "text": "Hello world"}
    )
    mock_tweepy.Client.return_value = mock_client

    config = {
        "twitter": {
            "api_key": "k",
            "api_secret": "s",
            "access_token": "t",
            "access_secret": "a",
        }
    }
    result = post(config, ["Hello world"])
    assert result["success"] is True
    assert result["post_ids"] == ["111"]
    mock_client.create_tweet.assert_called_once_with(text="Hello world")


@patch("scripts.platforms.twitter.tweepy")
def test_post_thread(mock_tweepy):
    """post() with multiple content parts posts a thread (each reply to previous)."""
    from scripts.platforms.twitter import post

    mock_client = MagicMock()
    mock_client.create_tweet.side_effect = [
        MagicMock(data={"id": "111", "text": "First"}),
        MagicMock(data={"id": "222", "text": "Second"}),
    ]
    mock_tweepy.Client.return_value = mock_client

    config = {
        "twitter": {
            "api_key": "k",
            "api_secret": "s",
            "access_token": "t",
            "access_secret": "a",
        }
    }
    result = post(config, ["First", "Second"])
    assert result["success"] is True
    assert result["post_ids"] == ["111", "222"]
    # Second tweet should reply to first
    calls = mock_client.create_tweet.call_args_list
    assert calls[1][1]["in_reply_to_tweet_id"] == "111"


@patch("scripts.platforms.twitter.tweepy")
def test_post_with_images(mock_tweepy):
    """post() uploads images via v1.1 API and attaches media IDs."""
    from scripts.platforms.twitter import post

    mock_client = MagicMock()
    mock_client.create_tweet.return_value = MagicMock(
        data={"id": "111", "text": "With image"}
    )
    mock_tweepy.Client.return_value = mock_client

    mock_api_v1 = MagicMock()
    mock_media = MagicMock()
    mock_media.media_id = 999
    mock_api_v1.media_upload.return_value = mock_media
    mock_tweepy.OAuth1UserHandler.return_value = MagicMock()
    mock_tweepy.API.return_value = mock_api_v1

    config = {
        "twitter": {
            "api_key": "k",
            "api_secret": "s",
            "access_token": "t",
            "access_secret": "a",
        }
    }
    result = post(config, ["With image"], images=["/path/to/img.png"])
    assert result["success"] is True
    mock_api_v1.media_upload.assert_called_once_with("/path/to/img.png")
    call_kwargs = mock_client.create_tweet.call_args[1]
    assert call_kwargs["media_ids"] == [999]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugin && python -m pytest ../tests/test_platform_twitter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.platforms'`

- [ ] **Step 3: Create `platforms/__init__.py`**

Create `plugin/scripts/platforms/__init__.py`:

```python
"""Platform modules for social media posting.

Each platform module implements:
    post(config, content_parts, images=None) -> dict
    validate_config(config) -> str | None
"""

PLATFORMS = {
    "twitter": "scripts.platforms.twitter",
    "reddit": "scripts.platforms.reddit",
    "threads": "scripts.platforms.threads",
    "facebook": "scripts.platforms.facebook",
}


def get_platform_module(platform_name):
    """Import and return the platform module for the given name.

    Returns None if platform is not supported.
    """
    module_path = PLATFORMS.get(platform_name)
    if not module_path:
        return None

    import importlib
    return importlib.import_module(module_path)
```

- [ ] **Step 4: Create `platforms/base.py`**

Create `plugin/scripts/platforms/base.py`:

```python
"""Shared utilities for platform modules."""


def validate_platform_config(config, platform_name, required_keys):
    """Check that a platform section exists in config with all required keys non-empty.

    Args:
        config: Full config dict.
        platform_name: e.g. "twitter", "reddit".
        required_keys: List of key names that must be non-empty strings.

    Returns:
        Error message string, or None if valid.
    """
    section = config.get(platform_name)
    if not section or not isinstance(section, dict):
        return f"No '{platform_name}' section in config. Run /setup {platform_name} to configure."

    for key in required_keys:
        if not section.get(key):
            return f"Missing '{platform_name}.{key}' in config. Run /setup {platform_name} to fix."

    return None
```

- [ ] **Step 5: Create `platforms/twitter.py`**

Create `plugin/scripts/platforms/twitter.py`:

```python
"""Twitter platform module — post tweets and threads via Twitter API v2."""

import os
import sys

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import tweepy

from scripts.platforms.base import validate_platform_config

REQUIRED_KEYS = ["api_key", "api_secret", "access_token", "access_secret"]


def validate_config(config):
    """Check Twitter credentials are present. Returns error string or None."""
    return validate_platform_config(config, "twitter", REQUIRED_KEYS)


def post(config, content_parts, images=None, frontmatter=None):
    """Post tweet or thread to Twitter.

    Args:
        config: Full config dict with 'twitter' section.
        content_parts: List of strings. 1 item = single tweet, 2+ = thread.
        images: Optional list of image file paths. Attached to first tweet.
        frontmatter: Draft frontmatter dict (unused for Twitter).

    Returns:
        dict with 'success', 'post_ids', and optionally 'error'.
    """
    tc = config["twitter"]
    post_ids = []

    try:
        client = tweepy.Client(
            consumer_key=tc["api_key"],
            consumer_secret=tc["api_secret"],
            access_token=tc["access_token"],
            access_token_secret=tc["access_secret"],
        )

        # Upload images via v1.1 API if provided
        media_ids = None
        if images:
            auth = tweepy.OAuth1UserHandler(
                consumer_key=tc["api_key"],
                consumer_secret=tc["api_secret"],
                access_token=tc["access_token"],
                access_token_secret=tc["access_secret"],
            )
            api_v1 = tweepy.API(auth)
            media_ids = []
            for path in images:
                media = api_v1.media_upload(path)
                media_ids.append(media.media_id)

        reply_to = None
        for i, text in enumerate(content_parts):
            kwargs = {"text": text}
            # Attach images only to first tweet
            if i == 0 and media_ids:
                kwargs["media_ids"] = media_ids
            if reply_to:
                kwargs["in_reply_to_tweet_id"] = reply_to

            response = client.create_tweet(**kwargs)
            post_id = response.data["id"]
            post_ids.append(post_id)
            reply_to = post_id

        return {"success": True, "post_ids": post_ids}

    except Exception as e:
        return {"success": False, "error": str(e), "post_ids": post_ids}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd plugin && python -m pytest ../tests/test_platform_twitter.py -v`
Expected: All 6 tests PASS

- [ ] **Step 7: Commit**

```bash
git add plugin/scripts/platforms/__init__.py plugin/scripts/platforms/base.py plugin/scripts/platforms/twitter.py tests/test_platform_twitter.py
git commit -m "feat: add Twitter platform module with shared base"
```

---

### Task 3: Create unified `post.py` entry point

**Files:**
- Create: `plugin/scripts/post.py`
- Test: `tests/test_post.py`

- [ ] **Step 1: Write failing tests for `post.py`**

Create `tests/test_post.py`:

```python
import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def _make_draft(platform="twitter", status="draft"):
    """Helper: create a temp draft file and return its path."""
    content = f"""---
platform: {platform}
type: thread
topic: "Test"
status: {status}
created_at: "2026-03-30 14:00"
posted_at: ""
post_ids: []
has_images: false
images: []
---

## Tweet 1
Hello world.
"""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    f.write(content)
    f.close()
    return f.name


@patch("scripts.platforms.twitter.tweepy")
@patch("scripts.utils.config.load_config")
def test_post_routes_to_twitter(mock_load_config, mock_tweepy):
    """post.py reads platform from frontmatter and routes to twitter module."""
    mock_load_config.return_value = {
        "twitter": {"api_key": "k", "api_secret": "s", "access_token": "t", "access_secret": "a"}
    }
    mock_client = MagicMock()
    mock_client.create_tweet.return_value = MagicMock(data={"id": "111", "text": "Hello"})
    mock_tweepy.Client.return_value = mock_client

    path = _make_draft("twitter")
    try:
        from scripts.post import main
        result = main(["--file", path])
        assert result["success"] is True
        assert result["post_ids"] == ["111"]
    finally:
        os.unlink(path)


@patch("scripts.utils.config.load_config")
def test_post_rejects_already_posted(mock_load_config):
    """post.py rejects drafts with status: posted."""
    mock_load_config.return_value = {"twitter": {"api_key": "k", "api_secret": "s", "access_token": "t", "access_secret": "a"}}

    path = _make_draft("twitter", status="posted")
    try:
        from scripts.post import main
        result = main(["--file", path])
        assert result["success"] is False
        assert "already posted" in result["error"].lower()
    finally:
        os.unlink(path)


@patch("scripts.utils.config.load_config")
def test_post_rejects_unsupported_platform(mock_load_config):
    """post.py returns error for unsupported platform."""
    mock_load_config.return_value = {}

    path = _make_draft("mastodon")
    try:
        from scripts.post import main
        result = main(["--file", path])
        assert result["success"] is False
        assert "unsupported" in result["error"].lower() or "mastodon" in result["error"].lower()
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugin && python -m pytest ../tests/test_post.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.post'`

- [ ] **Step 3: Write `post.py`**

Create `plugin/scripts/post.py`:

```python
#!/usr/bin/env python3
"""Unified entry point for posting content to any platform.

Reads a draft markdown file, determines the target platform from frontmatter,
routes to the correct platform module, posts, and updates the draft frontmatter.

Usage:
    python post.py --file <draft.md> [--config <config.yaml>]
"""

import argparse
import json
import os
import sys
from datetime import datetime

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

from scripts.utils.config import load_config
from scripts.utils.draft import parse_draft, update_frontmatter, resolve_image_paths
from scripts.platforms import get_platform_module


def post_from_file(file_path, config):
    """Read a draft file, post to the correct platform, update frontmatter."""
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    frontmatter, content_parts = parse_draft(file_path)

    if frontmatter is None:
        return {"success": False, "error": f"Invalid draft format (missing frontmatter): {file_path}"}

    if not content_parts:
        return {"success": False, "error": f"No content found in: {file_path}"}

    if frontmatter.get("status") == "posted":
        return {"success": False, "error": f"Already posted: {file_path}"}

    platform_name = frontmatter.get("platform")
    if not platform_name:
        return {"success": False, "error": f"No 'platform' field in frontmatter: {file_path}"}

    platform_module = get_platform_module(platform_name)
    if not platform_module:
        return {"success": False, "error": f"Unsupported platform: {platform_name}"}

    # Validate platform config
    config_error = platform_module.validate_config(config)
    if config_error:
        return {"success": False, "error": config_error}

    # Resolve images
    draft_dir = os.path.dirname(os.path.abspath(file_path))
    image_paths = resolve_image_paths(frontmatter, draft_dir)

    # Post
    result = platform_module.post(config, content_parts, images=image_paths or None, frontmatter=frontmatter)

    # Update frontmatter on success
    if result.get("success"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        update_frontmatter(file_path, {
            "status": "posted",
            "posted_at": now,
            "post_ids": result.get("post_ids", []),
        })
        result["file"] = file_path
        result["frontmatter_updated"] = True

    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Post content to social media platforms")
    parser.add_argument("--file", required=True, help="Draft markdown file to post")
    parser.add_argument("--config", help="Config file path (default: .social-agent.yaml)")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if config is None:
        result = {"success": False, "error": "Config file not found. Run /setup first."}
        print(json.dumps(result))
        return result

    result = post_from_file(args.file, config)
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugin && python -m pytest ../tests/test_post.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugin/scripts/post.py tests/test_post.py
git commit -m "feat: add unified post.py entry point with platform routing"
```

---

### Task 4: Rename plugin and update config

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json`
- Modify: `plugin/scripts/utils/config.py`
- Modify: `plugin/config.template.yaml`
- Modify: `plugin/scripts/generate_image.py`
- Modify: `plugin/scripts/requirements.txt`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for new config path and nested structure**

Create `tests/test_config.py`:

```python
import os
import sys
import tempfile

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import yaml


def test_get_config_path_returns_social_agent():
    """get_config_path returns .social-agent.yaml in CWD."""
    from scripts.utils.config import get_config_path

    path = get_config_path()
    assert path.endswith(".social-agent.yaml")


def test_load_config_nested_structure():
    """load_config correctly loads nested platform credentials."""
    from scripts.utils.config import load_config

    config_data = {
        "kie_api_key": "test-key",
        "twitter": {
            "api_key": "tk",
            "api_secret": "ts",
            "access_token": "tt",
            "access_secret": "ta",
        },
        "reddit": {
            "client_id": "rc",
            "client_secret": "rs",
            "username": "ru",
            "password": "rp",
        },
        "auto_post": False,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        path = f.name

    try:
        config = load_config(path)
        assert config["kie_api_key"] == "test-key"
        assert config["twitter"]["api_key"] == "tk"
        assert config["reddit"]["client_id"] == "rc"
        assert config["auto_post"] is False
    finally:
        os.unlink(path)


def test_load_config_missing_file():
    """load_config returns None for non-existent file."""
    from scripts.utils.config import load_config

    result = load_config("/nonexistent/path/config.yaml")
    assert result is None
```

- [ ] **Step 2: Run tests to verify `test_get_config_path_returns_social_agent` fails**

Run: `cd plugin && python -m pytest ../tests/test_config.py -v`
Expected: `test_get_config_path_returns_social_agent` FAILS (still returns `.twitter-agent.yaml`)

- [ ] **Step 3: Update `config.py`**

Edit `plugin/scripts/utils/config.py` — change `.twitter-agent.yaml` to `.social-agent.yaml`:

```python
import os
import yaml


def get_config_path():
    """Return the config file path in the current working directory."""
    return os.path.join(os.getcwd(), ".social-agent.yaml")


def load_config(path=None):
    """Load config from a YAML file.

    Returns the parsed YAML dict, or None if file doesn't exist.
    """
    if path is None:
        path = get_config_path()

    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        content = f.read().strip()

    if not content:
        return {}

    return yaml.safe_load(content) or {}


def save_config(config, path=None):
    """Save config dict as a YAML file."""
    if path is None:
        path = get_config_path()

    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)

    with open(path, "w") as f:
        f.write(yaml_str)
```

- [ ] **Step 4: Run config tests**

Run: `cd plugin && python -m pytest ../tests/test_config.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Update `plugin.json`**

Edit `plugin/.claude-plugin/plugin.json`:

```json
{
  "name": "social-agent",
  "version": "2.0.0",
  "description": "Manage social media content creation from knowledge bases — summarization, content generation, image generation, and posting to Twitter, Reddit, Threads, and Facebook."
}
```

- [ ] **Step 6: Update `config.template.yaml`**

Replace `plugin/config.template.yaml`:

```yaml
# Social Agent Configuration
# Copy this to .social-agent.yaml in your project directory

# Required: kie.ai API key (for image generation)
kie_api_key: ""

# Platform credentials — only fill platforms you use

twitter:
  api_key: ""
  api_secret: ""
  access_token: ""
  access_secret: ""

reddit:
  client_id: ""
  client_secret: ""
  username: ""
  password: ""

threads:
  access_token: ""

facebook:
  page_access_token: ""
  page_id: ""

# Optional settings
auto_post: false  # skip confirmation before posting
```

- [ ] **Step 7: Update `generate_image.py` default config comment**

In `plugin/scripts/generate_image.py`, change line 136:

```python
    parser.add_argument("--config", help="Config file path (default: .social-agent.yaml)")
```

- [ ] **Step 8: Update `requirements.txt`**

Replace `plugin/scripts/requirements.txt`:

```
requests>=2.28.0
tweepy>=4.14.0
praw>=7.7.0
pyyaml>=6.0
```

- [ ] **Step 9: Run all tests**

Run: `cd plugin && python -m pytest ../tests/ -v`
Expected: All tests PASS

- [ ] **Step 10: Commit**

```bash
git add plugin/.claude-plugin/plugin.json plugin/scripts/utils/config.py plugin/config.template.yaml plugin/scripts/generate_image.py plugin/scripts/requirements.txt tests/test_config.py
git commit -m "feat: rename plugin to social-agent with nested config structure"
```

---

### Task 5: Update all commands for rename

**Files:**
- Modify: `plugin/commands/setup.md`
- Modify: `plugin/commands/init.md`
- Modify: `plugin/commands/summarize.md`
- Modify: `plugin/commands/generate-content.md`
- Modify: `plugin/commands/generate-image.md`
- Create: `plugin/commands/post.md`
- Delete: `plugin/commands/post-twitter.md`
- Modify: `plugin/hooks/hooks.json`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Create `/post` command**

Create `plugin/commands/post.md`:

```markdown
---
description: Post content to social media — publish drafts to Twitter, Reddit, Threads, or Facebook
argument-hint: [draft-file|list]
---

Publish draft content to the correct social media platform based on the draft's `platform` frontmatter field.

## Setup

1. Read config from `.social-agent.yaml` in the current directory to get `auto_post`.
2. Check that `./contents/` directory exists. If not, tell user: "No contents/ directory found. Run `/setup` or `/init` first."

## Actions

### Post a draft (default or with file argument)

1. **Select draft**:
   - If a file argument is given, use that file.
   - If no argument, find the most recent `.md` file in `./contents/` with `status: draft`.
   - If no drafts found, tell user to run `/generate-content` first.

2. **Read and display draft**: Show the full content (text + any linked images) to the user. Show which platform it will be posted to.

3. **Confirm** (unless `auto_post: true` in config):
   - Ask: "Ready to post this to [platform]? (yes/no)"
   - If no, stop and tell user they can edit with `/generate-content edit <file>`.

4. **Post**: The script handles reading the draft, routing to the correct platform, posting, and updating frontmatter in one step.

   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/post.py \
     --file "<path to draft .md file>" \
     --config .social-agent.yaml
   ```

5. **Handle result**:
   - Parse JSON output.
   - If `success: true` and `frontmatter_updated: true`:
     - The script already updated the draft frontmatter (status, posted_at, post_ids).
     - Confirm with platform-specific URL:
       - Twitter: "Posted! Tweet URL: https://twitter.com/i/status/<post_id>"
       - Reddit: "Posted! Reddit URL: https://reddit.com/<post_id>"
       - Threads: "Posted! Threads post ID: <post_id>"
       - Facebook: "Posted! Facebook post ID: <post_id>"
   - If `success: false`:
     - Check if error is a network/proxy/sandbox restriction (403 Forbidden, tunnel, connection refused, proxy error).
     - If **network/sandbox error**: follow the "Sandbox Fallback" section below.
     - Otherwise show error message and suggest fixes (rate limit — wait, auth error — re-run `/setup`).

## Sandbox Fallback

When running inside the Claude desktop app, outbound network requests are blocked by the sandbox. When a network/proxy error is detected:

1. **Generate a ready-to-run shell script** at `./post_draft.sh`:

   ```bash
   #!/bin/bash
   cd "<user's project directory>"
   python "<absolute path to plugin>/scripts/post.py" \
     --file "<path to draft .md file>" \
     --config .social-agent.yaml
   ```

   Make it executable: `chmod +x ./post_draft.sh`

2. **Tell the user**:
   > The Claude desktop app blocks outbound network requests. I've generated `post_draft.sh` with the posting command.
   >
   > Run this in your terminal:
   >
   > ```bash
   > ./post_draft.sh
   > ```
   >
   > The script will post and update the draft file automatically. Paste the JSON output back here to confirm.

3. **When user pastes JSON output back**:
   - Parse the JSON result.
   - If `success: true`: the draft frontmatter is already updated by the script. Confirm with post URL.
   - If `success: false`: show the error and suggest fixes.
   - Clean up: remove `./post_draft.sh`.

### `list`

1. List all `.md` files in `./contents/` with `status: draft`.
2. Group by platform, then show: filename, type, topic, created_at, has_images.
3. If no drafts, tell user to run `/generate-content`.
4. Example output:
   ```
   Twitter:
     - 2026-03-30_ai-trends_thread_twitter.md — thread — "AI Trends" — no images

   Reddit:
     - 2026-03-30_ai-trends_submission_reddit.md — submission — "AI Trends" — r/artificial

   No drafts for: Threads, Facebook
   ```
```

- [ ] **Step 2: Update `/setup` command**

Replace `plugin/commands/setup.md`:

```markdown
---
description: Configure Social Agent API keys and preferences
argument-hint: [platform]
---

Walk the user through configuring their Social Agent project. Store config at `.social-agent.yaml` in the current directory.

## Process

1. **Check for existing config**: Read `.social-agent.yaml` in the current directory. If it exists, show current config (mask API keys — show only last 4 characters) and ask if user wants to update.

2. **If a platform argument is given** (e.g., `/setup twitter`), skip to that platform's credential collection (step 4). Only update that platform's section in the config.

3. **Collect kie.ai API key** using AskUserQuestion:
   - "Enter your kie.ai API key (for image generation, get it from https://kie.ai/api-key)."

4. **Ask which platforms to configure**:
   - "Which platforms do you want to configure? (twitter, reddit, threads, facebook — you can pick multiple, comma-separated)"

5. **For each selected platform**, collect credentials one at a time using AskUserQuestion:

   **Twitter:**
   - First show guide: "To get Twitter API credentials: 1) Go to https://developer.twitter.com/en/portal/dashboard 2) Create a project and app 3) Under 'Keys and tokens', generate API Key, API Secret, Access Token, and Access Token Secret 4) Make sure your app has Read and Write permissions"
   - Then collect: API Key, API Secret, Access Token, Access Token Secret

   **Reddit:**
   - First show guide: "To get Reddit API credentials: 1) Go to https://www.reddit.com/prefs/apps 2) Click 'create another app...' at the bottom 3) Choose 'script' type 4) Set redirect URI to http://localhost:8080 5) Note the client ID (under app name) and client secret"
   - Then collect: Client ID, Client Secret, Reddit Username, Reddit Password

   **Threads:**
   - First show guide: "To get Threads API access: 1) Go to https://developers.facebook.com/ 2) Create an app with 'Threads API' product 3) In Threads API settings, generate a long-lived access token 4) Required permissions: threads_basic, threads_content_publish"
   - Then collect: Access Token

   **Facebook:**
   - First show guide: "To get Facebook Page access: 1) Go to https://developers.facebook.com/ 2) Create an app with 'Facebook Login' product 3) Get a Page Access Token via Graph API Explorer (https://developers.facebook.com/tools/explorer/) 4) Select your Page and request pages_manage_posts permission 5) Get your Page ID from your Facebook Page's About section"
   - Then collect: Page Access Token, Page ID

6. **Collect preferences**:
   - "Should posts be published without confirmation? (yes/no, default: no)"

7. **Write config file**: Save all values to `.social-agent.yaml` in the current directory as plain YAML:

```yaml
kie_api_key: <value>

twitter:
  api_key: <value>
  api_secret: <value>
  access_token: <value>
  access_secret: <value>

reddit:
  client_id: <value>
  client_secret: <value>
  username: <value>
  password: <value>

threads:
  access_token: <value>

facebook:
  page_access_token: <value>
  page_id: <value>

auto_post: <value>
```

Only include platform sections that the user configured. Preserve existing sections when updating a single platform.

8. **Create project directories** if they don't exist: `knowledges/`, `contents/`, `images/`.

9. **Install Python dependencies**: Run `pip install -r ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt`

10. **Warn about .gitignore**: If a `.gitignore` file exists, check if `.social-agent.yaml` is listed. If not, suggest adding it: "Consider adding `.social-agent.yaml` to your .gitignore to avoid committing API keys."

11. **Confirm**: "Setup complete! Configured platforms: [list]. Add knowledge files to ./knowledges/ or use `/import <file>` to bring in files."
```

- [ ] **Step 3: Update `/init` command**

Edit `plugin/commands/init.md` — replace all content:

```markdown
---
description: Initialize current directory as a Social Agent project
---

Initialize the current working directory as a Social Agent project.

## Process

1. Check if `./knowledges/`, `./contents/`, and `./images/` directories already exist. If all exist, tell user: "Project already initialized."

2. Create directories:
   - `./knowledges/` — for imported knowledge files
   - `./contents/` — for generated social media content (.md drafts)
   - `./images/` — for generated images (banners, etc.)

3. Show the expected project structure:
   ```
   project/
   ├── .social-agent.yaml     # Config (run /setup)
   ├── knowledges/             # Knowledge files
   ├── contents/               # Content drafts (Twitter, Reddit, Threads, Facebook)
   ├── images/                 # Generated images
   └── summary.md              # Knowledge summary
   ```

4. Check if `.social-agent.yaml` exists in the current directory. If not, suggest: "Run `/setup` to configure your API keys."

5. Confirm: "Project initialized. Add knowledge files to ./knowledges/ or use `/import <file>` to bring in files and URLs."
```

- [ ] **Step 4: Update `/summarize` command**

In `plugin/commands/summarize.md`, change line 39 (`Suggested Content Angles` section description):

Replace `Twitter content angle` with `Social media content angle` in the template:

```
## Suggested Content Angles
- Angle 1: description of potential social media content angle
- Angle 2: description of potential social media content angle
```

And update the confirm message at line 45 from referencing Twitter to general social media.

- [ ] **Step 5: Update `/generate-content` command**

Replace `plugin/commands/generate-content.md`:

```markdown
---
description: Generate social media post drafts from project knowledge
argument-hint: --platform <name> [topic] | list | edit <file>
---

Create social media post drafts from the current project's knowledge summary, formatted for the target platform.

## Setup

1. Check that `./contents/` directory exists. If not, tell user: "No contents/ directory found. Run `/setup` or `/init` first."

## Content File Template

All content drafts are saved as `.md` files in `./contents/` with the following format:

### File Naming Convention

```
YYYY-MM-DD_<topic-slug>_<type>_<platform>.md
```

Examples:
- `2026-03-30_ai-trends_thread_twitter.md`
- `2026-03-30_ai-trends_submission_reddit.md`
- `2026-03-30_ai-trends_post_facebook.md`
- `2026-03-30_ai-trends_thread_threads.md`

### File Content Template

```markdown
---
platform: twitter | reddit | threads | facebook
type: tweet | thread | post | submission
topic: "Short topic description"
status: draft | posted
created_at: "YYYY-MM-DD HH:MM"
posted_at: ""
post_ids: []
has_images: false
images:
  - path: ""
    description: ""
# Reddit-specific (include only for reddit)
subreddit: ""
title: ""
# Facebook-specific (include only for facebook)
visibility: "public"
---

[Content body — format depends on platform]
```

### Platform-Specific Body Formats

**Twitter** (type: tweet or thread):
- Max 280 characters per tweet
- Single tweet: plain text body
- Thread: split into `## Tweet 1`, `## Tweet 2`, etc.
- 3-7 tweets per thread recommended

**Reddit** (type: submission):
- `title` field in frontmatter (max 300 characters)
- `subreddit` field in frontmatter (target subreddit, without r/ prefix)
- Body under `## Body` heading, full markdown supported
- No character limit on body

**Threads** (type: post or thread):
- Max 500 characters per post
- Single post: plain text body
- Thread: split into `## Post 1`, `## Post 2`, etc.
- 3-7 posts per thread recommended

**Facebook** (type: post):
- No practical character limit
- Entire body is one post, plain text
- `visibility` field: "public" (default)

## Actions

### Generate new content (`--platform <name> [topic]`)

1. `--platform` is required. If not provided, tell user: "Please specify a platform: `/generate-content --platform twitter|reddit|threads|facebook [topic]`"
2. Read `./summary.md`. If it doesn't exist, tell user to run `/summarize` first.
3. If a topic argument was given, focus content on that topic from the summary.
4. If no topic, pick the most compelling angle from "Suggested Content Angles".
5. Generate content following the platform-specific format rules above. Choose the best type for the platform:
   - **Twitter**: tweet (concise facts) or thread (explanations, 3-7 tweets)
   - **Reddit**: submission (always — pick appropriate subreddit, write compelling title)
   - **Threads**: post (short updates) or thread (longer explanations, 3-7 posts)
   - **Facebook**: post (always — can be longer form)
6. Save to `./contents/` using the file naming convention.
7. Confirm: "Draft created at `<path>`. Review it, then use `/generate-image` for visuals or `/post` to publish."

### `list`

1. List all `.md` files in `./contents/`.
2. For each, read the frontmatter and display: filename, platform, type, topic, status, created_at, has_images.
3. Group by platform, then by status (drafts first, then posted).
4. Show a summary like:
   ```
   Twitter:
     Drafts:
       - 2026-03-30_ai-trends_thread_twitter.md — thread — "AI Trends 2026" — no images
     Posted:
       - 2026-03-29_ml-basics_tweet_twitter.md — tweet — "ML Basics" — posted 2026-03-29

   Reddit:
     Drafts:
       - 2026-03-30_ai-trends_submission_reddit.md — submission — "AI Trends" — r/artificial
   ```

### `edit <file>`

1. Read the specified draft file.
2. Show current content to user.
3. Ask user what changes they want.
4. Apply changes and save.
5. Confirm: "Draft updated."
```

- [ ] **Step 6: Update `/generate-image` command**

In `plugin/commands/generate-image.md`, update line 7 to remove Twitter-specific wording:

Change: `Generate banner images for Twitter post drafts using kie.ai image generation API.`
To: `Generate banner images for social media post drafts using kie.ai image generation API.`

And update the confirm reference at line 56 from `/post-twitter` to `/post`.

- [ ] **Step 7: Update hooks.json**

Replace `plugin/hooks/hooks.json`:

```json
{
  "description": "Social Agent session startup hooks",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Perform startup checks for the Social Agent plugin:\n\n1. **Config check**: Check if `.social-agent.yaml` exists in the current working directory. If it does NOT exist, inform the user: 'Social Agent plugin is not configured for this project. Run /setup to initialize.' If it exists, read its YAML content and list which platforms are configured (have non-empty credentials) and which are not. Example: 'Configured platforms: Twitter, Reddit. Not configured: Threads, Facebook.'\n\n2. **Project structure check and auto-fix**: Check if the following directories exist in the current working directory:\n   - `knowledges/` — for knowledge files\n   - `contents/` — for generated social media content (.md files)\n   - `images/` — for generated images\n\n   **If any directory is missing, automatically create it.** Inform the user which directories were created.\n\n3. **Auto-organize misplaced files**: After ensuring directories exist, check for files in the project root that belong in subdirectories:\n   - Move any `.pdf`, `.txt`, `.csv`, `.json`, `.doc`, `.docx`, `.xls`, `.xlsx` files from the project root into `knowledges/`\n   - Move any `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg` image files from the project root into `images/`\n   - Do NOT move `.yaml`, `.md` (at root level like summary.md), `.gitignore`, or other config files\n\n   If any files were moved, inform the user: 'Auto-organized: moved N file(s) to their correct directories.' and list which files were moved where.\n\n   Expected project structure:\n   ```\n   project/\n   ├── .social-agent.yaml\n   ├── knowledges/\n   ├── contents/\n   ├── images/\n   └── summary.md\n   ```"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 8: Delete old `post-twitter.md` and `post_twitter.py`**

```bash
git rm plugin/commands/post-twitter.md
git rm plugin/scripts/post_twitter.py
```

- [ ] **Step 9: Update `CLAUDE.md`**

Update all references in `CLAUDE.md`:
- `twitter-agent` → `social-agent`
- `.twitter-agent.yaml` → `.social-agent.yaml`
- `post_twitter.py` → `post.py` + `platforms/twitter.py`
- `post-twitter.md` → `post.md`
- Update the repo layout tree
- Update config system description
- Update the testing section

- [ ] **Step 10: Run all tests**

Run: `cd plugin && python -m pytest ../tests/ -v`
Expected: All tests PASS

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -m "feat: rename to social-agent, update all commands and hooks for multi-platform"
```

---

### Task 6: Phase 1 — Verify Twitter end-to-end on new architecture

**Files:** No new files — verification only.

- [ ] **Step 1: Install dependencies**

```bash
cd plugin && pip install -r scripts/requirements.txt
```

- [ ] **Step 2: Test with user — setup Twitter credentials**

Run `/setup twitter` with the user. Walk through getting Twitter API credentials from developer.twitter.com. Save to `.social-agent.yaml`.

- [ ] **Step 3: Test with user — generate Twitter content**

Run `/generate-content --platform twitter "test topic"`. Verify:
- File created in `contents/` with correct naming: `YYYY-MM-DD_<topic>_<type>_twitter.md`
- Frontmatter has `platform: twitter`
- Content follows 280 char/tweet limit

- [ ] **Step 4: Test with user — post to Twitter**

Run `/post <draft-file>`. Verify:
- Script reads `platform: twitter` from frontmatter
- Routes to `platforms/twitter.py`
- Posts successfully
- Frontmatter updated with `status: posted`, `posted_at`, `post_ids`

- [ ] **Step 5: Commit verification**

```bash
git commit --allow-empty -m "chore: Phase 1 complete — Twitter verified on new architecture"
```

---

## Phase 2: Reddit

### Task 7: Create `platforms/reddit.py`

**Files:**
- Create: `plugin/scripts/platforms/reddit.py`
- Test: `tests/test_platform_reddit.py`

- [ ] **Step 1: Write failing tests for Reddit platform**

Create `tests/test_platform_reddit.py`:

```python
import os
import sys
from unittest.mock import MagicMock, patch

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_validate_config_valid():
    """validate_config returns None when all Reddit keys are present."""
    from scripts.platforms.reddit import validate_config

    config = {
        "reddit": {
            "client_id": "cid",
            "client_secret": "csecret",
            "username": "user",
            "password": "pass",
        }
    }
    assert validate_config(config) is None


def test_validate_config_missing_section():
    """validate_config returns error when reddit section is missing."""
    from scripts.platforms.reddit import validate_config

    error = validate_config({})
    assert error is not None
    assert "reddit" in error.lower()


def test_validate_config_missing_key():
    """validate_config returns error when a required key is empty."""
    from scripts.platforms.reddit import validate_config

    config = {
        "reddit": {
            "client_id": "cid",
            "client_secret": "",
            "username": "user",
            "password": "pass",
        }
    }
    error = validate_config(config)
    assert error is not None
    assert "client_secret" in error


@patch("scripts.platforms.reddit.praw")
def test_post_submission(mock_praw):
    """post() creates a Reddit submission with title and body."""
    from scripts.platforms.reddit import post

    mock_reddit = MagicMock()
    mock_subreddit = MagicMock()
    mock_submission = MagicMock()
    mock_submission.id = "abc123"
    mock_submission.url = "https://reddit.com/r/test/comments/abc123/title"
    mock_subreddit.submit.return_value = mock_submission
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.Reddit.return_value = mock_reddit

    config = {
        "reddit": {
            "client_id": "cid",
            "client_secret": "csecret",
            "username": "user",
            "password": "pass",
        }
    }
    frontmatter = {
        "platform": "reddit",
        "subreddit": "test",
        "title": "Test Title",
    }
    result = post(config, ["This is the body text."], frontmatter=frontmatter)
    assert result["success"] is True
    assert result["post_ids"] == ["abc123"]
    assert result["url"] == "https://reddit.com/r/test/comments/abc123/title"
    mock_subreddit.submit.assert_called_once_with(
        title="Test Title",
        selftext="This is the body text.",
    )


@patch("scripts.platforms.reddit.praw")
def test_post_submission_with_image(mock_praw):
    """post() creates a Reddit image submission when images provided."""
    from scripts.platforms.reddit import post

    mock_reddit = MagicMock()
    mock_subreddit = MagicMock()
    mock_submission = MagicMock()
    mock_submission.id = "img456"
    mock_submission.url = "https://reddit.com/r/test/comments/img456/title"
    mock_subreddit.submit_image.return_value = mock_submission
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.Reddit.return_value = mock_reddit

    config = {
        "reddit": {
            "client_id": "cid",
            "client_secret": "csecret",
            "username": "user",
            "password": "pass",
        }
    }
    frontmatter = {
        "platform": "reddit",
        "subreddit": "test",
        "title": "Image Post",
    }
    result = post(config, ["Body text."], images=["/path/to/img.png"], frontmatter=frontmatter)
    assert result["success"] is True
    assert result["post_ids"] == ["img456"]


@patch("scripts.platforms.reddit.praw")
def test_post_missing_subreddit(mock_praw):
    """post() returns error when subreddit is missing from frontmatter."""
    from scripts.platforms.reddit import post

    config = {
        "reddit": {
            "client_id": "cid",
            "client_secret": "csecret",
            "username": "user",
            "password": "pass",
        }
    }
    frontmatter = {
        "platform": "reddit",
        "title": "No Sub",
    }
    result = post(config, ["Body."], frontmatter=frontmatter)
    assert result["success"] is False
    assert "subreddit" in result["error"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugin && python -m pytest ../tests/test_platform_reddit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.platforms.reddit'`

- [ ] **Step 3: Write `platforms/reddit.py`**

Create `plugin/scripts/platforms/reddit.py`:

```python
"""Reddit platform module — post submissions via Reddit API using praw."""

import os
import sys

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import praw

from scripts.platforms.base import validate_platform_config

REQUIRED_KEYS = ["client_id", "client_secret", "username", "password"]


def validate_config(config):
    """Check Reddit credentials are present. Returns error string or None."""
    return validate_platform_config(config, "reddit", REQUIRED_KEYS)


def post(config, content_parts, images=None, frontmatter=None):
    """Post a submission to Reddit.

    Args:
        config: Full config dict with 'reddit' section.
        content_parts: List of strings. For Reddit, first item is the body.
        images: Optional list of image file paths. If provided, creates image post.
        frontmatter: Draft frontmatter dict with 'subreddit' and 'title' fields.

    Returns:
        dict with 'success', 'post_ids', 'url', and optionally 'error'.
    """
    frontmatter = frontmatter or {}
    subreddit_name = frontmatter.get("subreddit", "")
    title = frontmatter.get("title", "")

    if not subreddit_name:
        return {"success": False, "error": "Missing 'subreddit' in draft frontmatter."}

    if not title:
        return {"success": False, "error": "Missing 'title' in draft frontmatter."}

    rc = config["reddit"]
    body = content_parts[0] if content_parts else ""

    try:
        reddit = praw.Reddit(
            client_id=rc["client_id"],
            client_secret=rc["client_secret"],
            username=rc["username"],
            password=rc["password"],
            user_agent=f"social-agent:v2.0.0 (by /u/{rc['username']})",
        )
        subreddit = reddit.subreddit(subreddit_name)

        if images:
            submission = subreddit.submit_image(
                title=title,
                image_path=images[0],
            )
        else:
            submission = subreddit.submit(
                title=title,
                selftext=body,
            )

        return {
            "success": True,
            "post_ids": [submission.id],
            "url": submission.url,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugin && python -m pytest ../tests/test_platform_reddit.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Run all tests**

Run: `cd plugin && python -m pytest ../tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add plugin/scripts/platforms/reddit.py tests/test_platform_reddit.py
git commit -m "feat: add Reddit platform module with praw"
```

---

### Task 8: Phase 2 — Verify Reddit end-to-end with user

**Files:** No new files — verification only.

- [ ] **Step 1: Install praw**

```bash
pip install praw>=7.7.0
```

- [ ] **Step 2: Test with user — setup Reddit credentials**

Run `/setup reddit` with the user. Walk through creating a Reddit app at reddit.com/prefs/apps.

- [ ] **Step 3: Test with user — generate Reddit content**

Run `/generate-content --platform reddit "test topic"`. Verify:
- File created with `_submission_reddit.md` naming
- Frontmatter has `platform: reddit`, `subreddit`, `title`
- Body under `## Body` heading, full markdown

- [ ] **Step 4: Test with user — post to Reddit**

Run `/post <draft-file>`. Verify:
- Routes to `platforms/reddit.py`
- Posts to correct subreddit
- Returns URL
- Frontmatter updated

- [ ] **Step 5: Commit verification**

```bash
git commit --allow-empty -m "chore: Phase 2 complete — Reddit verified"
```

---

## Phase 3: Threads

### Task 9: Create `platforms/threads.py`

**Files:**
- Create: `plugin/scripts/platforms/threads.py`
- Test: `tests/test_platform_threads.py`

- [ ] **Step 1: Write failing tests for Threads platform**

Create `tests/test_platform_threads.py`:

```python
import os
import sys
from unittest.mock import MagicMock, patch

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_validate_config_valid():
    """validate_config returns None when Threads access token is present."""
    from scripts.platforms.threads import validate_config

    config = {"threads": {"access_token": "token123"}}
    assert validate_config(config) is None


def test_validate_config_missing():
    """validate_config returns error when threads section is missing."""
    from scripts.platforms.threads import validate_config

    error = validate_config({})
    assert error is not None
    assert "threads" in error.lower()


@patch("scripts.platforms.threads.requests")
def test_post_single(mock_requests):
    """post() creates a single Threads post."""
    from scripts.platforms.threads import post

    # Mock create container
    mock_create_resp = MagicMock()
    mock_create_resp.status_code = 200
    mock_create_resp.json.return_value = {"id": "container_1"}

    # Mock publish
    mock_publish_resp = MagicMock()
    mock_publish_resp.status_code = 200
    mock_publish_resp.json.return_value = {"id": "post_111"}

    mock_requests.post.side_effect = [mock_create_resp, mock_publish_resp]

    config = {"threads": {"access_token": "token123"}}
    result = post(config, ["Hello from Threads!"])
    assert result["success"] is True
    assert result["post_ids"] == ["post_111"]


@patch("scripts.platforms.threads.requests")
def test_post_thread(mock_requests):
    """post() creates a Threads thread (multiple posts)."""
    from scripts.platforms.threads import post

    # Each post in thread needs: create container, publish
    # Thread: create containers for each, then create carousel, then publish
    responses = []
    # Container for post 1
    responses.append(MagicMock(status_code=200, json=MagicMock(return_value={"id": "c1"})))
    # Container for post 2
    responses.append(MagicMock(status_code=200, json=MagicMock(return_value={"id": "c2"})))
    # Publish post 1
    responses.append(MagicMock(status_code=200, json=MagicMock(return_value={"id": "p1"})))
    # Publish post 2 (reply to p1)
    responses.append(MagicMock(status_code=200, json=MagicMock(return_value={"id": "p2"})))

    mock_requests.post.side_effect = responses

    config = {"threads": {"access_token": "token123"}}
    result = post(config, ["First post", "Second post"])
    assert result["success"] is True
    assert len(result["post_ids"]) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugin && python -m pytest ../tests/test_platform_threads.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.platforms.threads'`

- [ ] **Step 3: Write `platforms/threads.py`**

Create `plugin/scripts/platforms/threads.py`:

```python
"""Threads platform module — post to Threads via Meta's Threads API.

Uses the Threads Publishing API:
1. Create a media container (POST /me/threads)
2. Publish the container (POST /me/threads_publish)

For threads (multiple posts): publish first post, then reply to it.
"""

import os
import sys
import time

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import requests

from scripts.platforms.base import validate_platform_config

THREADS_API_BASE = "https://graph.threads.net/v1.0"
REQUIRED_KEYS = ["access_token"]


def validate_config(config):
    """Check Threads credentials are present. Returns error string or None."""
    return validate_platform_config(config, "threads", REQUIRED_KEYS)


def _create_container(access_token, text, reply_to_id=None, image_url=None):
    """Create a Threads media container.

    Returns container ID or raises Exception.
    """
    params = {
        "media_type": "TEXT",
        "text": text,
        "access_token": access_token,
    }
    if reply_to_id:
        params["reply_to_id"] = reply_to_id
    if image_url:
        params["media_type"] = "IMAGE"
        params["image_url"] = image_url

    resp = requests.post(f"{THREADS_API_BASE}/me/threads", params=params)
    data = resp.json()
    if "id" not in data:
        raise Exception(f"Failed to create container: {data.get('error', data)}")
    return data["id"]


def _publish_container(access_token, container_id):
    """Publish a Threads media container.

    Returns published post ID or raises Exception.
    """
    resp = requests.post(
        f"{THREADS_API_BASE}/me/threads_publish",
        params={"creation_id": container_id, "access_token": access_token},
    )
    data = resp.json()
    if "id" not in data:
        raise Exception(f"Failed to publish: {data.get('error', data)}")
    return data["id"]


def post(config, content_parts, images=None, frontmatter=None):
    """Post to Threads — single post or thread.

    Args:
        config: Full config dict with 'threads' section.
        content_parts: List of strings. 1 item = single post, 2+ = thread.
        images: Optional list of image file paths (not yet supported for Threads API uploads).
        frontmatter: Draft frontmatter dict (unused for Threads).

    Returns:
        dict with 'success', 'post_ids', and optionally 'error'.
    """
    access_token = config["threads"]["access_token"]
    post_ids = []

    try:
        reply_to = None
        for text in content_parts:
            # Create container
            container_id = _create_container(access_token, text, reply_to_id=reply_to)
            # Publish
            post_id = _publish_container(access_token, container_id)
            post_ids.append(post_id)
            reply_to = post_id

        return {"success": True, "post_ids": post_ids}

    except Exception as e:
        return {"success": False, "error": str(e), "post_ids": post_ids}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugin && python -m pytest ../tests/test_platform_threads.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Run all tests**

Run: `cd plugin && python -m pytest ../tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add plugin/scripts/platforms/threads.py tests/test_platform_threads.py
git commit -m "feat: add Threads platform module via Meta API"
```

---

### Task 10: Phase 3 — Verify Threads end-to-end with user

**Files:** No new files — verification only.

- [ ] **Step 1: Test with user — setup Threads credentials**

Run `/setup threads` with the user. Walk through getting a Threads access token from developers.facebook.com.

- [ ] **Step 2: Test with user — generate Threads content**

Run `/generate-content --platform threads "test topic"`. Verify:
- File created with `_post_threads.md` or `_thread_threads.md` naming
- Frontmatter has `platform: threads`
- Content follows 500 char/post limit, uses `## Post N` headings

- [ ] **Step 3: Test with user — post to Threads**

Run `/post <draft-file>`. Verify:
- Routes to `platforms/threads.py`
- Posts successfully
- Frontmatter updated

- [ ] **Step 4: Commit verification**

```bash
git commit --allow-empty -m "chore: Phase 3 complete — Threads verified"
```

---

## Phase 4: Facebook

### Task 11: Create `platforms/facebook.py`

**Files:**
- Create: `plugin/scripts/platforms/facebook.py`
- Test: `tests/test_platform_facebook.py`

- [ ] **Step 1: Write failing tests for Facebook platform**

Create `tests/test_platform_facebook.py`:

```python
import os
import sys
from unittest.mock import MagicMock, patch

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_validate_config_valid():
    """validate_config returns None when Facebook credentials are present."""
    from scripts.platforms.facebook import validate_config

    config = {
        "facebook": {
            "page_access_token": "token",
            "page_id": "12345",
        }
    }
    assert validate_config(config) is None


def test_validate_config_missing_section():
    """validate_config returns error when facebook section is missing."""
    from scripts.platforms.facebook import validate_config

    error = validate_config({})
    assert error is not None
    assert "facebook" in error.lower()


def test_validate_config_missing_key():
    """validate_config returns error when page_id is empty."""
    from scripts.platforms.facebook import validate_config

    config = {
        "facebook": {
            "page_access_token": "token",
            "page_id": "",
        }
    }
    error = validate_config(config)
    assert error is not None
    assert "page_id" in error


@patch("scripts.platforms.facebook.requests")
def test_post_text(mock_requests):
    """post() creates a Facebook Page text post."""
    from scripts.platforms.facebook import post

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "12345_67890"}
    mock_requests.post.return_value = mock_resp

    config = {
        "facebook": {
            "page_access_token": "token",
            "page_id": "12345",
        }
    }
    result = post(config, ["Hello from Facebook!"])
    assert result["success"] is True
    assert result["post_ids"] == ["12345_67890"]


@patch("scripts.platforms.facebook.requests")
def test_post_with_image(mock_requests):
    """post() creates a Facebook Page photo post when images provided."""
    from scripts.platforms.facebook import post

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "12345_photo1"}
    mock_requests.post.return_value = mock_resp

    config = {
        "facebook": {
            "page_access_token": "token",
            "page_id": "12345",
        }
    }
    result = post(config, ["Photo post!"], images=["/path/to/img.png"])
    assert result["success"] is True
    assert result["post_ids"] == ["12345_photo1"]
    # Should call photos endpoint
    call_url = mock_requests.post.call_args[0][0]
    assert "photos" in call_url


@patch("scripts.platforms.facebook.requests")
def test_post_api_error(mock_requests):
    """post() returns error when API returns error response."""
    from scripts.platforms.facebook import post

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": {"message": "Invalid token"}}
    mock_requests.post.return_value = mock_resp

    config = {
        "facebook": {
            "page_access_token": "bad_token",
            "page_id": "12345",
        }
    }
    result = post(config, ["Hello!"])
    assert result["success"] is False
    assert "invalid token" in result["error"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugin && python -m pytest ../tests/test_platform_facebook.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.platforms.facebook'`

- [ ] **Step 3: Write `platforms/facebook.py`**

Create `plugin/scripts/platforms/facebook.py`:

```python
"""Facebook platform module — post to Facebook Pages via Graph API.

Uses the Facebook Graph API v19.0:
- Text posts: POST /{page_id}/feed
- Photo posts: POST /{page_id}/photos
"""

import os
import sys

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import requests

from scripts.platforms.base import validate_platform_config

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
REQUIRED_KEYS = ["page_access_token", "page_id"]


def validate_config(config):
    """Check Facebook credentials are present. Returns error string or None."""
    return validate_platform_config(config, "facebook", REQUIRED_KEYS)


def post(config, content_parts, images=None, frontmatter=None):
    """Post to a Facebook Page.

    Args:
        config: Full config dict with 'facebook' section.
        content_parts: List of strings. All parts joined as one post body.
        images: Optional list of image file paths. First image used for photo post.
        frontmatter: Draft frontmatter dict. 'visibility' field controls privacy.

    Returns:
        dict with 'success', 'post_ids', and optionally 'error'.
    """
    fc = config["facebook"]
    page_id = fc["page_id"]
    access_token = fc["page_access_token"]
    frontmatter = frontmatter or {}

    body = "\n\n".join(content_parts)

    try:
        if images:
            # Photo post
            with open(images[0], "rb") as img_file:
                resp = requests.post(
                    f"{GRAPH_API_BASE}/{page_id}/photos",
                    data={
                        "message": body,
                        "access_token": access_token,
                    },
                    files={"source": img_file},
                )
        else:
            # Text post
            resp = requests.post(
                f"{GRAPH_API_BASE}/{page_id}/feed",
                data={
                    "message": body,
                    "access_token": access_token,
                },
            )

        data = resp.json()

        if "error" in data:
            return {"success": False, "error": data["error"].get("message", str(data["error"]))}

        if "id" not in data:
            return {"success": False, "error": f"Unexpected response: {data}"}

        return {"success": True, "post_ids": [data["id"]]}

    except Exception as e:
        return {"success": False, "error": str(e)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugin && python -m pytest ../tests/test_platform_facebook.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Run all tests**

Run: `cd plugin && python -m pytest ../tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add plugin/scripts/platforms/facebook.py tests/test_platform_facebook.py
git commit -m "feat: add Facebook platform module via Graph API"
```

---

### Task 12: Phase 4 — Verify Facebook end-to-end with user

**Files:** No new files — verification only.

- [ ] **Step 1: Test with user — setup Facebook credentials**

Run `/setup facebook` with the user. Walk through getting Page Access Token from Graph API Explorer.

- [ ] **Step 2: Test with user — generate Facebook content**

Run `/generate-content --platform facebook "test topic"`. Verify:
- File created with `_post_facebook.md` naming
- Frontmatter has `platform: facebook`, `visibility: public`
- Body is plain text, no heading splits

- [ ] **Step 3: Test with user — post to Facebook**

Run `/post <draft-file>`. Verify:
- Routes to `platforms/facebook.py`
- Posts to correct Facebook Page
- Frontmatter updated

- [ ] **Step 4: Final — run full test suite**

Run: `cd plugin && python -m pytest ../tests/ -v`
Expected: All tests PASS across all modules

- [ ] **Step 5: Commit verification**

```bash
git commit --allow-empty -m "chore: Phase 4 complete — Facebook verified, all platforms operational"
```
