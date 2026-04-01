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

### Platform-Specific Body Formats & Formatting Rules

> **CRITICAL: Always count characters BEFORE finalizing content.** Each platform has strict limits. Content that exceeds the limit WILL fail to post. Aim for 80% of max length for optimal engagement.

**Twitter/X** (type: tweet or thread):
- **Hard limit: 280 characters per tweet** (including spaces, emojis, hashtags — everything)
- **Target: 200-240 characters** for optimal engagement (leave room for hashtags)
- Single tweet: plain text body
- Thread: split into `## Tweet 1`, `## Tweet 2`, etc. (max 25 tweets per thread)
- 3-7 tweets per thread recommended
- URLs count as 23 characters regardless of actual length
- **Formatting rules:**
  - Separate each idea/point with a blank line (line break)
  - Hook strong on the first line — make it attention-grabbing
  - 1-2 sentences per block, never a wall of text
  - Use 1 emoji at the start of the first line (optional for subsequent lines)
  - End with 1-2 relevant hashtags on a separate line (hashtags count toward 280 limit)
- **Validation:** Count the total characters of the body text. If it exceeds 280, shorten it. Do NOT publish content over 280 characters.
- Example (237 chars):
    ```
    🏛️ Historic: Trump becomes first sitting president to attend Supreme Court oral arguments.

    The case — can his order end birthright citizenship?

    Every lower court has blocked it. Ruling expected by summer.
    ```

**Reddit** (type: submission):
- **Hard limit: 300 characters for title, 40,000 characters for body**
- **Target: 60-100 chars for title** (concise, searchable)
- `title` field in frontmatter
- `subreddit` field in frontmatter (without r/ prefix)
- Body under `## Body` heading, full markdown supported
- **Formatting rules:**
  - Use markdown headers, bullet points, bold for structure
  - Short paragraphs (2-3 sentences each), separated by blank lines
  - No emojis (Reddit culture prefers plain text)
  - TL;DR at the end for long posts

**Threads** (type: post or thread):
- **Hard limit: 500 characters per post** (including spaces, emojis, hashtags, bullet points — everything)
- **Target: 350-450 characters** for readability with formatting
- Single post: plain text body
- Thread: split into `## Post 1`, `## Post 2`, etc.
- 3-7 posts per thread recommended
- Links are NOT clickable in Threads posts
- **Formatting rules:**
  - Separate each idea with a blank line
  - Conversational tone, more casual than Twitter
  - Use bullet points (•) for lists — but remember each bullet line counts toward 500 limit
  - 1 emoji at opening line, sparingly elsewhere
  - 0-3 hashtags at the end on a separate line (count toward 500 limit)
- **Validation:** Count the total characters of the body text. If it exceeds 500, shorten it. Do NOT publish content over 500 characters.
- Example (388 chars):
    ```
    Something unprecedented at the Supreme Court today. 🏛️

    Trump showed up in person to attend oral arguments — first sitting president to ever do this.

    The case:
    • Can his order end birthright citizenship?
    • Children born in the US to undocumented parents — citizens or not?

    Ruling expected by summer.

    #SCOTUS
    ```

**Facebook** (type: post):
- **Hard limit: 63,206 characters** (effectively unlimited)
- **Target: 100-250 characters** for highest engagement, or 500-1000 for storytelling posts
- **First 3 lines are critical** — Facebook truncates with "See more" after ~480 pixels (~3 lines)
- Entire body is one post, plain text
- `visibility` field: "public" (default)
- **Formatting rules:**
  - Short paragraphs (2-3 sentences), separated by blank lines
  - Strong hook in the first paragraph — must be compelling enough to click "See more"
  - Storytelling style — more detail and context than Twitter/Threads
  - Optional emoji at start of paragraphs
  - End with a question or CTA to encourage engagement (e.g., "What do you think? 👇")
- Example:
    ```
    History is being made right now. 🚀

    NASA's Artemis II has launched — the first crewed mission to the Moon since 1972. Four astronauts are on a 10-day journey around the lunar far side.

    Victor Glover becomes the first person of color to leave Earth orbit. Christina Koch becomes the first woman on a lunar trajectory.

    After months of delays, the Artemis era has officially begun.

    What do you think about humanity's return to the Moon? 👇
    ```

## Actions

### Generate new content (`--platform <name> [topic]`)

1. `--platform` is required. If not provided, tell user: "Please specify a platform: `/generate-content --platform twitter|reddit|threads|facebook [topic]`"
2. **Ask immediately:** "Would you like to generate a banner image for this content? (default: yes for scheduled tasks)" — If the user declines, skip image generation. If they agree or don't respond (scheduled task), proceed with image generation after step 7.
3. Read `./summary.md`. If it doesn't exist, tell user to run `/summarize` first.
4. If a topic argument was given, focus content on that topic from the summary.
5. If no topic, pick the most compelling angle from "Suggested Content Angles".
6. Generate content following the platform-specific format rules above.
7. **Validate character count** before saving. If over the platform limit, shorten the content.
8. Save to `./contents/` using the file naming convention.
9. Confirm: "Draft created at `<path>` ([N] characters)."
10. **If image generation was agreed to (or this is a scheduled task):** Run `/generate-image` for this draft. The image will be shared across all drafts with the same topic slug.

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
