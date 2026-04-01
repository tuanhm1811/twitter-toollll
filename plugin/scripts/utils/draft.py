"""Shared draft file parsing and frontmatter management.

Extracted from post_twitter.py to be reused across all platform modules.
"""

import os
import re

import yaml


def parse_draft(file_path):
    """Parse a draft markdown file into frontmatter dict and content parts.

    Content parts are split differently based on platform:
    - Twitter: split by "## Tweet N" headings
    - Threads: split by "## Post N" headings
    - Reddit: body after "## Body" heading returned as single part
    - Facebook: entire body returned as single part

    Returns:
        (frontmatter_dict, list_of_content_strings)
        Returns (None, []) if the file has no valid frontmatter.
    """
    with open(file_path, "r") as f:
        raw = f.read()

    match = re.match(r"^---\n(.*?)\n---\n(.*)", raw, re.DOTALL)
    if not match:
        return None, []

    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()

    if not body:
        return frontmatter, []

    platform = frontmatter.get("platform", "")

    if platform == "twitter":
        parts = re.split(r"^## Tweet \d+\s*\n", body, flags=re.MULTILINE)
        parts = [p.strip() for p in parts if p.strip()]
        if not parts:
            parts = [body]
    elif platform == "threads":
        parts = re.split(r"^## Post \d+\s*\n", body, flags=re.MULTILINE)
        parts = [p.strip() for p in parts if p.strip()]
        if not parts:
            parts = [body]
    elif platform == "reddit":
        body_match = re.split(r"^## Body\s*\n", body, flags=re.MULTILINE)
        if len(body_match) > 1:
            parts = [body_match[1].strip()]
        else:
            parts = [body]
    else:
        # Facebook and any unknown platform: entire body as one part
        parts = [body]

    return frontmatter, parts


def update_frontmatter(file_path, updates):
    """Update specific frontmatter fields in a draft file, preserving the body.

    Args:
        file_path: Path to the draft markdown file.
        updates: Dict of field names and new values to merge into frontmatter.
    """
    with open(file_path, "r") as f:
        raw = f.read()

    match = re.match(r"^---\n(.*?)\n---\n(.*)", raw, re.DOTALL)
    if not match:
        return

    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)

    frontmatter.update(updates)

    new_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip()
    with open(file_path, "w") as f:
        f.write(f"---\n{new_yaml}\n---\n{body}")


def resolve_image_paths(frontmatter, draft_dir):
    """Resolve image paths from frontmatter relative to the project root.

    Args:
        frontmatter: Parsed frontmatter dict.
        draft_dir: Absolute path to the directory containing the draft file.

    Returns:
        List of dicts with 'path' (absolute local path) and 'url' (remote URL, may be empty).
    """
    project_dir = os.path.dirname(draft_dir)  # contents/ -> project root
    resolved = []

    if frontmatter.get("has_images") and frontmatter.get("images"):
        for img in frontmatter["images"]:
            if isinstance(img, dict):
                p = img.get("path", "")
                url = img.get("url", "")
            else:
                p = str(img)
                url = ""
            if p:
                if not os.path.isabs(p):
                    p = os.path.join(project_dir, p)
                resolved.append({"path": p, "url": url})

    return resolved
