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


def verify_credentials(config):
    """Verify Threads credentials by calling /me. Returns dict with success."""
    access_token = config["threads"]["access_token"]
    try:
        resp = requests.get(
            f"{THREADS_API_BASE}/me",
            params={"access_token": access_token, "fields": "id,username"},
        )
        data = resp.json()
        if "error" in data:
            return {"success": False, "error": data["error"].get("message", str(data["error"]))}
        return {"success": True, "username": data.get("username", data.get("id"))}
    except Exception as e:
        return {"success": False, "error": str(e)}


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
        images: Optional list of image dicts with 'path' and 'url' keys.
        frontmatter: Draft frontmatter dict (unused for Threads).

    Returns:
        dict with 'success', 'post_ids', and optionally 'error'.
    """
    access_token = config["threads"]["access_token"]
    post_ids = []

    # Extract image URL for first post (if available)
    first_image_url = None
    if images:
        img = images[0]
        url = img.get("url", "") if isinstance(img, dict) else ""
        if url:
            first_image_url = url

    try:
        reply_to = None
        for i, text in enumerate(content_parts):
            # Attach image only to first post
            image_url = first_image_url if i == 0 else None
            container_id = _create_container(access_token, text, reply_to_id=reply_to, image_url=image_url)
            post_id = _publish_container(access_token, container_id)
            post_ids.append(post_id)
            reply_to = post_id

        return {"success": True, "post_ids": post_ids}

    except Exception as e:
        return {"success": False, "error": str(e), "post_ids": post_ids}
