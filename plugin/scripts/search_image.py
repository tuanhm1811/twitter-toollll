#!/usr/bin/env python3
"""Download images from URLs for use as social media post images."""

import argparse
import json
import os
import sys

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import requests

VALID_IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp", "image/gif")


def download_image(url, output_path):
    """Download an image from a URL to a local file.

    Args:
        url: Remote image URL to download.
        output_path: Where to save the downloaded image.

    Returns:
        dict with 'success', 'path', 'url', 'source', and optionally 'error'.
    """
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type not in VALID_IMAGE_TYPES:
            return {
                "success": False,
                "error": f"Not an image: content-type is '{content_type}'",
            }

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)

        return {"success": True, "path": output_path, "url": url, "source": "web"}

    except Exception as e:
        return {"success": False, "error": f"Failed to download image: {e}"}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Download image from URL")
    parser.add_argument("--url", required=True, help="Image URL to download")
    parser.add_argument("--output", required=True, help="Output file path")
    args = parser.parse_args(argv)

    result = download_image(args.url, args.output)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
