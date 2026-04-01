---
description: Generate images for social media drafts using kie.ai
argument-hint: [draft-file] [--prompt "custom prompt"]
---

Generate banner images for social media post drafts using kie.ai image generation API.

## Setup

1. Check that `./images/` and `./contents/` directories exist. If not, tell user: "Missing directories. Run `/setup` or `/init` first."

## Process

### Determine the draft

- If a draft file argument is provided, use that file.
- If no argument, find the most recent `.md` file in `./contents/` with `status: draft`.
- If no drafts found, tell user to run `/generate-content` first.

### Craft the image prompt

- If `--prompt` argument is provided, use that directly.
- Otherwise, read the draft content and craft an image prompt that:
  - Captures the main theme of the tweet/thread
  - Is descriptive and specific for AI image generation
  - Requests a style suitable for social media banners (clean, professional, eye-catching)
  - Specifies landscape orientation

### Image Naming Convention

```
YYYY-MM-DD_<topic-slug>_banner.png
```

Save images to `./images/`, matching the content file's topic slug.

### Generate the image

Run the Python script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate_image.py \
  --prompt "<crafted prompt>" \
  --output "./images/YYYY-MM-DD_<topic-slug>_banner.png" \
  --size "3:2" \
  --config .social-agent.yaml
```

### Handle result

1. Parse the JSON output from the script.
2. If `success: true`:
   - The JSON response includes both `path` (local file) and `url` (remote kie.ai URL).
   - Find all draft files in `./contents/` that share the same topic slug (extract from the image filename pattern `YYYY-MM-DD_<topic-slug>_banner.png`). Match draft files named `*_<topic-slug>_*`.
   - For each matching draft file (skip files with `platform: reddit`):
     - Update frontmatter: set `has_images: true`
     - Add entry to `images:` list:
       ```yaml
       - path: "images/YYYY-MM-DD_<topic-slug>_banner.png"
         url: "<url from JSON response>"
         description: "<the prompt used>"
       ```
   - Show the generated image to the user (use Read tool on the image file).
   - Confirm: "Image generated at `<path>` and linked to N draft(s): [list filenames]."
3. If `success: false`:
   - Show the error message.
   - Suggest: "Try again with a different prompt using `/generate-image --prompt \"...\"`"
