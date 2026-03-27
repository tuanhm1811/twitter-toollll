# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Code plugin for Twitter content creation from knowledge bases. Single-user personal tool — no database, no auth, no frontend. All state lives in YAML config and markdown files on disk.

## Installing the Plugin

```bash
# Install into Claude Code (run from anywhere)
claude plugin add /path/to/twitter-agent/plugin

# Or if you're in this repo
claude plugin add ./plugin

# Install Python dependencies (required for scripts)
pip install -r plugin/scripts/requirements.txt
```

The plugin directory is `plugin/` — this is what gets registered with Claude Code. The `.claude-plugin/plugin.json` manifest inside it defines the plugin name and version.

## Development Commands

```bash
# Run all tests (from repo root)
cd plugin && python -m pytest ../tests/ -v

# Run a single test file
python -m pytest tests/test_config.py -v

# Run a single test
python -m pytest tests/test_post_twitter.py::test_post_thread -v

# Install dependencies
pip install -r plugin/scripts/requirements.txt
```

## Architecture

**Plugin commands** (markdown in `plugin/commands/`) instruct Claude what to do. **Python scripts** (in `plugin/scripts/`) handle external API calls and return JSON. Commands call scripts via `python ${CLAUDE_PLUGIN_ROOT}/scripts/<script>.py` with CLI arguments.

### Repo Layout

```
twitter-agent/
├── CLAUDE.md
├── plugin/                            # The Claude Code plugin (install this)
│   ├── .claude-plugin/plugin.json     # Plugin manifest
│   ├── commands/                      # 7 slash commands
│   ├── hooks/hooks.json               # SessionStart hook
│   ├── scripts/                       # Python scripts (kie.ai, Twitter API)
│   │   ├── utils/config.py            # Config loader
│   │   ├── generate_image.py          # kie.ai image generation
│   │   └── post_twitter.py            # Twitter posting
│   └── config.template.yaml           # Config reference
└── docs/                              # Design specs and plans
```

### Config System

Config lives at `.twitter-agent.yaml` in the user's project directory (CWD), not in `~/.claude/`. Plain YAML, no frontmatter. Loaded by `plugin/scripts/utils/config.py` — `get_config_path()` returns `os.path.join(os.getcwd(), ".twitter-agent.yaml")`.

### Python Scripts Run From Any CWD

Scripts include `sys.path.insert(0, _PLUGIN_ROOT)` at the top so `from scripts.utils.config import load_config` works regardless of the working directory. This is critical — commands invoke scripts from the user's project folder, not the plugin directory.

### Image Generation (kie.ai) is Async Polling

`generate_image.py` submits a task, polls every 3 seconds (max 60 attempts), then downloads the result. Three API calls: submit → poll status → get download URL → download image.

### Twitter Posting Uses Two API Versions

`tweepy.Client` (v2) for posting tweets. `tweepy.API` (v1.1) for media uploads — v2 doesn't support media yet. Both require the same 4 credentials.

### Content Draft Format

Drafts in `contents/` use YAML frontmatter tracking: `status` (draft/posted), `created_at`, `posted_at`, `tweet_ids`, `has_images`, `images` list. File naming: `YYYY-MM-DD_<topic-slug>_<type>.md`.

### User's Project Folder Structure

When a user runs `/setup` in their project:

```
my-project/
├── .twitter-agent.yaml    # Config with API keys
├── knowledges/            # Imported files (pdf, md, csv, etc.)
├── contents/              # Twitter content drafts (.md)
├── images/                # Generated images
└── summary.md             # Knowledge summary
```

### SessionStart Hook

Auto-creates missing directories (`knowledges/`, `contents/`, `images/`) and moves misplaced files from project root into correct folders. Also validates config exists with required API keys.

## Testing

All tests use `unittest.mock` — no real API calls. HTTP requests mocked via `patch("scripts.generate_image.requests")`. Time mocked to skip polling delays.
