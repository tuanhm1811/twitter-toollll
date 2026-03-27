#!/usr/bin/env python3
"""Post tweets and threads via Twitter API v2.

Supports two modes:
  --file <draft.md>   Read a draft markdown file, post it, and update its frontmatter.
  --text / --thread   Post raw text directly (original mode).
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

# Ensure plugin root is in path so imports work from any CWD
_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import tweepy
import yaml

from scripts.utils.config import load_config


def create_twitter_client(config):
    """Create a Tweepy Client for Twitter API v2."""
    return tweepy.Client(
        consumer_key=config["twitter_api_key"],
        consumer_secret=config["twitter_api_secret"],
        access_token=config["twitter_access_token"],
        access_token_secret=config["twitter_access_secret"],
    )


def create_twitter_api_v1(config):
    """Create a Tweepy API (v1.1) for media uploads."""
    auth = tweepy.OAuth1UserHandler(
        consumer_key=config["twitter_api_key"],
        consumer_secret=config["twitter_api_secret"],
        access_token=config["twitter_access_token"],
        access_token_secret=config["twitter_access_secret"],
    )
    return tweepy.API(auth)


# ---------------------------------------------------------------------------
# Draft file parsing
# ---------------------------------------------------------------------------

def parse_draft(file_path):
    """Parse a draft markdown file into frontmatter dict and list of tweet texts."""
    with open(file_path, "r") as f:
        raw = f.read()

    # Split YAML frontmatter from body
    match = re.match(r"^---\n(.*?)\n---\n(.*)", raw, re.DOTALL)
    if not match:
        return None, []

    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()

    # Split body into tweets by "## Tweet N" headings
    parts = re.split(r"^## Tweet \d+\s*\n", body, flags=re.MULTILINE)
    tweets = [p.strip() for p in parts if p.strip()]

    # If no headings found, treat the whole body as a single tweet
    if not tweets:
        tweets = [body]

    return frontmatter, tweets


def update_draft_frontmatter(file_path, updates):
    """Update specific frontmatter fields in a draft file, preserving the body."""
    with open(file_path, "r") as f:
        raw = f.read()

    match = re.match(r"^---\n(.*?)\n---\n(.*)", raw, re.DOTALL)
    if not match:
        return

    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)

    frontmatter.update(updates)

    new_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip()
    with open(file_path, "w") as f:
        f.write(f"---\n{new_yaml}\n---\n{body}")


def post_tweet(config, text, image_paths=None, reply_to=None):
    """Post a single tweet, optionally with images and as a reply."""
    try:
        client = create_twitter_client(config)
        media_ids = None

        if image_paths:
            api_v1 = create_twitter_api_v1(config)
            media_ids = []
            for path in image_paths:
                media = api_v1.media_upload(path)
                media_ids.append(media.media_id)

        kwargs = {"text": text}
        if media_ids:
            kwargs["media_ids"] = media_ids
        if reply_to:
            kwargs["in_reply_to_tweet_id"] = reply_to

        response = client.create_tweet(**kwargs)
        return {
            "success": True,
            "tweet_id": response.data["id"],
            "text": response.data["text"],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def post_thread(config, tweets, image_paths_per_tweet=None):
    """Post a thread of tweets, each replying to the previous.

    Args:
        config: Config dict with Twitter API keys
        tweets: List of tweet texts
        image_paths_per_tweet: Optional list of lists — image paths for each tweet.
            e.g. [["img1.png"], None, ["img2.png"]] attaches img1 to tweet 1,
            nothing to tweet 2, img2 to tweet 3.
    """
    tweet_ids = []
    try:
        client = create_twitter_client(config)
        reply_to = None

        for i, text in enumerate(tweets):
            media_ids = None
            if image_paths_per_tweet and i < len(image_paths_per_tweet) and image_paths_per_tweet[i]:
                api_v1 = create_twitter_api_v1(config)
                media_ids = []
                for path in image_paths_per_tweet[i]:
                    media = api_v1.media_upload(path)
                    media_ids.append(media.media_id)

            kwargs = {"text": text}
            if media_ids:
                kwargs["media_ids"] = media_ids
            if reply_to:
                kwargs["in_reply_to_tweet_id"] = reply_to

            response = client.create_tweet(**kwargs)
            tweet_id = response.data["id"]
            tweet_ids.append(tweet_id)
            reply_to = tweet_id

        return {"success": True, "tweet_ids": tweet_ids}
    except Exception as e:
        return {"success": False, "error": str(e), "tweet_ids_posted": tweet_ids}


def post_from_file(file_path, config):
    """Read a draft file, post it to Twitter, and update the draft frontmatter."""
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    frontmatter, tweets = parse_draft(file_path)
    if frontmatter is None:
        return {"success": False, "error": f"Invalid draft format (missing frontmatter): {file_path}"}

    if not tweets:
        return {"success": False, "error": f"No tweet content found in: {file_path}"}

    if frontmatter.get("status") == "posted":
        return {"success": False, "error": f"Already posted: {file_path}"}

    # Resolve image paths relative to the draft file's directory
    draft_dir = os.path.dirname(os.path.abspath(file_path))
    project_dir = os.path.dirname(draft_dir)  # contents/ -> project root

    image_paths = []
    if frontmatter.get("has_images") and frontmatter.get("images"):
        for img in frontmatter["images"]:
            p = img.get("path", "") if isinstance(img, dict) else str(img)
            if p:
                if not os.path.isabs(p):
                    p = os.path.join(project_dir, p)
                image_paths.append(p)

    # Post
    if len(tweets) == 1:
        result = post_tweet(config, tweets[0], image_paths=image_paths or None)
    else:
        # For threads, attach all images to the first tweet (common pattern)
        thread_images = [image_paths or None] + [None] * (len(tweets) - 1) if image_paths else None
        result = post_thread(config, tweets, image_paths_per_tweet=thread_images)

    # Update frontmatter on success
    if result.get("success"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        tweet_ids = result.get("tweet_ids", [])
        if not tweet_ids and result.get("tweet_id"):
            tweet_ids = [result["tweet_id"]]
        update_draft_frontmatter(file_path, {
            "status": "posted",
            "posted_at": now,
            "tweet_ids": tweet_ids,
        })
        result["file"] = file_path
        result["frontmatter_updated"] = True

    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Post tweets via Twitter API")
    parser.add_argument("--file", help="Draft markdown file to post (reads content and updates frontmatter)")
    parser.add_argument("--text", help="Tweet text (for single tweet)")
    parser.add_argument("--thread", nargs="+", help="Thread texts (multiple tweets)")
    parser.add_argument("--images", help="Comma-separated image paths (for single tweet)")
    parser.add_argument("--thread-images",
                        help="JSON array of image arrays per tweet, e.g. '[[\"img1.png\"], null, [\"img2.png\"]]'")
    parser.add_argument("--reply-to", help="Tweet ID to reply to")
    parser.add_argument("--config", help="Config file path (default: .twitter-agent.yaml)")
    args = parser.parse_args(argv)

    if not args.file and not args.text and not args.thread:
        parser.error("One of --file, --text, or --thread is required")

    config = load_config(args.config)
    if config is None:
        print(json.dumps({"success": False, "error": "Config file not found. Run /setup first."}))
        sys.exit(1)

    if args.file:
        result = post_from_file(args.file, config)
    elif args.thread:
        thread_images = None
        if args.thread_images:
            thread_images = json.loads(args.thread_images)
        result = post_thread(config, args.thread, image_paths_per_tweet=thread_images)
    else:
        image_paths = args.images.split(",") if args.images else None
        result = post_tweet(config, args.text, image_paths=image_paths, reply_to=args.reply_to)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
