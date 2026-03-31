# Social Agent — Multi-Platform Content Creation

**Date:** 2026-03-30
**Status:** Approved
**Scope:** Extend twitter-agent plugin to support Facebook, Twitter, Threads, Reddit

---

## 1. Overview

Extend the existing `twitter-agent` Claude Code plugin into `social-agent` — a multi-platform content creation and posting tool. Content is generated from knowledge bases, formatted per platform, and posted via platform APIs.

Single-user personal tool. No database, no auth, no frontend. All state lives in YAML config and markdown files on disk.

### Supported Platforms

| Platform | Library | Content Types |
|----------|---------|---------------|
| Twitter | `tweepy` | tweet, thread (280 chars/tweet) |
| Reddit | `praw` | submission (title + markdown body, no char limit) |
| Threads | `requests` (Meta API) | post, thread (500 chars/post) |
| Facebook | `requests` (Graph API) | post (no practical char limit) |

---

## 2. Approach

**Approach 2: Shared base + platform modules.** Shared logic (parse draft, update frontmatter) in `utils/draft.py`. Each platform implements only its posting logic in `platforms/<name>.py`. Single entry point `post.py` routes by platform field in frontmatter.

### Why This Approach

- `parse_draft()` and `update_frontmatter()` already exist in `post_twitter.py` — just move to `utils/draft.py`
- Adding a new platform = 1 file in `platforms/`
- Each platform testable independently

---

## 3. Rename & Config

### Rename

| Current | New |
|---------|-----|
| Plugin name: `twitter-agent` | `social-agent` |
| Config: `.twitter-agent.yaml` | `.social-agent.yaml` |
| Manifest description | "Manage social media content creation from knowledge bases" |

### Config Structure (`.social-agent.yaml`)

```yaml
# Image generation
kie_api_key: ""

# Platform credentials — only fill platforms you use
twitter:
  api_key: ""
  api_secret: ""
  access_token: ""
  access_secret: ""

reddit:
  client_id: ""
  client_secret: ""
  username: ""
  password: ""

threads:
  access_token: ""

facebook:
  page_access_token: ""
  page_id: ""

# Preferences
auto_post: false
```

### `/setup` Flow

1. Ask kie.ai API key (shared)
2. Ask: "Which platforms do you want to configure? (twitter, reddit, threads, facebook — can select multiple)"
3. For each selected platform → show step-by-step guide to get credentials → collect keys
4. Ask `auto_post` preference
5. Write config, create directories, install dependencies
6. Warn about `.gitignore`

Subcommand: `/setup <platform>` to configure a single platform.

SessionStart hook checks `.social-agent.yaml`, lists which platforms are configured vs unconfigured. Does not require all platforms.

---

## 4. Content Draft Format

### Frontmatter

```yaml
---
platform: twitter | reddit | threads | facebook
type: tweet | thread | post | submission
topic: "Short topic description"
status: draft | posted
created_at: "YYYY-MM-DD HH:MM"
posted_at: ""
post_ids: []
has_images: false
images:
  - path: ""
    description: ""
# Reddit-specific
subreddit: ""
title: ""
# Facebook-specific
visibility: "public"
---
```

Key change: `tweet_ids` → `post_ids` (platform-agnostic).

### File Naming

```
YYYY-MM-DD_<topic-slug>_<type>_<platform>.md
```

Examples:
- `2026-03-30_ai-trends_thread_twitter.md`
- `2026-03-30_ai-trends_submission_reddit.md`
- `2026-03-30_ai-trends_post_facebook.md`
- `2026-03-30_ai-trends_thread_threads.md`

### Platform Content Rules

**Twitter** (tweet / thread):
- 280 chars per tweet
- Body split by `## Tweet N` headings
- Script posts each as reply to previous (thread)

**Reddit** (submission):
- Title in frontmatter `title` field (max 300 chars)
- Body under `## Body` heading, full markdown
- `subreddit` field specifies target subreddit

**Threads** (post / thread):
- 500 chars per post
- Body split by `## Post N` headings
- Similar to Twitter threading

**Facebook** (post):
- No practical char limit
- Entire body is one post
- `visibility` field controls audience

---

## 5. Scripts Architecture

### Directory Structure

```
scripts/
├── post.py                    # Single entry point for posting
├── generate_image.py          # Unchanged
├── platforms/
│   ├── __init__.py
│   ├── base.py                # Shared: validate config, format result
│   ├── twitter.py             # post(config, tweets, images) — tweepy
│   ├── reddit.py              # post(config, title, body, subreddit, images) — praw
│   ├── threads.py             # post(config, posts, images) — requests (Meta API)
│   └── facebook.py            # post(config, body, images, visibility) — requests (Graph API)
├── utils/
│   ├── __init__.py
│   ├── config.py              # load_config / save_config (updated path)
│   └── draft.py               # parse_draft(), update_frontmatter(), resolve_image_paths()
└── requirements.txt
```

