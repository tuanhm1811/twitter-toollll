import os
import sys
from unittest.mock import MagicMock, patch

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


@patch("scripts.search_image.requests")
def test_download_image_success(mock_requests):
    """download_image saves file and returns path, url, source."""
    from scripts.search_image import download_image

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "image/jpeg"}
    mock_resp.content = b"fakejpegdata"
    mock_requests.get.return_value = mock_resp

    result = download_image("https://example.com/photo.jpg", "/tmp/test_search_img.png")

    assert result["success"] is True
    assert result["path"] == "/tmp/test_search_img.png"
    assert result["url"] == "https://example.com/photo.jpg"
    assert result["source"] == "web"

    if os.path.exists("/tmp/test_search_img.png"):
        os.unlink("/tmp/test_search_img.png")


@patch("scripts.search_image.requests")
def test_download_image_404(mock_requests):
    """download_image returns error on HTTP 404."""
    from scripts.search_image import download_image

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.raise_for_status.side_effect = Exception("404 Not Found")
    mock_requests.get.return_value = mock_resp

    result = download_image("https://example.com/missing.jpg", "/tmp/missing.png")

    assert result["success"] is False
    assert "error" in result


@patch("scripts.search_image.requests")
def test_download_image_not_image_content_type(mock_requests):
    """download_image returns error when content-type is not an image."""
    from scripts.search_image import download_image

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.content = b"<html>not an image</html>"
    mock_requests.get.return_value = mock_resp

    result = download_image("https://example.com/page.html", "/tmp/bad.png")

    assert result["success"] is False
    assert "not an image" in result["error"].lower() or "content-type" in result["error"].lower()
