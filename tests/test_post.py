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
