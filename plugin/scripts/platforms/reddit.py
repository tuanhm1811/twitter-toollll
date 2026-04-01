"""Reddit platform module — post submissions via Reddit API using praw."""

import os
import sys

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import praw

from scripts.platforms.base import validate_platform_config

REQUIRED_KEYS = ["client_id", "client_secret", "username", "password"]


def validate_config(config):
    """Check Reddit credentials are present. Returns error string or None."""
    return validate_platform_config(config, "reddit", REQUIRED_KEYS)


def post(config, content_parts, images=None, frontmatter=None):
    """Post a submission to Reddit.

    Args:
        config: Full config dict with 'reddit' section.
        content_parts: List of strings. For Reddit, first item is the body.
        images: Optional list of image dicts (ignored — Reddit always uses text posts).
        frontmatter: Draft frontmatter dict with 'subreddit' and 'title' fields.

    Returns:
        dict with 'success', 'post_ids', 'url', and optionally 'error'.
    """
    frontmatter = frontmatter or {}
    subreddit_name = frontmatter.get("subreddit", "")
    title = frontmatter.get("title", "")

    if not subreddit_name:
        return {"success": False, "error": "Missing 'subreddit' in draft frontmatter."}

    if not title:
        return {"success": False, "error": "Missing 'title' in draft frontmatter."}

    rc = config["reddit"]
    body = content_parts[0] if content_parts else ""

    try:
        reddit = praw.Reddit(
            client_id=rc["client_id"],
            client_secret=rc["client_secret"],
            username=rc["username"],
            password=rc["password"],
            user_agent=f"social-agent:v2.0.0 (by /u/{rc['username']})",
        )
        subreddit = reddit.subreddit(subreddit_name)

        # Always use text post — images are not supported for Reddit
        submission = subreddit.submit(
            title=title,
            selftext=body,
        )

        return {
            "success": True,
            "post_ids": [submission.id],
            "url": submission.url,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