### `post.py` Entry Point

```
python post.py --file contents/2026-03-30_ai-trends_thread_twitter.md
```

Logic:
1. `parse_draft()` → get `platform` from frontmatter
2. Route to `platforms/<platform>.py`
3. Call platform's `post()` function
4. On success → `update_frontmatter()` (status, posted_at, post_ids)
5. Return JSON result

### `utils/draft.py` — Shared Logic

Extracted from current `post_twitter.py`:
- `parse_draft(file_path)` → (frontmatter, content_parts)
- `update_frontmatter(file_path, updates)` → update YAML fields
- `resolve_image_paths(frontmatter, draft_dir)` → resolve relative paths

### Each `platforms/<name>.py` Implements

```python
def post(config, content, images=None):
    """Post content to platform. Return dict with success/post_ids."""
    ...

def validate_config(config):
    """Check required credentials exist. Return error message or None."""
    ...
```

### Dependencies (`requirements.txt`)

```
requests>=2.28.0
tweepy>=4.14.0
praw>=7.7.0
pyyaml>=6.0
```

Threads and Facebook use `requests` directly (Meta Graph API).

---

## 6. Commands

### Retained (with reference updates)

| Command | Changes |
|---------|---------|
| `/init` | `.twitter-agent.yaml` → `.social-agent.yaml` |
| `/import` | No changes |
| `/summarize` | "Twitter content angle" → "Social media content angle" |
| `/generate-image` | No changes |

### Modified

**`/setup`** — Platform selection + credential guides:
```
/setup                    → Full setup (step by step)
/setup twitter            → Setup only Twitter
/setup reddit             → Setup only Reddit
```

**`/generate-content`** — Added `--platform` flag:
```
/generate-content --platform twitter "topic"
/generate-content --platform reddit "topic"
/generate-content list
/generate-content edit <file>
```

`--platform` is required when generating new content (no default).

`list` displays all drafts grouped by platform then by status.

### New

**`/post`** — Replaces `/post-twitter`:
```
/post <draft-file>        → Read platform from frontmatter, post accordingly
/post                     → Post most recent draft (any platform)
/post list                → List all drafts ready to post, grouped by platform
```

### Removed

`/post-twitter` → replaced by `/post`

### Total: 7 commands

`/setup`, `/init`, `/import`, `/summarize`, `/generate-content`, `/generate-image`, `/post`

---

## 7. Build Order

Sequential, test each platform before moving to next.

### Phase 0: Refactor & Rename

- Rename plugin → `social-agent`
- Config `.twitter-agent.yaml` → `.social-agent.yaml`
- Extract `post_twitter.py` → `utils/draft.py` + `platforms/twitter.py` + `post.py`
- Update all command references
- Update hook
- **Verify**: Twitter posting still works on new architecture

### Phase 1: Twitter (verify)

- End-to-end test on new architecture
- Setup credentials → generate content → post
- **Test with user**: Create Twitter draft, post live

### Phase 2: Reddit

- Add `platforms/reddit.py` (using `praw`)
- Update `/setup` — add Reddit credential guide
- Update `/generate-content` — Reddit format rules
- Update `/post` — Reddit routing
- **Test with user**: Setup Reddit → generate → post live

### Phase 3: Threads

- Add `platforms/threads.py` (Meta Threads API, using `requests`)
- Update `/setup`, `/generate-content`, `/post`
- **Test with user**: Setup → generate → post live

### Phase 4: Facebook

- Add `platforms/facebook.py` (Graph API, using `requests`)
- Update `/setup`, `/generate-content`, `/post`
- **Test with user**: Setup → generate → post live

Each phase completes before the next begins.

---

## 8. Testing Strategy

All tests use `unittest.mock` — no real API calls.

- `tests/test_config.py` — Config loader with new structure
- `tests/test_draft.py` — parse_draft, update_frontmatter for all formats
- `tests/test_post.py` — Entry point routing
- `tests/test_platform_twitter.py` — Twitter posting (mock tweepy)
- `tests/test_platform_reddit.py` — Reddit posting (mock praw)
- `tests/test_platform_threads.py` — Threads posting (mock requests)
- `tests/test_platform_facebook.py` — Facebook posting (mock requests)

Plus live testing with user at each phase.
