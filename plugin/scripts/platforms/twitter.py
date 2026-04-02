"""Twitter platform module — post tweets and threads via Twitter API v2."""

import os
import sys

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import tweepy

from scripts.platforms.base import validate_platform_config

REQUIRED_KEYS = ["api_key", "api_secret", "access_token", "access_secret"]


def validate_config(config):
    """Check Twitter credentials are present. Returns error string or None."""
    return validate_platform_config(config, "twitter", REQUIRED_KEYS)


def verify_credentials(config):
    """Verify Twitter credentials by calling get_me(). Returns dict with success."""
    tc = config["twitter"]
    try:
        client = tweepy.Client(
            consumer_key=tc["api_key"],
            consumer_secret=tc["api_secret"],
            access_token=tc["access_token"],
            access_token_secret=tc["access_secret"],
        )
        me = client.get_me()
        return {"success": True, "username": me.data.username}
    except Exception as e:
        return {"success": False, "error": str(e)}


def post(config, content_parts, images=None, frontmatter=None):
    """Post tweet or thread to Twitter.

    Args:
        config: Full config dict with 'twitter' section.
        content_parts: List of strings. 1 item = single tweet, 2+ = thread.
        images: Optional list of image dicts or file paths. Attached to first tweet.
        frontmatter: Draft frontmatter dict (unused for Twitter).

    Returns:
        dict with 'success', 'post_ids', and optionally 'error'.
    """
    tc = config["twitter"]
    post_ids = []

    try:
        client = tweepy.Client(
            consumer_key=tc["api_key"],
            consumer_secret=tc["api_secret"],
            access_token=tc["access_token"],
            access_token_secret=tc["access_secret"],
        )

        # Upload images via v1.1 API if provided
        media_ids = None
        if images:
            auth = tweepy.OAuth1UserHandler(
                consumer_key=tc["api_key"],
                consumer_secret=tc["api_secret"],
                access_token=tc["access_token"],
                access_token_secret=tc["access_secret"],
            )
            api_v1 = tweepy.API(auth)
            media_ids = []
            for img in images:
                path = img["path"] if isinstance(img, dict) else img
                media = api_v1.media_upload(path)
                media_ids.append(media.media_id)

        reply_to = None
        for i, text in enumerate(content_parts):
            kwargs = {"text": text}
            # Attach images only to first tweet
            if i == 0 and media_ids:
                kwargs["media_ids"] = media_ids
            if reply_to:
                kwargs["in_reply_to_tweet_id"] = reply_to

            response = client.create_tweet(**kwargs)
            post_id = response.data["id"]
            post_ids.append(post_id)
            reply_to = post_id

        return {"success": True, "post_ids": post_ids}

    except Exception as e:
        return {"success": False, "error": str(e), "post_ids": post_ids}
