# Twitter Agent Plugin — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code plugin that manages Twitter content creation from knowledge bases — workspaces, summarization, content generation, image generation, and posting.

**Architecture:** Single Claude Code plugin with commands (slash commands), hooks (session-start config check), and Python scripts (image generation, Twitter posting). Workspaces are folders on disk. Config is stored in `~/.claude/twitter-agent.local.md` with YAML frontmatter.

**Tech Stack:** Claude Code plugin system (markdown commands, JSON hooks), Python 3 (tweepy, openai, google-generativeai, pyyaml)

---

## File Map

| File | Responsibility |
|------|---------------|
| `.claude-plugin/plugin.json` | Plugin manifest — name, version, description |
| `config.template.yaml` | Documents all config keys and defaults |
| `scripts/utils/config.py` | Load/save config from `~/.claude/twitter-agent.local.md` |
| `scripts/generate_image.py` | CLI: generate images via OpenAI DALL-E or Gemini Imagen |
| `scripts/post_twitter.py` | CLI: post tweets/threads via Twitter API v2 |
| `scripts/requirements.txt` | Python dependencies |
| `commands/setup.md` | `/setup` — walk user through API key configuration |
| `commands/workspace.md` | `/workspace` — create, list, switch, import |
| `commands/summarize.md` | `/summarize` — generate knowledge summary |
| `commands/generate-content.md` | `/generate-content` — create Twitter drafts |
| `commands/generate-image.md` | `/generate-image` — generate images for drafts |
| `commands/post-twitter.md` | `/post-twitter` — publish drafts to Twitter |
| `hooks/hooks.json` | Session-start hook config |
| `tests/test_config.py` | Tests for config loader |
| `tests/test_generate_image.py` | Tests for image generation script |
| `tests/test_post_twitter.py` | Tests for Twitter posting script |

---

### Task 1: Plugin Scaffold & Config Loader

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `config.template.yaml`
- Create: `scripts/utils/__init__.py`
- Create: `scripts/utils/config.py`
- Create: `scripts/requirements.txt`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Create plugin manifest**

```bash
mkdir -p .claude-plugin
```

Write `.claude-plugin/plugin.json`:
```json
{
  "name": "twitter-agent",
  "version": "1.0.0",
  "description": "Manage Twitter content creation from knowledge bases — workspaces, summarization, content generation, image generation, and posting."
}
```

- [ ] **Step 2: Create config template**

Write `config.template.yaml`:
```yaml
# Twitter Agent Configuration
# Copy this to ~/.claude/twitter-agent.local.md as YAML frontmatter
# Wrap with --- delimiters at top and bottom

# Required: At least one image provider
openai_api_key: ""
gemini_api_key: ""

# Required: Twitter API credentials
twitter_api_key: ""
twitter_api_secret: ""
twitter_access_token: ""
twitter_access_secret: ""

# Optional settings
default_image_provider: "openai"       # openai or gemini
workspace_root: "~/twitter-workspaces" # where workspaces live
auto_post: false                       # skip confirmation before posting
active_workspace: ""                   # current active workspace name
```

- [ ] **Step 3: Create requirements.txt**

Write `scripts/requirements.txt`:
```
openai>=1.0.0
google-generativeai>=0.5.0
tweepy>=4.14.0
pyyaml>=6.0
```

- [ ] **Step 4: Write failing tests for config loader**

Write `tests/__init__.py` (empty file).

Write `scripts/utils/__init__.py` (empty file).

