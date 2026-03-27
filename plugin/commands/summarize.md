---
description: Summarize knowledge files in current project
argument-hint: [update]
---

Generate a structured summary from all knowledge files in the current project.

## Setup

1. Check that `./knowledges/` directory exists. If not, tell user: "No knowledges/ directory found. Run `/setup` or `/init` first."

## Modes

### Full summarization (default, no arguments)

1. List all files in `./knowledges/`.
2. If no files found, tell user: "No knowledge files found. Import files with `/import <file>`."
3. Read each file. For large collections (more than 10 files), process in batches of 5 to avoid context overflow.
4. Generate `./summary.md` with this structure:

```markdown
# Knowledge Summary

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

5. Confirm: "Summary generated at ./summary.md with N sources processed."

### Update mode (`/summarize update`)

1. Read existing `./summary.md`.
2. Check the "Source Index" section to identify already-processed files.
3. List files in `./knowledges/` and identify new or modified files (process any file not in Source Index).
4. Read only the new/changed files.
5. Append new topics, facts, and sources to the existing summary sections.
6. Update the "Last updated" date.
7. Confirm: "Summary updated with N new sources."
