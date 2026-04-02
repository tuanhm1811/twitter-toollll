# `/plan-content` — Content Calendar Planning & Scheduling

## Overview

A new slash command that lets users plan social media content for an upcoming period (e.g., 1 week). AI proposes a content calendar from the project's knowledge base, generates all drafts and images after approval, then schedules automatic posting via Claude Code triggers.

## Command Syntax

```
/plan-content [duration] [--posts-per-day N]
```

- `duration`: Human-readable period. Examples: `7 days`, `2 weeks`, `30 days`. Default: `7 days`.
- `--posts-per-day`: Number of posts per day. Default: `1`.

## Complete Flow

```
/plan-content 7 days
       │
       ▼
  ┌─────────────────────────────┐
  │ Phase 1: PLAN               │
  │ 1. Read summary.md          │
  │ 2. Propose calendar         │
  │    (topics, times, platforms)│
  └──────────┬──────────────────┘
             ▼
      Review 1 (calendar outline)
      ↻ user edits → update → show again
             │ approve
             ▼
  ┌─────────────────────────────┐
  │ Phase 2: GENERATE           │
  │ 3. Generate drafts          │
  │    (per topic × platform)   │
  │ 4. Generate images          │
  │    (1 AI image per topic)   │
  │ 5. Update calendar file     │
  │ 6. Create HTML review page  │
  └──────────┬──────────────────┘
             ▼
      Review 2 (content + images in browser)
      ↻ user edits → update → show again
             │ approve all
             ▼
  ┌─────────────────────────────┐
  │ Phase 3: SCHEDULE           │
  │ 7. Create 1 trigger per slot│
  │ 8. Update statuses          │
  │ 9. Cleanup temp files       │
  └─────────────────────────────┘
```

## Phase 1: Calendar Proposal

### Input
- Read `summary.md` to extract available topics from the knowledge base.
- Read `.social-agent.yaml` to determine which platforms are configured.

### AI Behavior
- Select the most compelling and diverse topics from the knowledge base.
- Distribute topics across the requested period (1 topic per slot by default).
- Assign posting times — AI chooses varied times across days for natural distribution. If multiple posts per day, times must differ.
- Default all configured platforms for every slot. User can remove platforms per slot during review.
- Image source defaults to `ai` for all slots (knowledge base content is project-related, not news). User can change to `web` during review.

### Calendar File

Created at `contents/calendar-YYYY-MM-DD.md`:

```markdown
---
created_at: "2026-04-02 10:00"
period: "2026-04-03 → 2026-04-09"
posts_per_day: 1
status: draft
---

## 2026-04-03 (Thu) — 09:00
**Topic:** Artemis II mission update
**Platforms:** twitter, threads, facebook
**Image:** ai

## 2026-04-04 (Fri) — 18:30
**Topic:** AI regulation in EU
**Platforms:** twitter, threads, facebook
**Image:** ai

## 2026-04-05 (Sat) — 12:00
**Topic:** Climate tech breakthroughs
**Platforms:** twitter, threads
**Image:** ai
```

Each slot contains: date + time, topic, list of platforms, image source type.

### Review 1

- Display the full calendar in terminal.
- User says what to change (edit topic, remove a platform, change time, swap image source to web).
- AI updates the calendar file and displays again.
- Loop until user says "approve" or equivalent.

## Phase 2: Content & Image Generation

Triggered after calendar approval.

### Draft Generation
- For each slot, generate platform-specific drafts using the same logic as `/generate-content`.
- Each topic × platform = 1 draft file.
- Example: 7 slots × 3 platforms = 21 draft files.
- File naming follows existing convention: `YYYY-MM-DD_<topic-slug>_<type>_<platform>.md`.

### New Frontmatter Fields

Each generated draft includes:

```yaml
scheduled_at: "2026-04-03 09:00"
calendar: calendar-2026-04-02.md
```

- `scheduled_at`: The exact datetime this draft should be posted.
- `calendar`: Reference back to the source calendar file.

### Image Generation
- 1 image per topic (shared across all platforms for that topic).
- Default AI-generated via kie.ai (`generate_image.py`).
- If user changed a slot to `Image: web` during review 1, use web search + `search_image.py` instead.
- Image naming: `YYYY-MM-DD_<topic-slug>_banner.png` (ai) or `_photo.png` (web).

### Calendar File Update

After generation completes, update the calendar file:
- Status: `draft` → `generated`
- Each slot gets added `Drafts:` and `Image file:` fields:

