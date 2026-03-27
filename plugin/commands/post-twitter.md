---
description: Post Twitter drafts — publish tweets and threads
argument-hint: [draft-file|list]
---

Publish draft content to Twitter using the Twitter API.

## Setup

1. Read config from `.twitter-agent.yaml` in the current directory to get `auto_post`.
2. Check that `./contents/` directory exists. If not, tell user: "No contents/ directory found. Run `/setup` or `/init` first."

## Actions

### Post a draft (default or with file argument)

1. **Select draft**:
   - If a file argument is given, use that file.
   - If no argument, find the most recent `.md` file in `./contents/` with `status: draft`.
   - If no drafts found, tell user to run `/generate-content` first.

2. **Read and display draft**: Show the full content (text + any linked images) to the user.

3. **Confirm** (unless `auto_post: true` in config):
   - Ask: "Ready to post this to Twitter? (yes/no)"
   - If no, stop and tell user they can edit with `/generate-content edit <file>`.

4. **Post**: The script handles reading the draft, posting, and updating frontmatter in one step.

   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/post_twitter.py \
     --file "<path to draft .md file>" \
     --config .twitter-agent.yaml
   ```

5. **Handle result**:
   - Parse JSON output.
   - If `success: true` and `frontmatter_updated: true`:
     - The script already updated the draft frontmatter (status, posted_at, tweet_ids).
     - Confirm: "Posted! Tweet URL: https://twitter.com/i/status/<tweet_id>"
   - If `success: false`:
     - Check if error is a network/proxy/sandbox restriction (403 Forbidden, tunnel, connection refused, proxy error).
     - If **network/sandbox error**: follow the "Sandbox Fallback" section below.
     - Otherwise show error message and suggest fixes (rate limit — wait, auth error — re-run `/setup`).

## Sandbox Fallback

When running inside the Claude desktop app, outbound network requests are blocked by the sandbox. When a network/proxy error is detected:

1. **Generate a ready-to-run shell script** at `./post_draft.sh`:

   ```bash
   #!/bin/bash
   cd "<user's project directory>"
   python "<absolute path to plugin>/scripts/post_twitter.py" \
     --file "<path to draft .md file>" \
     --config .twitter-agent.yaml
   ```

   Make it executable: `chmod +x ./post_draft.sh`

2. **Tell the user**:
   > The Claude desktop app blocks outbound network requests. I've generated `post_draft.sh` with the posting command.
   >
   > Run this in your terminal:
   >
   > ```bash
   > ./post_draft.sh
   > ```
   >
   > The script will post and update the draft file automatically. Paste the JSON output back here to confirm.

3. **When user pastes JSON output back**:
   - Parse the JSON result.
   - If `success: true`: the draft frontmatter is already updated by the script. Confirm with tweet URL.
   - If `success: false`: show the error and suggest fixes.
   - Clean up: remove `./post_draft.sh`.

### `list`

1. List all `.md` files in `./contents/` with `status: draft`.
2. Show: filename, type, topic, created_at, has_images.
3. If no drafts, tell user to run `/generate-content`.
