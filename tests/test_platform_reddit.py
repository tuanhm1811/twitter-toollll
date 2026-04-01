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
def test_post_ignores_images(mock_praw):
    """post() ignores images and always creates text post."""
    from scripts.platforms.reddit import post

    mock_reddit = MagicMock()
    mock_subreddit = MagicMock()
    mock_submission = MagicMock()
    mock_submission.id = "txt789"
    mock_submission.url = "https://reddit.com/r/test/comments/txt789/title"
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
        "title": "Image Ignored",
    }
    result = post(config, ["Body text."], images=[{"path": "/img.png", "url": "https://kie.ai/img.png"}], frontmatter=frontmatter)
    assert result["success"] is True
    mock_subreddit.submit.assert_called_once()
    mock_subreddit.submit_image.assert_not_called()


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
