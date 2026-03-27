# Twitter Agent — Claude Code Plugin Design

## Overview

A Claude Code plugin for managing Twitter content creation from knowledge bases. The plugin provides skills that let the agent manage workspaces (folders of knowledge files), summarize knowledge, generate Twitter posts and images, and publish to Twitter. Python scripts handle all external API calls (image generation, Twitter posting).

Personal tool — single user, no auth, no frontend, no database.

## Plugin Structure

```
twitter-agent/
├── plugin.json                    # Plugin manifest
├── config.template.yaml           # Template showing required keys
├── scripts/
│   ├── requirements.txt           # Python dependencies
│   ├── generate_image.py          # Image generation via APIs
│   ├── post_twitter.py            # Twitter API posting
│   └── utils/
│       └── config.py              # Config loader (reads .local.md)
├── skills/
│   ├── setup.md                   # First-time setup / API key config
│   ├── workspace.md               # Workspace management
│   ├── summarize.md               # Knowledge summarization
│   ├── generate-content.md        # Twitter content generation
│   ├── generate-image.md          # Image generation
│   └── post-twitter.md            # Post to Twitter
└── hooks/
    └── session-start.md           # Check config on session start
```

## Config System

Config stored at `~/.claude/twitter-agent.local.md` (user home directory) with YAML frontmatter:

```yaml
---
openai_api_key: sk-...
gemini_api_key: AI...
twitter_api_key: ...
twitter_api_secret: ...
twitter_access_token: ...
twitter_access_secret: ...
default_image_provider: openai
workspace_root: ~/twitter-workspaces
auto_post: false
active_workspace: ai-news
---
```

### Setup Skill (`/setup`)

- Walks through each required API key one at a time using `AskUserQuestion`
- Validates format where possible (e.g., OpenAI keys start with `sk-`)
- Writes the config file
- Configurable: `workspace_root`, `default_image_provider`, `auto_post`
- Re-runnable anytime to update keys

### Session-Start Hook

- Fires on every new Claude Code session
- Checks if config file exists and has required keys
- If missing or incomplete: informs user and suggests running `/setup`
- Lightweight — config existence check only

### Required Keys

- Twitter API (4 keys): `twitter_api_key`, `twitter_api_secret`, `twitter_access_token`, `twitter_access_secret`
- At least one image provider: `openai_api_key` or `gemini_api_key`

## Workspace Management

### Concept

A workspace is a folder on disk. No database, no index — the agent reads the filesystem directly.

### Folder Structure

```
~/twitter-workspaces/              # Root (configurable)
├── ai-news/
│   ├── knowledge/                 # Raw imported files
│   │   ├── paper1.pdf
│   │   ├── notes.md
│   │   └── data.csv
│   ├── summary.md                 # Agent-generated summary
│   ├── content/                   # Generated Twitter content
│   │   ├── 2026-03-27-thread.md
│   │   └── 2026-03-27-banner.png
│   └── workspace.yaml             # Workspace metadata
├── web-dev/
│   └── ...
```

### Workspace Metadata (`workspace.yaml`)

```yaml
name: AI News
description: Latest AI research and news
created: 2026-03-27
tags: [ai, research, ml]
```

### Workspace Skill (`/workspace`)

- `/workspace create <name>` — create new workspace folder structure
- `/workspace list` — list all workspaces
- `/workspace switch <name>` — set active workspace by writing `active_workspace: <name>` to the config file; other skills read this value to determine which workspace to operate on
- `/workspace import <file-or-url>` — for local files: copy into active workspace's `knowledge/` folder; for URLs: download page content and save as markdown using the agent's WebFetch capability

## Knowledge Summarization

### Summarize Skill (`/summarize`)

Reads all files in the active workspace's `knowledge/` folder and generates `summary.md`.

### Process

1. Agent lists files in `knowledge/`
2. Reads each file (agent handles PDFs, markdown, text, CSV, JSON, images)
3. Generates structured `summary.md`

### Summary Format

