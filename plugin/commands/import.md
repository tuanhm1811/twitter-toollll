---
description: Import knowledge files or URLs into current project
argument-hint: <file-or-url>
---

Import a knowledge file or web page into the current project's `knowledges/` directory.

## Process

1. Check that `./knowledges/` directory exists. If not, tell user: "No knowledges/ directory found. Run `/init` or `/setup` first."

2. Parse the argument `$ARGUMENTS`:

   **If it's a local file path:**
   - Verify the file exists.
   - Copy it to `./knowledges/`.
   - Confirm: "Imported '<filename>' into ./knowledges/"

   **If it's a URL (starts with http:// or https://):**
   - Use WebFetch to download the page content.
   - Extract the domain and path slug from the URL.
   - Save as markdown in `./knowledges/<domain>-<slug>.md`.
   - Confirm: "Imported '<url>' as '<filename>' into ./knowledges/"

3. If no argument provided, show usage: "Usage: `/import <file-path-or-url>`"
