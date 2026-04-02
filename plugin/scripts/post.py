#!/usr/bin/env python3
"""Unified entry point for posting content to any platform.

Reads a draft markdown file, determines the target platform from frontmatter,
routes to the correct platform module, posts, and updates the draft frontmatter.

Usage:
    python post.py --file <draft.md> [--config <config.yaml>] [--dry-run]
"""

import argparse
import json
import os
import sys
from datetime import datetime

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

from scripts.utils.config import load_config
from scripts.utils.draft import parse_draft, update_frontmatter, resolve_image_paths
from scripts.platforms import get_platform_module


def dry_run(file_path, config):
    """Validate draft and verify platform credentials without posting.

    Checks: file exists, valid frontmatter, content present, platform supported,
    config valid, and credentials work (via read-only API call).
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    frontmatter, content_parts = parse_draft(file_path)

    if frontmatter is None:
        return {"success": False, "error": f"Invalid draft format (missing frontmatter): {file_path}"}

    if not content_parts:
        return {"success": False, "error": f"No content found in: {file_path}"}

    platform_name = frontmatter.get("platform")
    if not platform_name:
        return {"success": False, "error": f"No 'platform' field in frontmatter: {file_path}"}

    platform_module = get_platform_module(platform_name)
    if not platform_module:
        return {"success": False, "error": f"Unsupported platform: {platform_name}"}

    config_error = platform_module.validate_config(config)
    if config_error:
        return {"success": False, "error": config_error}

    # Verify credentials with read-only API call
    verify = platform_module.verify_credentials(config)
    if not verify.get("success"):
        return {"success": False, "error": f"Credential verification failed: {verify.get('error')}"}

    return {"success": True, "dry_run": True, "platform": platform_name, "file": file_path, "verified": verify}


def post_from_file(file_path, config):
    """Read a draft file, post to the correct platform, update frontmatter."""
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    frontmatter, content_parts = parse_draft(file_path)

    if frontmatter is None:
        return {"success": False, "error": f"Invalid draft format (missing frontmatter): {file_path}"}

    if not content_parts:
        return {"success": False, "error": f"No content found in: {file_path}"}

    if frontmatter.get("status") == "posted":
        return {"success": False, "error": f"Already posted: {file_path}"}

    platform_name = frontmatter.get("platform")
    if not platform_name:
        return {"success": False, "error": f"No 'platform' field in frontmatter: {file_path}"}

    platform_module = get_platform_module(platform_name)
    if not platform_module:
        return {"success": False, "error": f"Unsupported platform: {platform_name}"}

    # Validate platform config
    config_error = platform_module.validate_config(config)
    if config_error:
        return {"success": False, "error": config_error}

    # Resolve images
    draft_dir = os.path.dirname(os.path.abspath(file_path))
    image_paths = resolve_image_paths(frontmatter, draft_dir)

    # Post
    result = platform_module.post(config, content_parts, images=image_paths or None, frontmatter=frontmatter)

    # Update frontmatter on success
    if result.get("success"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        update_frontmatter(file_path, {
            "status": "posted",
            "posted_at": now,
            "post_ids": result.get("post_ids", []),
        })
        result["file"] = file_path
        result["frontmatter_updated"] = True

    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Post content to social media platforms")
    parser.add_argument("--file", required=True, help="Draft markdown file to post")
    parser.add_argument("--config", help="Config file path (default: .social-agent.yaml)")
    parser.add_argument("--dry-run", action="store_true", help="Validate draft and verify credentials without posting")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if config is None:
        result = {"success": False, "error": "Config file not found. Run /setup first."}
        print(json.dumps(result))
        return result

    if args.dry_run:
        result = dry_run(args.file, config)
    else:
        result = post_from_file(args.file, config)
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    main()