Write `tests/test_config.py`:
```python
import os
import tempfile
import pytest
from scripts.utils.config import load_config, save_config, get_config_path


def test_get_config_path_returns_expected_path():
    path = get_config_path()
    assert path.endswith(".claude/twitter-agent.local.md")
    assert os.path.expanduser("~") in path


def test_load_config_missing_file():
    result = load_config("/tmp/nonexistent-config-12345.local.md")
    assert result is None


def test_load_config_valid_file():
    content = """---
openai_api_key: sk-test123
twitter_api_key: tw-key
twitter_api_secret: tw-secret
twitter_access_token: tw-token
twitter_access_secret: tw-access
default_image_provider: openai
workspace_root: ~/twitter-workspaces
auto_post: false
active_workspace: ai-news
---
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".local.md", delete=False) as f:
        f.write(content)
        f.flush()
        config = load_config(f.name)

    os.unlink(f.name)
    assert config["openai_api_key"] == "sk-test123"
    assert config["twitter_api_key"] == "tw-key"
    assert config["default_image_provider"] == "openai"
    assert config["auto_post"] is False
    assert config["active_workspace"] == "ai-news"


def test_load_config_empty_frontmatter():
    content = """---
---
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".local.md", delete=False) as f:
        f.write(content)
        f.flush()
        config = load_config(f.name)

    os.unlink(f.name)
    assert config == {}


def test_save_config_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.local.md")
        config = {
            "openai_api_key": "sk-test",
            "workspace_root": "~/twitter-workspaces",
            "auto_post": False,
        }
        save_config(config, path)

        loaded = load_config(path)
        assert loaded["openai_api_key"] == "sk-test"
        assert loaded["workspace_root"] == "~/twitter-workspaces"
        assert loaded["auto_post"] is False


def test_save_config_overwrites_existing():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.local.md")
        save_config({"openai_api_key": "old"}, path)
        save_config({"openai_api_key": "new"}, path)

        loaded = load_config(path)
        assert loaded["openai_api_key"] == "new"
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `cd /Users/luthebao/Documents/coding/twitter-agent && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.utils.config'`

- [ ] **Step 6: Implement config loader**

Write `scripts/utils/config.py`:
```python
import os
import yaml


def get_config_path():
    """Return the default config file path."""
    return os.path.join(os.path.expanduser("~"), ".claude", "twitter-agent.local.md")


def load_config(path=None):
    """Load config from a .local.md file with YAML frontmatter.

    Returns the parsed YAML dict, or None if file doesn't exist.
    """
    if path is None:
        path = get_config_path()

    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        content = f.read()

    # Parse YAML frontmatter between --- delimiters
    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    yaml_content = parts[1].strip()
    if not yaml_content:
        return {}

    return yaml.safe_load(yaml_content)


def save_config(config, path=None):
    """Save config dict as YAML frontmatter in a .local.md file."""
    if path is None:
        path = get_config_path()

    os.makedirs(os.path.dirname(path), exist_ok=True)

    yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
    content = f"---\n{yaml_str}---\n"

    with open(path, "w") as f:
        f.write(content)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /Users/luthebao/Documents/coding/twitter-agent && python -m pytest tests/test_config.py -v`
Expected: All 6 tests PASS

- [ ] **Step 8: Commit**

```bash
git init
git add .claude-plugin/plugin.json config.template.yaml scripts/utils/__init__.py scripts/utils/config.py scripts/requirements.txt tests/__init__.py tests/test_config.py
git commit -m "feat: plugin scaffold with config loader"
```

---

### Task 2: Image Generation Script

**Files:**
- Create: `scripts/generate_image.py`
- Create: `tests/test_generate_image.py`

- [ ] **Step 1: Write failing tests for image generation**

