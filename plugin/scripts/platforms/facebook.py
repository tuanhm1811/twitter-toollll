"""Facebook platform module — post to Facebook Pages via Graph API."""

import os
import sys

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import requests

from scripts.platforms.base import validate_platform_config

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
REQUIRED_KEYS = ["page_access_token", "page_id"]


def validate_config(config):
    return validate_platform_config(config, "facebook", REQUIRED_KEYS)


def post(config, content_parts, images=None, frontmatter=None):
    fc = config["facebook"]
    page_id = fc["page_id"]
    access_token = fc["page_access_token"]
    body = "\n\n".join(content_parts)

    try:
        if images:
            with open(images[0], "rb") as img_file:
                resp = requests.post(
                    f"{GRAPH_API_BASE}/{page_id}/photos",
                    data={"message": body, "access_token": access_token},
                    files={"source": img_file},
                )
        else:
            resp = requests.post(
                f"{GRAPH_API_BASE}/{page_id}/feed",
                data={"message": body, "access_token": access_token},
            )

        data = resp.json()
        if "error" in data:
            return {"success": False, "error": data["error"].get("message", str(data["error"]))}
        if "id" not in data:
            return {"success": False, "error": f"Unexpected response: {data}"}
        return {"success": True, "post_ids": [data["id"]]}
    except Exception as e:
        return {"success": False, "error": str(e)}
