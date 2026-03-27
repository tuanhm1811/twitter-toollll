---
description: Generate Twitter post drafts from project knowledge
argument-hint: [topic|list|edit <file>]
---

Create Twitter post drafts from the current project's knowledge summary.

## Setup

1. Check that `./contents/` directory exists. If not, tell user: "No contents/ directory found. Run `/setup` or `/init` first."

## Content File Template

All content drafts are saved as `.md` files in `./contents/` with the following format:

### File Naming Convention

```
YYYY-MM-DD_<topic-slug>_<type>.md
```

Examples:
- `2026-03-27_ai-model-comparison_thread.md`
- `2026-03-27_gpt5-release_tweet.md`
- `2026-03-28_ml-trends-2026_thread.md`

### File Content Template

```markdown
---
type: tweet | thread
topic: "Short topic description"
status: draft | posted
created_at: "YYYY-MM-DD HH:MM"
posted_at: ""
tweet_ids: []
has_images: false
images:
  - path: ""
    description: ""
---

## Tweet 1
Content of the first tweet (max 280 characters)...

## Tweet 2
Content of the second tweet...

## Tweet 3
Content of the third tweet...
```

**Frontmatter fields:**
- `type` — `tweet` (single) or `thread` (multiple tweets)
- `topic` — short description of the content topic
- `status` — `draft` (not yet posted) or `posted` (already published)
- `created_at` — when the draft was created
- `posted_at` — when it was posted to Twitter (empty if draft)
- `tweet_ids` — list of Twitter tweet IDs after posting (empty if draft)
- `has_images` — whether images are attached to this content
- `images` — list of image objects with `path` and `description`

## Actions

### Generate new content (default or with topic)

1. Read `./summary.md`. If it doesn't exist, tell user to run `/summarize` first.
2. If a topic argument was given, focus content on that topic from the summary.
3. If no topic, pick the most compelling angle from "Suggested Content Angles".
4. Generate Twitter content. Choose the best format:
   - **Single tweet**: For concise facts or announcements (max 280 characters)
   - **Thread**: For explanations, tutorials, or multi-faceted topics (3-7 tweets)
5. Save to `./contents/` using the file naming convention and content template above.
6. Confirm: "Draft created at `<path>`. Review it, then use `/generate-image` for visuals or `/post-twitter` to publish."

### `list`

1. List all `.md` files in `./contents/`.
2. For each, read the frontmatter and display: filename, type, topic, status, created_at, has_images.
3. Group by status: drafts first, then posted.
4. Show a summary like:
   ```
   Drafts:
     - 2026-03-27_ai-trends_thread.md — thread — "AI Trends 2026" — no images
     - 2026-03-27_new-model_tweet.md — tweet — "New Model Release" — 1 image

   Posted:
     - 2026-03-26_ml-basics_thread.md — thread — "ML Basics" — posted 2026-03-26
   ```

### `edit <file>`

1. Read the specified draft file.
2. Show current content to user.
3. Ask user what changes they want.
4. Apply changes and save.
5. Confirm: "Draft updated."