Write `tests/test_generate_image.py`:
```python
import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from scripts.generate_image import generate_image_openai, generate_image_gemini, main


def test_generate_image_openai_success():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(b64_json="iVBORw0KGgo=")]  # minimal base64
    mock_client.images.generate.return_value = mock_response

    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test.png")
        with patch("scripts.generate_image.OpenAI", return_value=mock_client):
            result = generate_image_openai(
                api_key="sk-test",
                prompt="a cat",
                output_path=output,
                size="1200x675",
            )
        assert result["success"] is True
        assert result["path"] == output
        assert os.path.exists(output)


def test_generate_image_openai_api_error():
    mock_client = MagicMock()
    mock_client.images.generate.side_effect = Exception("API rate limit")

    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test.png")
        with patch("scripts.generate_image.OpenAI", return_value=mock_client):
            result = generate_image_openai(
                api_key="sk-test",
                prompt="a cat",
                output_path=output,
                size="1200x675",
            )
        assert result["success"] is False
        assert "API rate limit" in result["error"]


def test_generate_image_gemini_success():
    mock_model = MagicMock()
    mock_image = MagicMock()
    mock_image._image_bytes = b"\x89PNG\r\n"
    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [mock_image]

    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "test.png")
        with patch("scripts.generate_image.genai") as mock_genai:
            mock_genai.ImageGenerationModel.from_pretrained.return_value = mock_model
            mock_model.generate_images.return_value = mock_response
            result = generate_image_gemini(
                api_key="ai-test",
                prompt="a cat",
                output_path=output,
                size="1200x675",
            )
        assert result["success"] is True
        assert result["path"] == output


def test_main_missing_prompt(capsys):
    with pytest.raises(SystemExit):
        main(["--provider", "openai", "--output", "/tmp/test.png", "--config", "/tmp/fake.md"])


def test_main_outputs_json():
    mock_result = {"success": True, "path": "/tmp/test.png"}
    with patch("scripts.generate_image.generate_image_openai", return_value=mock_result):
        with patch("scripts.generate_image.load_config", return_value={"openai_api_key": "sk-test"}):
            with patch("sys.stdout") as mock_stdout:
                main(["--prompt", "a cat", "--provider", "openai", "--output", "/tmp/test.png", "--config", "/tmp/fake.md"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/luthebao/Documents/coding/twitter-agent && python -m pytest tests/test_generate_image.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.generate_image'`

- [ ] **Step 3: Implement image generation script**

Write `scripts/generate_image.py`:
```python
#!/usr/bin/env python3
"""Generate images via OpenAI DALL-E or Google Gemini Imagen."""

import argparse
import base64
import json
import os
import sys

from scripts.utils.config import load_config

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


def generate_image_openai(api_key, prompt, output_path, size="1792x1024"):
    """Generate an image using OpenAI DALL-E 3."""
    try:
        if OpenAI is None:
            return {"success": False, "error": "openai package not installed. Run: pip install openai"}
        client = OpenAI(api_key=api_key)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size=size,
            response_format="b64_json",
        )
        image_data = base64.b64decode(response.data[0].b64_json)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_data)
        return {"success": True, "path": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_image_gemini(api_key, prompt, output_path, size="1200x675"):
    """Generate an image using Google Gemini Imagen."""
    try:
        if genai is None:
            return {"success": False, "error": "google-generativeai package not installed. Run: pip install google-generativeai"}
        genai.configure(api_key=api_key)
        model = genai.ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
        )
        image_bytes = response.candidates[0].content.parts[0]._image_bytes
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return {"success": True, "path": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate images via AI APIs")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--provider", choices=["openai", "gemini"], default="openai", help="API provider")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--size", default="1792x1024", help="Image size (default: 1792x1024)")
    parser.add_argument("--config", help="Config file path")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if config is None:
        print(json.dumps({"success": False, "error": "Config file not found. Run /setup first."}))
        sys.exit(1)

    if args.provider == "openai":
        api_key = config.get("openai_api_key")
        if not api_key:
            print(json.dumps({"success": False, "error": "openai_api_key not set in config"}))
            sys.exit(1)
        result = generate_image_openai(api_key, args.prompt, args.output, args.size)
    else:
        api_key = config.get("gemini_api_key")
        if not api_key:
            print(json.dumps({"success": False, "error": "gemini_api_key not set in config"}))
            sys.exit(1)
        result = generate_image_gemini(api_key, args.prompt, args.output, args.size)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/luthebao/Documents/coding/twitter-agent && python -m pytest tests/test_generate_image.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_image.py tests/test_generate_image.py
git commit -m "feat: image generation script with OpenAI and Gemini support"
```

---

### Task 3: Twitter Posting Script

**Files:**
- Create: `scripts/post_twitter.py`
- Create: `tests/test_post_twitter.py`

- [ ] **Step 1: Write failing tests for Twitter posting**

