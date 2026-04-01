---
description: Generate or find images for social media drafts
argument-hint: [draft-file] [--prompt "custom prompt"]
---

Generate banner images (AI) or find real photos (web) for social media post drafts.

## Setup

1. Check that `./images/` and `./contents/` directories exist. If not, tell user: "Missing directories. Run `/setup` or `/init` first."

## Process

### Determine the draft

- If a draft file argument is provided, use that file.
- If no argument, find the most recent `.md` file in `./contents/` with `status: draft`.
- If no drafts found, tell user to run `/generate-content` first.

### Classify content type

Read the draft content and determine whether it needs an AI-generated banner or a real photo from the web.

1. If `./summary.md` exists, read it to understand the user's project/product context.
2. Classify the draft content:
   - **image_source = "ai"** if the content:
     - Is about the user's project/product (matches topics in summary.md)
     - Discusses abstract tech concepts, tutorials, tips, or how-to content
     - Promotes a product, service, or tool
   - **image_source = "web"** if the content:
     - Mentions real-world news events (wars, launches, elections, disasters)
     - References real people in a news context (politicians, CEOs, public figures)
     - Describes specific incidents with dates or locations
     - Covers geopolitical events or current affairs
   - **When in doubt** (content mixes both): prefer "web" for news-related content.
3. Tell the user: "Content classified as [ai/web] — [brief reason]."

### If image_source = "web": Find real photo

1. Use WebSearch to find news articles related to the draft topic. Search for the main subject + "photo" or key event name.
2. Use WebFetch on the most relevant article to extract image URLs from the page.
3. Choose the highest quality, most relevant image URL (prefer editorial photos, avoid ads/logos/thumbnails).
4. Run the download script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/search_image.py \
  --url "<selected image URL>" \
  --output "./images/YYYY-MM-DD_<topic-slug>_photo.png"
```

5. Parse the JSON output.
6. If `success: false` — tell user "Could not download web image, falling back to AI generation." Then follow the "ai" path below.

### If image_source = "ai": Generate AI banner

1. If `--prompt` argument is provided, use that directly.
2. Otherwise, read the draft content and craft an image prompt that:
   - Captures the main theme of the content
   - Is descriptive and specific for AI image generation
   - Requests a style suitable for social media banners (clean, professional, eye-catching)
   - Specifies landscape orientation

### Image Naming Convention

- AI-generated: `YYYY-MM-DD_<topic-slug>_banner.png`
- Web photo: `YYYY-MM-DD_<topic-slug>_photo.png`

Save images to `./images/`, matching the content file's topic slug.

### Generate the AI image (only for image_source = "ai")

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate_image.py \
  --prompt "<crafted prompt>" \
  --output "./images/YYYY-MM-DD_<topic-slug>_banner.png" \
  --size "3:2" \
  --config .social-agent.yaml
```

### Handle result

1. Parse the JSON output from the script (either `search_image.py` or `generate_image.py`).
2. If `success: true`:
   - The JSON response includes `path` (local file) and `url` (remote URL).
   - For web images, the JSON also includes `source: "web"`.
   - Find all draft files in `./contents/` that share the same topic slug (extract from the image filename pattern `YYYY-MM-DD_<topic-slug>_*`). Match draft files named `*_<topic-slug>_*`.
   - For each matching draft file (skip files with `platform: reddit`):
     - Update frontmatter: set `has_images: true`
     - Add entry to `images:` list:
       ```yaml
       - path: "images/YYYY-MM-DD_<topic-slug>_[banner|photo].png"
         url: "<url from JSON response>"
         description: "<the prompt used OR article source for web images>"
         source: "ai" or "web"
       ```
   - Show the generated/downloaded image to the user (use Read tool on the image file).
   - Confirm: "Image [generated/found] at `<path>` and linked to N draft(s): [list filenames]."
3. If `success: false`:
   - Show the error message.
   - Suggest: "Try again with a different prompt using `/generate-image --prompt \"...\"`"
