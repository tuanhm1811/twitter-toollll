import os
import sys
from unittest.mock import MagicMock, patch

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


@patch("scripts.generate_image.requests")
@patch("scripts.generate_image.time")
def test_generate_image_returns_url(mock_time, mock_requests):
    """generate_image returns both local path and remote kie.ai URL on success."""
    from scripts.generate_image import generate_image

    # Step 1: Submit task
    submit_resp = MagicMock()
    submit_resp.json.return_value = {"code": 200, "data": {"taskId": "t1"}}

    # Step 2: Poll status — immediate success
    status_resp = MagicMock()
    status_resp.json.return_value = {
        "code": 200,
        "data": {
            "status": "SUCCESS",
            "response": {"resultUrls": ["https://kie.ai/images/abc123.png"]},
        },
    }

    # Step 3a: Get download URL
    dl_url_resp = MagicMock()
    dl_url_resp.json.return_value = {"code": 200, "data": "https://cdn.kie.ai/abc123.png"}

    # Step 3b: Download image bytes
    img_resp = MagicMock()
    img_resp.content = b"fakepng"

    mock_requests.post.side_effect = [submit_resp, dl_url_resp]
    mock_requests.get.side_effect = [status_resp, img_resp]

    result = generate_image("key", "a cat", "/tmp/test_img.png", size="3:2")

    assert result["success"] is True
    assert result["path"] == "/tmp/test_img.png"
    assert result["url"] == "https://kie.ai/images/abc123.png"

    # Cleanup
    if os.path.exists("/tmp/test_img.png"):
        os.unlink("/tmp/test_img.png")
