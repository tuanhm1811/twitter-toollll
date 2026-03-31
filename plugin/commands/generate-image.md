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
python ${CLAUDE_PLUGIN_ROOT}/scripts/generate_image.py \
  --prompt "<crafted prompt>" \
  --output "./images/YYYY-MM-DD_<topic-slug>_banner.png" \
  --size "3:2" \
  --config .social-agent.yaml
```

### Handle result

1. Parse the JSON output from the script.
2. If `success: true`:
   - Update the draft file's frontmatter:
     - Set `has_images: true`
     - Add entry to `images:` list with `path` (relative, e.g. `../images/2026-03-27_ai-trends_banner.png`) and `description` (the prompt used)
   - Show the generated image to the user (use Read tool on the image file).
   - Confirm: "Image generated at `<path>` and linked to draft."
3. If `success: false`:
   - Show the error message.
   - Suggest: "Try again with a different prompt using `/generate-image --prompt \"...\"`"