Write `tests/test_post_twitter.py`:
```python
import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from scripts.post_twitter import post_tweet, post_thread, main


def test_post_tweet_text_only():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = {"id": "123456", "text": "Hello world"}
    mock_client.create_tweet.return_value = mock_response

    with patch("scripts.post_twitter.create_twitter_client", return_value=mock_client):
        result = post_tweet(
            config={"twitter_api_key": "k", "twitter_api_secret": "s", "twitter_access_token": "t", "twitter_access_secret": "a"},
            text="Hello world",
        )
    assert result["success"] is True
    assert result["tweet_id"] == "123456"


def test_post_tweet_with_images():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = {"id": "789", "text": "With image"}
    mock_client.create_tweet.return_value = mock_response

    mock_api = MagicMock()
    mock_media = MagicMock()
    mock_media.media_id = 111
    mock_api.media_upload.return_value = mock_media

    with patch("scripts.post_twitter.create_twitter_client", return_value=mock_client):
        with patch("scripts.post_twitter.create_twitter_api_v1", return_value=mock_api):
            result = post_tweet(
                config={"twitter_api_key": "k", "twitter_api_secret": "s", "twitter_access_token": "t", "twitter_access_secret": "a"},
                text="With image",
                image_paths=["/tmp/fake.png"],
            )
    assert result["success"] is True
    assert result["tweet_id"] == "789"


def test_post_tweet_api_error():
    mock_client = MagicMock()
    mock_client.create_tweet.side_effect = Exception("Rate limit exceeded")

    with patch("scripts.post_twitter.create_twitter_client", return_value=mock_client):
        result = post_tweet(
            config={"twitter_api_key": "k", "twitter_api_secret": "s", "twitter_access_token": "t", "twitter_access_secret": "a"},
            text="Hello",
        )
    assert result["success"] is False
    assert "Rate limit" in result["error"]


def test_post_thread():
    mock_client = MagicMock()
    call_count = 0

    def mock_create_tweet(**kwargs):
        nonlocal call_count
        call_count += 1
        resp = MagicMock()
        resp.data = {"id": str(call_count), "text": kwargs.get("text", "")}
        return resp

    mock_client.create_tweet.side_effect = mock_create_tweet

    with patch("scripts.post_twitter.create_twitter_client", return_value=mock_client):
        result = post_thread(
            config={"twitter_api_key": "k", "twitter_api_secret": "s", "twitter_access_token": "t", "twitter_access_secret": "a"},
            tweets=["First tweet", "Second tweet", "Third tweet"],
        )
    assert result["success"] is True
    assert len(result["tweet_ids"]) == 3
    assert result["tweet_ids"] == ["1", "2", "3"]


def test_main_missing_text(capsys):
    with pytest.raises(SystemExit):
        main(["--config", "/tmp/fake.md"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/luthebao/Documents/coding/twitter-agent && python -m pytest tests/test_post_twitter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.post_twitter'`

- [ ] **Step 3: Implement Twitter posting script**

Write `scripts/post_twitter.py`:
```python
#!/usr/bin/env python3
"""Post tweets and threads via Twitter API v2."""

import argparse
import json
import sys

import tweepy

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
    """Post a thread of tweets, each replying to the previous."""
    try:
        client = create_twitter_client(config)
        tweet_ids = []
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Post tweets via Twitter API")
    parser.add_argument("--text", help="Tweet text (for single tweet)")
    parser.add_argument("--thread", nargs="+", help="Thread texts (multiple tweets)")
    parser.add_argument("--images", help="Comma-separated image paths")
    parser.add_argument("--reply-to", help="Tweet ID to reply to")
    parser.add_argument("--config", help="Config file path")
    args = parser.parse_args(argv)

    if not args.text and not args.thread:
        parser.error("Either --text or --thread is required")

    config = load_config(args.config)
    if config is None:
        print(json.dumps({"success": False, "error": "Config file not found. Run /setup first."}))
        sys.exit(1)

    image_paths = args.images.split(",") if args.images else None

    if args.thread:
        result = post_thread(config, args.thread)
    else:
        result = post_tweet(config, args.text, image_paths=image_paths, reply_to=args.reply_to)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/luthebao/Documents/coding/twitter-agent && python -m pytest tests/test_post_twitter.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/post_twitter.py tests/test_post_twitter.py
git commit -m "feat: Twitter posting script with tweet and thread support"
```