```markdown
## 2026-04-03 (Thu) — 09:00
**Topic:** Artemis II mission update
**Platforms:** twitter, threads, facebook
**Image:** ai
**Drafts:**
- contents/2026-04-03_artemis-ii-mission-update_tweet_twitter.md
- contents/2026-04-03_artemis-ii-mission-update_post_threads.md
- contents/2026-04-03_artemis-ii-mission-update_post_facebook.md
**Image file:** images/2026-04-03_artemis-ii-mission-update_banner.png
```

### Review 2: HTML Review Page

Generate `contents/calendar-YYYY-MM-DD-review.html` and open in browser.

**Layout per slot:**
- Header: date, time, topic
- Banner image: full-width display
- Platform columns side by side: platform name, character count, full content

```
┌──────────────────────────────────────────────────┐
│ 2026-04-03 (Thu) — 09:00                         │
│ Topic: Artemis II mission update                 │
│                                                  │
│ [============ banner image ============]         │
│                                                  │
│  Twitter          Threads         Facebook       │
│ ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│ │ 240 chars   │  │ 420 chars   │  │ 200 chars   │  │
│ │ Tweet 1:    │  │ Post 1:     │  │ Full post:  │  │
│ │ ...         │  │ ...         │  │ ...         │  │
│ │ Tweet 2:    │  │ Post 2:     │  │             │  │
│ │ ...         │  │ ...         │  │             │  │
│ └────────────┘  └────────────┘  └────────────┘  │
├──────────────────────────────────────────────────┤
│ 2026-04-04 (Fri) — 18:30                         │
│ ...                                              │
└──────────────────────────────────────────────────┘
```

**Technical details:**
- Self-contained HTML with inline CSS (no external dependencies, no server needed).
- Images loaded via relative paths from `../images/`.
- Responsive layout for readability.

**Review loop:**
- User views in browser, returns to terminal to request changes.
- AI edits the relevant draft files, regenerates the HTML review page.
- Loop until user approves all.

## Phase 3: Scheduling

Triggered after user approves all content in review 2.

### Trigger Creation
- Create **1 Claude Code scheduled trigger per calendar slot**.
- Each trigger fires at the slot's `scheduled_at` time.
- The trigger posts all drafts for that slot (all platforms for that topic).
- Example: 7 slots = 7 triggers.

Trigger action: find all draft files with matching `scheduled_at` and `status: scheduled`, then call `/post` for each.

### Status Updates
- Calendar file status: `generated` → `scheduled`
- All draft files: `status: draft` → `status: scheduled`

### Cleanup
- Delete `contents/calendar-YYYY-MM-DD-review.html` (temporary review file).
- Keep `contents/calendar-YYYY-MM-DD.md` (permanent record).
- Keep all draft files and images (needed by triggers to post).

### Final Summary
Display to user:
- Total posts scheduled: N
- Platforms: list
- Period: start date → end date
- Next scheduled post: date + time + topic

## Data Model Changes

### New Draft Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `scheduled_at` | string | Datetime to post, format `"YYYY-MM-DD HH:MM"` |
| `calendar` | string | Filename of source calendar |

### New Draft Status

Existing: `draft`, `posted`
New: `scheduled` (approved and trigger created, waiting to fire)

### Calendar File Statuses

| Status | Meaning |
|--------|---------|
| `draft` | Calendar proposed, pending review 1 |
| `generated` | Content + images created, pending review 2 |
| `scheduled` | All triggers created, waiting to fire |

## Files Created by `/plan-content`

For a 7-day plan with 1 post/day and 3 platforms:

| Type | Count | Pattern | Permanent? |
|------|-------|---------|------------|
| Calendar | 1 | `contents/calendar-YYYY-MM-DD.md` | Yes |
| Drafts | 21 | `contents/YYYY-MM-DD_<slug>_<type>_<platform>.md` | Yes |
| Images | 7 | `images/YYYY-MM-DD_<slug>_banner.png` | Yes |
| Review HTML | 1 | `contents/calendar-YYYY-MM-DD-review.html` | No (deleted after approve) |
| Triggers | 7 | Claude Code scheduled triggers | Auto-removed after firing |

## Scope Boundaries

- `/plan-content` only plans content from the project's knowledge base (`summary.md`).
- It does NOT plan news/current events (cannot predict future news).
- Image source defaults to `ai` (project content). User can override to `web` per slot during review.
- Does not modify existing commands (`/generate-content`, `/post`, `/generate-image`) — reuses their logic internally.
