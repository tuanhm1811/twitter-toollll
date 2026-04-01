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


@patch("scripts.platforms.twitter.tweepy")
@patch("scripts.utils.config.load_config")
def test_post_passes_image_dicts(mock_load_config, mock_tweepy):
    """post.py passes resolved image dicts to platform module."""
    mock_load_config.return_value = {
        "twitter": {"api_key": "k", "api_secret": "s", "access_token": "t", "access_secret": "a"}
    }
    mock_client = MagicMock()
    mock_client.create_tweet.return_value = MagicMock(data={"id": "333", "text": "Img"})
    mock_tweepy.Client.return_value = mock_client

    mock_api_v1 = MagicMock()
    mock_media = MagicMock()
    mock_media.media_id = 777
    mock_api_v1.media_upload.return_value = mock_media
    mock_tweepy.OAuth1UserHandler.return_value = MagicMock()
    mock_tweepy.API.return_value = mock_api_v1

    # Create draft with image in frontmatter
    content = """---
platform: twitter
type: tweet
topic: "Test Images"
status: draft
created_at: "2026-04-01 10:00"
posted_at: ""
post_ids: []
has_images: true
images:
  - path: "images/test_banner.png"
    url: "https://kie.ai/images/test.png"
    description: "Test banner"
---

Hello with image!
"""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, dir="/tmp")
    f.write(content)
    f.close()

    try:
        from scripts.post import main
        result = main(["--file", f.name])
        assert result["success"] is True
        # Verify media_upload was called (images were passed through)
        mock_api_v1.media_upload.assert_called_once()
        # The path should be resolved to absolute
        call_arg = mock_api_v1.media_upload.call_args[0][0]
        assert call_arg.endswith("images/test_banner.png")
    finally:
        os.unlink(f.name)