---

### Task 4: Session-Start Hook

**Files:**
- Create: `hooks/hooks.json`

- [ ] **Step 1: Create hooks directory**

```bash
mkdir -p hooks
```

- [ ] **Step 2: Write hooks.json**

Write `hooks/hooks.json`:
```json
{
  "SessionStart": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "prompt",
          "prompt": "Check if the file ~/.claude/twitter-agent.local.md exists. If it does NOT exist, inform the user: 'Twitter Agent plugin is not configured yet. Run /setup to configure your API keys.' If it exists, read its YAML frontmatter and check that at least twitter_api_key and one of openai_api_key or gemini_api_key are non-empty. If keys are missing, inform the user which keys are missing and suggest running /setup."
        }
      ]
    }
  ]
}
```

- [ ] **Step 3: Commit**

```bash
git add hooks/hooks.json
git commit -m "feat: session-start hook for config validation"
```

---

### Task 5: Setup Command

**Files:**
- Create: `commands/setup.md`

- [ ] **Step 1: Create commands directory**

```bash
mkdir -p commands
```

- [ ] **Step 2: Write setup command**

Write `commands/setup.md`:
```markdown
---
name: setup
description: Configure Twitter Agent API keys and preferences
---

# Twitter Agent Setup

Walk the user through configuring their Twitter Agent API keys and preferences. Store config at `~/.claude/twitter-agent.local.md` with YAML frontmatter.

## Process

1. **Check for existing config**: Read `~/.claude/twitter-agent.local.md`. If it exists, show current config (mask API keys — show only last 4 characters) and ask if user wants to update.

2. **Collect API keys one at a time** using AskUserQuestion:

   a. **OpenAI API key** (optional if Gemini provided): "Enter your OpenAI API key (for DALL-E image generation, starts with 'sk-'). Press Enter to skip."

   b. **Gemini API key** (optional if OpenAI provided): "Enter your Google Gemini API key (for Imagen image generation). Press Enter to skip."

   c. Validate that at least one image provider key was given. If neither, ask again.

   d. **Twitter API Key**: "Enter your Twitter API key (from developer.twitter.com)."

   e. **Twitter API Secret**: "Enter your Twitter API secret."

   f. **Twitter Access Token**: "Enter your Twitter access token."

   g. **Twitter Access Token Secret**: "Enter your Twitter access token secret."

3. **Collect preferences**:

   a. **Default image provider**: "Which image provider should be the default? (openai/gemini)" — default to whichever key was provided, or openai if both.

   b. **Workspace root**: "Where should workspaces be stored? (default: ~/twitter-workspaces)" — use default if user presses Enter.

   c. **Auto post**: "Should tweets be posted without confirmation? (yes/no, default: no)"

4. **Write config file**: Save all values to `~/.claude/twitter-agent.local.md` as YAML frontmatter using this format:

```
---
openai_api_key: <value>
gemini_api_key: <value>
twitter_api_key: <value>
twitter_api_secret: <value>
twitter_access_token: <value>
twitter_access_secret: <value>
default_image_provider: <value>
workspace_root: <value>
auto_post: <value>
active_workspace: ""
---
```

5. **Create workspace root directory** if it doesn't exist.

6. **Install Python dependencies**: Run `pip install -r ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt`

7. **Confirm**: "Setup complete! Your Twitter Agent is ready. Try `/workspace create <name>` to get started."
```

- [ ] **Step 3: Commit**

```bash
git add commands/setup.md
git commit -m "feat: /setup command for API key configuration"
```

---

### Task 6: Workspace Command

**Files:**
- Create: `commands/workspace.md`

- [ ] **Step 1: Write workspace command**

