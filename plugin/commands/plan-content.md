---
description: Plan a content calendar and schedule posts for an upcoming period
argument-hint: [duration] [--posts-per-day N]
---

Plan social media content for an upcoming period. AI proposes a calendar from the knowledge base, generates drafts and images, and schedules automatic posting.

## Setup

1. Check that `./contents/` and `./images/` directories exist. If not, tell user: "Missing directories. Run `/setup` or `/init` first."
2. Read `./summary.md`. If it doesn't exist, tell user: "No summary.md found. Run `/summarize` first."
3. Read `.social-agent.yaml` to determine which platforms are configured. If no platforms configured, tell user: "No platforms configured. Run `/setup` first."

## Arguments

- `duration`: How far ahead to plan. Examples: `7 days`, `2 weeks`, `30 days`. Default: `7 days`.
- `--posts-per-day N`: Number of posts per day. Default: `1`.

## Phase 1: Calendar Proposal

1. Read `./summary.md` to extract available topics.
2. Select the most compelling and diverse topics from the knowledge base. Spread variety — avoid consecutive similar topics.
3. Create a calendar with 1 slot per post:
   - Assign varied posting times across days (e.g., mornings, afternoons, evenings). If multiple posts/day, times must differ.
   - Default ALL configured platforms for every slot.
   - Default `Image: ai` for every slot (knowledge base content is project-related).
4. Write the calendar to `./contents/calendar-YYYY-MM-DD.md` with this format:

   ```markdown
   ---
   created_at: "YYYY-MM-DD HH:MM"
   period: "YYYY-MM-DD → YYYY-MM-DD"
   posts_per_day: N
   status: draft
   ---

   ## YYYY-MM-DD (Day) — HH:MM
   **Topic:** Topic name
   **Platforms:** twitter, threads, facebook
   **Image:** ai
   ```

5. Display the full calendar in terminal.
6. Ask user: "Review the calendar above. Tell me what to change, or say **approve** to start generating content."
7. **Review loop:** If user requests changes (edit topic, remove/add platform, change time, change image source), update the calendar file and display again. Repeat until user approves.

## Phase 2: Content & Image Generation

Triggered after calendar approval.

1. Parse the approved calendar using:

   ```python
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar_utils.py parse --file <calendar-path>
   ```

   This is for reference — the command orchestrates generation directly.

2. **For each slot in the calendar, sequentially:**
   a. Generate platform-specific drafts using the same logic as `/generate-content`:
      - For each platform in the slot, generate a draft following platform-specific formatting rules and character limits from `/generate-content`.
      - Each draft includes extra frontmatter fields:
        ```yaml
        scheduled_at: "YYYY-MM-DD HH:MM"
        calendar: calendar-YYYY-MM-DD.md
        ```
      - Save to `./contents/` with naming: `YYYY-MM-DD_<topic-slug>_<type>_<platform>.md`
   b. Generate image for this slot's topic:
      - If `Image: ai` → Run `/generate-image` with the draft (uses kie.ai).
      - If `Image: web` → Run `/generate-image` with the draft (uses web search).
      - 1 image per topic, shared across all platforms for that topic.
   c. Update the calendar slot with draft file paths and image file path.

3. After all slots are generated, update calendar status to `generated`.

4. **Build review data** for each slot:
   - Read each draft file's content body.
   - Collect into a structure: `{date, time, topic, image_file, drafts: {platform: content}}`.

5. **Generate HTML review page:**

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_page.py \
     --calendar <calendar-path> \
     --output ./contents/calendar-YYYY-MM-DD-review.html
   ```

   Or build the review data in-command and call the script. The review page shows:
   - Each slot: date, time, topic
   - Banner image (full width)
   - Platform columns side by side with character counts

6. Open the HTML file in the user's browser:

   ```bash
   open ./contents/calendar-YYYY-MM-DD-review.html
   ```

7. Tell user: "Review page opened in browser. Check the content and images. Tell me what to change, or say **approve all** to schedule."

8. **Review loop:** If user requests changes, edit the relevant draft files, regenerate the HTML review page, and reload. Repeat until user approves all.

## Phase 3: Scheduling

Triggered after user approves all content.

1. **For each slot in the calendar:**
   - Collect all draft files for this slot (from the calendar's `Drafts:` list).
   - Use Claude Code `/schedule` to create ONE scheduled trigger for this slot:
     - Trigger time: the slot's datetime (e.g., "2026-04-03 09:00")
     - Trigger action: For each draft file in this slot, run `/post <draft-file>`
   - This means: 1 trigger per slot, each trigger posts to all platforms for that topic.

2. **Update statuses:**
   - Update each draft file: `status: scheduled`
   - Update calendar file: `status: scheduled`

3. **Cleanup:**
   - Delete `./contents/calendar-YYYY-MM-DD-review.html`

4. **Display summary:**

   ```
   Content calendar scheduled!

   Period: 2026-04-03 → 2026-04-09
   Total posts: 21 (7 topics × 3 platforms)
   Triggers: 7

   Upcoming:
     2026-04-03 09:00 — Topic A → twitter, threads, facebook
     2026-04-04 18:30 — Topic B → twitter, threads, facebook
     ...

   Use `/schedule list` to view or cancel scheduled triggers.
   ```
