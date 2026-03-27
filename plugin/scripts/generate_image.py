#!/usr/bin/env python3
"""Generate images via kie.ai API."""

import argparse
import json
import os
import sys
import time

# Ensure plugin root is in path so imports work from any CWD
_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import requests

from scripts.utils.config import load_config

KIE_BASE_URL = "https://api.kie.ai"
GENERATE_ENDPOINT = f"{KIE_BASE_URL}/api/v1/gpt4o-image/generate"
STATUS_ENDPOINT = f"{KIE_BASE_URL}/api/v1/gpt4o-image/record-info"
DOWNLOAD_ENDPOINT = f"{KIE_BASE_URL}/api/v1/common/download-url"

POLL_INTERVAL = 3  # seconds between status checks
MAX_POLL_ATTEMPTS = 60  # max ~3 minutes of polling


def generate_image(api_key, prompt, output_path, size="1:1"):
    """Generate an image using kie.ai 4o Image API.

    Args:
        api_key: kie.ai API key
        prompt: Text description of the image to generate
        output_path: Where to save the generated image
        size: Aspect ratio - "1:1", "3:2", or "2:3"
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Step 1: Submit generation task
    try:
        resp = requests.post(
            GENERATE_ENDPOINT,
            headers=headers,
            json={"prompt": prompt, "size": size},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 200:
            return {"success": False, "error": f"API error: {data.get('msg', 'Unknown error')}"}

        task_id = data["data"]["taskId"]
    except Exception as e:
        return {"success": False, "error": f"Failed to submit task: {e}"}

    # Step 2: Poll for completion
    try:
        for _ in range(MAX_POLL_ATTEMPTS):
            time.sleep(POLL_INTERVAL)
            status_resp = requests.get(
                STATUS_ENDPOINT,
                headers=headers,
                params={"taskId": task_id},
                timeout=30,
            )
            status_resp.raise_for_status()
            status_data = status_resp.json()

            if status_data.get("code") != 200:
                continue

            task_info = status_data.get("data", {})
            status = task_info.get("status")

            if status == "SUCCESS":
                result_urls = task_info.get("response", {}).get("resultUrls", [])
                if not result_urls:
                    return {"success": False, "error": "No image URLs in response"}

                # Step 3: Download the image
                image_url = result_urls[0]
                return _download_image(headers, image_url, output_path)

            elif status in ("CREATE_TASK_FAILED", "GENERATE_FAILED"):
                error_msg = task_info.get("errorMessage", "Generation failed")
                return {"success": False, "error": error_msg}

        return {"success": False, "error": "Timeout waiting for image generation"}
    except Exception as e:
        return {"success": False, "error": f"Failed polling status: {e}"}


def _download_image(headers, image_url, output_path):
    """Download image from kie.ai URL to local file."""
    try:
        # Get direct download URL
        dl_resp = requests.post(
            DOWNLOAD_ENDPOINT,
            headers=headers,
            json={"url": image_url},
            timeout=30,
        )
        dl_resp.raise_for_status()
        dl_data = dl_resp.json()

        if dl_data.get("code") != 200:
            return {"success": False, "error": f"Download URL error: {dl_data.get('msg')}"}

        download_url = dl_data["data"]

        # Download the actual image
        img_resp = requests.get(download_url, timeout=60)
        img_resp.raise_for_status()

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_resp.content)

        return {"success": True, "path": output_path}
    except Exception as e:
        return {"success": False, "error": f"Failed to download image: {e}"}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate images via kie.ai API")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--output", default="./images/output.png",
                        help="Output file path (default: ./images/output.png)")
    parser.add_argument("--size", default="3:2", choices=["1:1", "3:2", "2:3"],
                        help="Aspect ratio (default: 3:2 for Twitter banners)")
    parser.add_argument("--config", help="Config file path (default: .twitter-agent.yaml)")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if config is None:
        print(json.dumps({"success": False, "error": "Config file not found. Run /setup first."}))
        sys.exit(1)

    api_key = config.get("kie_api_key")
    if not api_key:
        print(json.dumps({"success": False, "error": "kie_api_key not set in config"}))
        sys.exit(1)

    result = generate_image(api_key, args.prompt, args.output, args.size)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