Write `commands/workspace.md`:
```markdown
---
name: workspace
description: Manage Twitter Agent workspaces — create, list, switch, import files
args: "<action> [arguments]"
---

# Workspace Management

Manage workspaces for organizing knowledge files and generated content.

## Setup

1. Read config from `~/.claude/twitter-agent.local.md` to get `workspace_root` and `active_workspace`.
2. If config doesn't exist, tell user to run `/setup` first.

## Actions

Parse the first argument to determine the action:

### `create <name>`

1. Convert `<name>` to kebab-case for the folder name.
2. Create directory structure under `<workspace_root>/<name>/`:
   - `knowledge/` — for imported files
   - `content/` — for generated content
3. Create `workspace.yaml` in the workspace root:
   ```yaml
   name: <name>
   description: ""
   created: <today's date YYYY-MM-DD>
   tags: []
   ```
4. Set `active_workspace` to `<name>` in the config file.
5. Confirm: "Workspace '<name>' created and set as active. Import knowledge files with `/workspace import <file>`."

### `list`

1. List all directories in `<workspace_root>/`.
2. For each, read `workspace.yaml` and show name, description, created date.
3. Mark the active workspace with `[active]`.

### `switch <name>`

1. Verify `<workspace_root>/<name>/` exists.
2. Update `active_workspace` in config file to `<name>`.
3. Confirm: "Switched to workspace '<name>'."

### `import <file-or-url>`

1. Check that an active workspace is set. If not, tell user to create or switch to one.
2. **If argument is a local file path**: Copy the file to `<workspace_root>/<active>/knowledge/`.
3. **If argument is a URL**: Use WebFetch to download the page content, save as a markdown file in `<workspace_root>/<active>/knowledge/<domain>-<slug>.md`.
4. Confirm: "Imported '<filename>' into workspace '<active>'."

### No arguments or `help`

Show available actions:
- `/workspace create <name>` — create a new workspace
- `/workspace list` — list all workspaces
- `/workspace switch <name>` — switch active workspace
- `/workspace import <file-or-url>` — import knowledge file
```

- [ ] **Step 2: Commit**

```bash
git add commands/workspace.md
git commit -m "feat: /workspace command for workspace management"
```

---

### Task 7: Summarize Command

**Files:**
- Create: `commands/summarize.md`

- [ ] **Step 1: Write summarize command**

Write `commands/summarize.md`:
```markdown
---
name: summarize
description: Summarize knowledge files in the active workspace into a structured summary
args: "[update]"
---

# Knowledge Summarization

Generate a structured summary from all knowledge files in the active workspace.

## Setup

1. Read config from `~/.claude/twitter-agent.local.md` to get `workspace_root` and `active_workspace`.
2. If no active workspace, tell user to run `/workspace create <name>` or `/workspace switch <name>`.
3. Set `workspace_path` = `<workspace_root>/<active_workspace>`.

## Modes

### Full summarization (default, no arguments)

1. List all files in `<workspace_path>/knowledge/`.
2. If no files found, tell user: "No knowledge files found. Import files with `/workspace import <file>`."
3. Read each file. For large collections (more than 10 files), process in batches of 5 to avoid context overflow.
4. Generate `<workspace_path>/summary.md` with this structure:

```markdown
# <Workspace Name> — Knowledge Summary

## Key Topics
- Topic 1: brief description
- Topic 2: brief description

## Key Facts & Data Points
- Fact 1 (source: filename)
- Fact 2 (source: filename)

## Source Index
- filename1.ext — one-line description of contents
- filename2.ext — one-line description of contents

## Suggested Content Angles
- Angle 1: description of potential Twitter content angle
- Angle 2: description of potential Twitter content angle

Last updated: <today's date YYYY-MM-DD>
```

5. Confirm: "Summary generated at `<workspace_path>/summary.md` with N sources processed."

### Update mode (`/summarize update`)

1. Read existing `<workspace_path>/summary.md`.
2. Check the "Source Index" section to identify already-processed files.
3. List files in `knowledge/` and identify new or modified files (compare file modification times if possible, otherwise process any file not in Source Index).
4. Read only the new/changed files.
5. Append new topics, facts, and sources to the existing summary sections.
6. Update the "Last updated" date.
7. Confirm: "Summary updated with N new sources."
```

- [ ] **Step 2: Commit**