```markdown
# <Workspace Name> — Knowledge Summary

## Key Topics
- Topic 1: ...
- Topic 2: ...

## Key Facts & Data Points
- ...

## Source Index
- paper1.pdf — describes...
- notes.md — contains...

## Suggested Content Angles
- Angle 1: ...
- Angle 2: ...

Last updated: YYYY-MM-DD
```

### Commands

- `/summarize` — full regeneration of summary
- `/summarize update` — only process new/changed files, append to existing

The skill instructs the agent to read files in batches if there are many, to avoid context overflow.

## Twitter Content Generation

### Generate-Content Skill (`/generate-content`)

Creates Twitter post drafts from the workspace's `summary.md`.

### Content Types

- Single tweet (max 280 chars)
- Thread (numbered series)
- Quote tweet / reply format

### Draft File Format (`content/YYYY-MM-DD-topic-slug.md`)

```markdown
---
type: thread
topic: "New GPT-5 capabilities"
status: draft
created: 2026-03-27
posted_at:
tweet_ids: []
images: []
---

## Tweet 1
The latest research on GPT-5 shows...

## Tweet 2
What makes this interesting is...

## Tweet 3
Key takeaway: ...
```

### Commands

- `/generate-content` — generate new content, agent picks best angles from summary
- `/generate-content <topic>` — generate about a specific topic
- `/generate-content list` — list all drafts with status
- `/generate-content edit <file>` — revise an existing draft

## Image Generation

### Generate-Image Skill (`/generate-image`)

Creates images by calling a Python script that hits external APIs.

### Python Script (`scripts/generate_image.py`)

- Arguments: `--prompt`, `--provider` (openai/gemini), `--output`, `--size` (default: 1200x675 for Twitter banners)
- Reads API keys from config file (`~/.claude/twitter-agent.local.md` — path passed via `--config` argument)
- Calls appropriate API (OpenAI DALL-E / Gemini Imagen)
- Saves image to output path
- Returns file path on success, error message on failure

### Skill Behavior

1. Agent reads content draft to understand context
2. Agent crafts image prompt based on topic
3. Calls Python script via Bash
4. Updates draft's `images:` frontmatter with generated file path

### Commands

- `/generate-image` — generate image for most recent draft
- `/generate-image <draft-file>` — generate for specific draft
- `/generate-image --prompt "custom prompt"` — custom prompt

## Twitter Posting

### Post-Twitter Skill (`/post-twitter`)

Publishes content using a Python script that calls the Twitter API.

### Python Script (`scripts/post_twitter.py`)

- Arguments: `--text`, `--images` (optional, comma-separated paths), `--reply-to` (tweet ID, for threads)
- Reads Twitter API keys from config file (`~/.claude/twitter-agent.local.md` — path passed via `--config` argument)
- Posts tweet, returns tweet ID and URL on success
- For threads: posts sequentially, each reply chained to previous

### Skill Behavior

1. Agent reads draft file
2. Single tweet: one call to script
3. Thread: calls script per tweet, passing `--reply-to` with previous tweet ID
4. Updates draft frontmatter: `status: posted`, `posted_at`, `tweet_ids`
5. Includes `--images` flag if images referenced

### Safety

- By default, agent shows content and asks for confirmation before posting
- Set `auto_post: true` in config to skip confirmation

### Commands

- `/post-twitter` — post most recent draft
- `/post-twitter <draft-file>` — post specific draft
- `/post-twitter list` — show all drafts ready to post

## Skills Summary

| Skill | Purpose |
|-------|---------|
| `/setup` | Configure API keys and preferences |
| `/workspace` | Create, list, switch, import files |
| `/summarize` | Generate summary.md from knowledge files |
| `/generate-content` | Create Twitter post drafts from summary |
| `/generate-image` | Generate banner images via Python script |
| `/post-twitter` | Post drafts to Twitter via Python script |

## Python Dependencies

Expected in `scripts/requirements.txt`:
- `openai` — DALL-E image generation
- `google-generativeai` — Gemini Imagen
- `tweepy` — Twitter API v2
- `pyyaml` — config parsing
- `requests` — HTTP calls
