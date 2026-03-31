# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Code plugin for social media content creation from knowledge bases. Single-user personal tool — no database, no auth, no frontend. All state lives in YAML config and markdown files on disk.

## Installing the Plugin

```bash
# Install into Claude Code (run from anywhere)
claude plugin add /path/to/social-agent/plugin

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
python -m pytest tests/test_post.py::test_post_thread -v

# Install dependencies
pip install -r plugin/scripts/requirements.txt
```

## Architecture

**Plugin commands** (markdown in `plugin/commands/`) instruct Claude what to do. **Python scripts** (in `plugin/scripts/`) handle external API calls and return JSON. Commands call scripts via `python ${CLAUDE_PLUGIN_ROOT}/scripts/<script>.py` with CLI arguments.

### Repo Layout

```
social-agent/
├── CLAUDE.md
├── plugin/                            # The Claude Code plugin (install this)
│   ├── .claude-plugin/plugin.json     # Plugin manifest
│   ├── commands/                      # 7 slash commands
│   ├── hooks/hooks.json               # SessionStart hook
│   ├── scripts/                       # Python scripts (kie.ai, social media APIs)
│   │   ├── utils/config.py            # Config loader
│   │   ├── utils/draft.py             # Draft file reader/writer
│   │   ├── generate_image.py          # kie.ai image generation
│   │   ├── post.py                    # Unified posting entry point
│   │   └── platforms/                 # Per-platform posting logic
│   │       ├── base.py                # Base platform class
│   │       └── twitter.py             # Twitter posting
│   └── config.template.yaml           # Config reference
└── docs/                              # Design specs and plans
```

### Config System

Config lives at `.social-agent.yaml` in the user's project directory (CWD), not in `~/.claude/`. Plain YAML, no frontmatter. Loaded by `plugin/scripts/utils/config.py` — `get_config_path()` returns `os.path.join(os.getcwd(), ".social-agent.yaml")`. Platform credentials are nested under platform keys (e.g., `twitter:`, `reddit:`, `threads:`, `facebook:`).

### Python Scripts Run From Any CWD

Scripts include `sys.path.insert(0, _PLUGIN_ROOT)` at the top so `from scripts.utils.config import load_config` works regardless of the working directory. This is critical — commands invoke scripts from the user's project folder, not the plugin directory.

### Image Generation (kie.ai) is Async Polling

`generate_image.py` submits a task, polls every 3 seconds (max 60 attempts), then downloads the result. Three API calls: submit → poll status → get download URL → download image.

### Platform Posting

`post.py` reads the draft's `platform` frontmatter field and routes to the correct platform module in `platforms/`. Each platform module (e.g., `platforms/twitter.py`) implements posting logic using platform-specific APIs. Twitter uses `tweepy.Client` (v2) for posting tweets and `tweepy.API` (v1.1) for media uploads.

### Content Draft Format

Drafts in `contents/` use YAML frontmatter tracking: `platform`, `status` (draft/posted), `created_at`, `posted_at`, `post_ids`, `has_images`, `images` list. File naming: `YYYY-MM-DD_<topic-slug>_<type>_<platform>.md`.

### User's Project Folder Structure

When a user runs `/setup` in their project:

```
my-project/
├── .social-agent.yaml     # Config with API keys
├── knowledges/            # Imported files (pdf, md, csv, etc.)
├── contents/              # Social media content drafts (.md)
├── images/                # Generated images
└── summary.md             # Knowledge summary
```

### SessionStart Hook

Auto-creates missing directories (`knowledges/`, `contents/`, `images/`) and moves misplaced files from project root into correct folders. Also validates config exists and lists which platforms are configured.

## Testing

All tests use `unittest.mock` — no real API calls. HTTP requests mocked via `patch("scripts.generate_image.requests")`. Time mocked to skip polling delays.