```bash
git add commands/summarize.md
git commit -m "feat: /summarize command for knowledge summarization"
```

---

### Task 8: Generate-Content Command

**Files:**
- Create: `commands/generate-content.md`

- [ ] **Step 1: Write generate-content command**

Write `commands/generate-content.md`:
```markdown
---
name: generate-content
description: Generate Twitter post drafts from workspace knowledge summary
args: "[topic|list|edit <file>]"
---

# Twitter Content Generation

Create Twitter post drafts from the active workspace's knowledge summary.

## Setup

1. Read config from `~/.claude/twitter-agent.local.md` to get `workspace_root` and `active_workspace`.
2. If no active workspace, tell user to create or switch to one.
3. Set `workspace_path` = `<workspace_root>/<active_workspace>`.

## Actions

### Generate new content (default or with topic)

1. Read `<workspace_path>/summary.md`. If it doesn't exist, tell user to run `/summarize` first.
2. If a topic argument was given, focus content on that topic from the summary.
3. If no topic, pick the most compelling angle from "Suggested Content Angles".
4. Generate Twitter content. Choose the best format:
   - **Single tweet**: For concise facts or announcements (max 280 characters)
   - **Thread**: For explanations, tutorials, or multi-faceted topics (3-7 tweets)
5. Save as `<workspace_path>/content/<YYYY-MM-DD>-<topic-slug>.md` with frontmatter:

```markdown
---
type: tweet|thread
topic: "Topic description"
status: draft
created: <today's date YYYY-MM-DD>
posted_at:
tweet_ids: []
images: []
---

<content here>
```

For threads, use `## Tweet 1`, `## Tweet 2`, etc. as headers.

6. Confirm: "Draft created at `<path>`. Review it, then use `/generate-image` for visuals or `/post-twitter` to publish."

### `list`

1. List all `.md` files in `<workspace_path>/content/`.
2. For each, read the frontmatter and display: filename, type, topic, status, created date.
3. Group by status: drafts first, then posted.

### `edit <file>`

1. Read the specified draft file.
2. Show current content to user.
3. Ask user what changes they want.
4. Apply changes and save.
5. Confirm: "Draft updated."
```

- [ ] **Step 2: Commit**

```bash
git add commands/generate-content.md
git commit -m "feat: /generate-content command for Twitter draft creation"
```

---

### Task 9: Generate-Image Command

**Files:**
- Create: `commands/generate-image.md`

- [ ] **Step 1: Write generate-image command**

Write `commands/generate-image.md`:
```markdown
---
name: generate-image
description: Generate images for Twitter post drafts using AI image generation APIs
args: "[draft-file] [--prompt \"custom prompt\"]"
---

# Image Generation

Generate banner images for Twitter post drafts using OpenAI DALL-E or Google Gemini Imagen.

## Setup

1. Read config from `~/.claude/twitter-agent.local.md` to get `workspace_root`, `active_workspace`, and `default_image_provider`.
2. If no active workspace, tell user to create or switch to one.
3. Set `workspace_path` = `<workspace_root>/<active_workspace>`.

## Process

### Determine the draft

- If a draft file argument is provided, use that file.
- If no argument, find the most recent `.md` file in `<workspace_path>/content/` with `status: draft`.
- If no drafts found, tell user to run `/generate-content` first.

### Craft the image prompt

- If `--prompt` argument is provided, use that directly.
- Otherwise, read the draft content and craft an image prompt that:
  - Captures the main theme of the tweet/thread
  - Is descriptive and specific for AI image generation
  - Requests a style suitable for Twitter banners (clean, professional, eye-catching)
  - Specifies landscape orientation

### Generate the image

Run the Python script:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/generate_image.py \
  --prompt "<crafted prompt>" \
  --provider <default_image_provider from config> \
  --output "<workspace_path>/content/<YYYY-MM-DD>-<topic-slug>-banner.png" \
  --size "1792x1024" \
  --config ~/.claude/twitter-agent.local.md
