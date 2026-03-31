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
