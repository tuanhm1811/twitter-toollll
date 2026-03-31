"""SessionStart hook: check config, create dirs, auto-organize files."""

import os
import sys
import shutil
import json

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PLUGIN_ROOT)

from scripts.utils.config import load_config

REQUIRED_DIRS = ["knowledges", "contents", "images"]

KNOWLEDGE_EXTS = {".pdf", ".txt", ".csv", ".json", ".doc", ".docx", ".xls", ".xlsx"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

PLATFORMS = ["twitter", "reddit", "threads", "facebook"]


def check_config():
    config = load_config()
    if config is None:
        print("Social Agent is not configured for this project. Run /setup to initialize.")
        return

    configured = []
    not_configured = []
    for p in PLATFORMS:
        creds = config.get(p)
        if isinstance(creds, dict) and any(v for v in creds.values() if v):
            configured.append(p.capitalize())
        else:
            not_configured.append(p.capitalize())

    parts = []
    if configured:
        parts.append(f"Configured platforms: {', '.join(configured)}")
    if not_configured:
        parts.append(f"Not configured: {', '.join(not_configured)}")
    if parts:
        print(". ".join(parts) + ".")


def ensure_dirs():
    created = []
    for d in REQUIRED_DIRS:
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
            created.append(f"{d}/")
    if created:
        print(f"Created directories: {', '.join(created)}")


def auto_organize():
    moved = []
    for entry in os.listdir("."):
        if not os.path.isfile(entry):
            continue
        _, ext = os.path.splitext(entry)
        ext = ext.lower()
        if ext in KNOWLEDGE_EXTS:
            dest = os.path.join("knowledges", entry)
            shutil.move(entry, dest)
            moved.append(f"  {entry} -> knowledges/")
        elif ext in IMAGE_EXTS:
            dest = os.path.join("images", entry)
            shutil.move(entry, dest)
            moved.append(f"  {entry} -> images/")
    if moved:
        print(f"Auto-organized {len(moved)} file(s):")
        print("\n".join(moved))


if __name__ == "__main__":
    check_config()
    ensure_dirs()
    auto_organize()