```

### Handle result

1. Parse the JSON output from the script.
2. If `success: true`:
   - Update the draft file's `images:` frontmatter to include the generated image path.
   - Show the generated image to the user (use Read tool on the image file).
   - Confirm: "Image generated at `<path>` and linked to draft."
3. If `success: false`:
   - Show the error message.
   - Suggest: "Try again with a different prompt using `/generate-image --prompt \"...\"`"
```

- [ ] **Step 2: Commit**

```bash
git add commands/generate-image.md
git commit -m "feat: /generate-image command for AI image generation"
```

---

### Task 10: Post-Twitter Command

**Files:**
- Create: `commands/post-twitter.md`

- [ ] **Step 1: Write post-twitter command**

Write `commands/post-twitter.md`:
```markdown
---
name: post-twitter
description: Post Twitter drafts — publish tweets and threads with images
args: "[draft-file|list]"
---

# Twitter Posting

Publish draft content to Twitter using the Twitter API.

## Setup

1. Read config from `~/.claude/twitter-agent.local.md` to get `workspace_root`, `active_workspace`, and `auto_post`.
2. If no active workspace, tell user to create or switch to one.
3. Set `workspace_path` = `<workspace_root>/<active_workspace>`.

## Actions

### Post a draft (default or with file argument)

1. **Select draft**:
   - If a file argument is given, use that file.
   - If no argument, find the most recent `.md` file in `<workspace_path>/content/` with `status: draft`.
   - If no drafts found, tell user to run `/generate-content` first.

2. **Read and display draft**: Show the full content (text + any linked images) to the user.

3. **Confirm** (unless `auto_post: true` in config):
   - Ask: "Ready to post this to Twitter? (yes/no)"
   - If no, stop and tell user they can edit with `/generate-content edit <file>`.

4. **Post**:
   - Read the draft frontmatter for `type` and `images`.
   - **Single tweet**: Run:
     ```bash
     python ${CLAUDE_PLUGIN_ROOT}/scripts/post_twitter.py \
       --text "<tweet text>" \
       --images "<comma-separated image paths if any>" \
       --config ~/.claude/twitter-agent.local.md
     ```
   - **Thread**: Run:
     ```bash
     python ${CLAUDE_PLUGIN_ROOT}/scripts/post_twitter.py \
       --thread "<tweet 1>" "<tweet 2>" "<tweet 3>" \
       --config ~/.claude/twitter-agent.local.md
     ```

5. **Handle result**:
   - Parse JSON output.
   - If `success: true`:
     - Update draft frontmatter: `status: posted`, `posted_at: <now>`, `tweet_ids: [<ids>]`.
     - Confirm: "Posted! Tweet URL: https://twitter.com/i/status/<tweet_id>"
   - If `success: false`:
     - Show error message.
     - Suggest possible fixes (rate limit → wait, auth error → re-run `/setup`).

### `list`

1. List all `.md` files in `<workspace_path>/content/` with `status: draft`.
2. Show: filename, type, topic, created date.
3. If no drafts, tell user to run `/generate-content`.
```

- [ ] **Step 2: Commit**

```bash
git add commands/post-twitter.md
git commit -m "feat: /post-twitter command for publishing to Twitter"
```

---

### Task 11: Final Integration & README

**Files:**
- Verify: all files exist and are consistent

- [ ] **Step 1: Run all tests**

```bash
cd /Users/luthebao/Documents/coding/twitter-agent && python -m pytest tests/ -v
```
Expected: All tests PASS

- [ ] **Step 2: Verify plugin structure**

```bash
find . -type f | sort
```

Expected output:
```
./.claude-plugin/plugin.json
./commands/generate-content.md
./commands/generate-image.md
./commands/post-twitter.md
./commands/setup.md
./commands/summarize.md
./commands/workspace.md
./config.template.yaml
./hooks/hooks.json
./scripts/generate_image.py
./scripts/post_twitter.py
./scripts/requirements.txt
./scripts/utils/__init__.py
./scripts/utils/config.py
./tests/__init__.py
./tests/test_config.py
./tests/test_generate_image.py
./tests/test_post_twitter.py
```

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete Twitter Agent Claude Code plugin"
```
