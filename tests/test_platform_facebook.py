import os
import sys
from unittest.mock import MagicMock, mock_open, patch

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_validate_config_valid():
    from scripts.platforms.facebook import validate_config
    config = {"facebook": {"page_access_token": "token", "page_id": "12345"}}
    assert validate_config(config) is None


def test_validate_config_missing_section():
    from scripts.platforms.facebook import validate_config
    error = validate_config({})
    assert error is not None
    assert "facebook" in error.lower()


def test_validate_config_missing_key():
    from scripts.platforms.facebook import validate_config
    config = {"facebook": {"page_access_token": "token", "page_id": ""}}
    error = validate_config(config)
    assert error is not None
    assert "page_id" in error


@patch("scripts.platforms.facebook.requests")
def test_post_text(mock_requests):
    from scripts.platforms.facebook import post
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "12345_67890"}
    mock_requests.post.return_value = mock_resp
    config = {"facebook": {"page_access_token": "token", "page_id": "12345"}}
    result = post(config, ["Hello from Facebook!"])
    assert result["success"] is True
    assert result["post_ids"] == ["12345_67890"]


@patch("scripts.platforms.facebook.requests")
@patch("builtins.open", mock_open(read_data=b"imgdata"))
def test_post_with_image(mock_requests):
    from scripts.platforms.facebook import post
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "12345_photo1"}
    mock_requests.post.return_value = mock_resp
    config = {"facebook": {"page_access_token": "token", "page_id": "12345"}}
    result = post(config, ["Photo post!"], images=["/path/to/img.png"])
    assert result["success"] is True
    assert result["post_ids"] == ["12345_photo1"]
    call_url = mock_requests.post.call_args[0][0]
    assert "photos" in call_url


@patch("scripts.platforms.facebook.requests")
def test_post_api_error(mock_requests):
    from scripts.platforms.facebook import post
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": {"message": "Invalid token"}}
    mock_requests.post.return_value = mock_resp
    config = {"facebook": {"page_access_token": "bad_token", "page_id": "12345"}}
    result = post(config, ["Hello!"])
    assert result["success"] is False
    assert "invalid token" in result["error"].lower()
