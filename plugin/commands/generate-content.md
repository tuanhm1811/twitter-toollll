---
description: Generate social media post drafts from project knowledge
argument-hint: --platform <name> [topic] | list | edit <file>
---

Create social media post drafts from the current project's knowledge summary, formatted for the target platform.

## Setup

1. Check that `./contents/` directory exists. If not, tell user: "No contents/ directory found. Run `/setup` or `/init` first."

## Content File Template

All content drafts are saved as `.md` files in `./contents/` with the following format:

### File Naming Convention

```
YYYY-MM-DD_<topic-slug>_<type>_<platform>.md
```

Examples:
- `2026-03-30_ai-trends_thread_twitter.md`
- `2026-03-30_ai-trends_submission_reddit.md`
- `2026-03-30_ai-trends_post_facebook.md`
- `2026-03-30_ai-trends_thread_threads.md`

### File Content Template

```markdown
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
# Reddit-specific (include only for reddit)
subreddit: ""
title: ""
# Facebook-specific (include only for facebook)
visibility: "public"
---

[Content body — format depends on platform]
```

### Platform-Specific Body Formats

**Twitter** (type: tweet or thread):
- Max 280 characters per tweet
- Single tweet: plain text body
- Thread: split into `## Tweet 1`, `## Tweet 2`, etc.
- 3-7 tweets per thread recommended

**Reddit** (type: submission):
- `title` field in frontmatter (max 300 characters)
- `subreddit` field in frontmatter (target subreddit, without r/ prefix)
- Body under `## Body` heading, full markdown supported
- No character limit on body

**Threads** (type: post or thread):
- Max 500 characters per post
- Single post: plain text body
- Thread: split into `## Post 1`, `## Post 2`, etc.
- 3-7 posts per thread recommended

**Facebook** (type: post):
- No practical character limit
- Entire body is one post, plain text
- `visibility` field: "public" (default)

## Actions

### Generate new content (`--platform <name> [topic]`)

1. `--platform` is required. If not provided, tell user: "Please specify a platform: `/generate-content --platform twitter|reddit|threads|facebook [topic]`"
2. **Ask immediately:** "Would you like to generate a banner image for this content? (default: yes for scheduled tasks)" — If the user declines, skip image generation. If they agree or don't respond (scheduled task), proceed with image generation after step 7.
3. Read `./summary.md`. If it doesn't exist, tell user to run `/summarize` first.
4. If a topic argument was given, focus content on that topic from the summary.
5. If no topic, pick the most compelling angle from "Suggested Content Angles".
6. Generate content following the platform-specific format rules above.
7. Save to `./contents/` using the file naming convention.
8. Confirm: "Draft created at `<path>`."
9. **If image generation was agreed to (or this is a scheduled task):** Run `/generate-image` for this draft. The image will be shared across all drafts with the same topic slug.

### `list`

1. List all `.md` files in `./contents/`.
2. For each, read the frontmatter and display: filename, platform, type, topic, status, created_at, has_images.
3. Group by platform, then by status (drafts first, then posted).

### `edit <file>`

1. Read the specified draft file.
2. Show current content to user.
3. Ask user what changes they want.
4. Apply changes and save.
5. Confirm: "Draft updated."
