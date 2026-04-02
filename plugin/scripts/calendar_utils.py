"""Calendar file parsing and updating for /plan-content.

Calendar files live in contents/calendar-YYYY-MM-DD.md with YAML frontmatter
and ## date-time heading slots.
"""

import os
import re
import sys

import yaml

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def parse_calendar(file_path):
    """Parse a calendar markdown file into metadata and slot list.

    Returns:
        (metadata_dict, list_of_slot_dicts)
        Each slot dict has: date, day, time, topic, platforms, image,
        and optionally: drafts, image_file.
    """
    with open(file_path, "r") as f:
        raw = f.read()

    fm_match = re.match(r"^---\n(.*?)\n---\n(.*)", raw, re.DOTALL)
    if not fm_match:
        return {}, []

    metadata = yaml.safe_load(fm_match.group(1)) or {}
    body = fm_match.group(2).strip()

    slots = []
    # Split by ## headings: "## 2026-04-03 (Thu) — 09:00"
    slot_pattern = re.compile(
        r"^## (\d{4}-\d{2}-\d{2}) \((\w+)\) — (\d{2}:\d{2})\s*$",
        re.MULTILINE,
    )
    matches = list(slot_pattern.finditer(body))

    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        block = body[start:end].strip()

        slot = {
            "date": m.group(1),
            "day": m.group(2),
            "time": m.group(3),
            "topic": "",
            "platforms": [],
            "image": "ai",
        }

        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("**Topic:**"):
                slot["topic"] = line.replace("**Topic:**", "").strip()
            elif line.startswith("**Platforms:**"):
                raw_platforms = line.replace("**Platforms:**", "").strip()
                slot["platforms"] = [p.strip() for p in raw_platforms.split(",")]
            elif line.startswith("**Image:**"):
                slot["image"] = line.replace("**Image:**", "").strip()
            elif line.startswith("**Image file:**"):
                slot["image_file"] = line.replace("**Image file:**", "").strip()
            elif line.startswith("- contents/"):
                if "drafts" not in slot:
                    slot["drafts"] = []
                slot["drafts"].append(line.lstrip("- ").strip())

        slots.append(slot)

    return metadata, slots


def write_calendar(file_path, metadata, slots):
    """Write a calendar file from metadata and slot list."""
    yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False).strip()
    lines = [f"---\n{yaml_str}\n---\n"]

    for slot in slots:
        lines.append(f"## {slot['date']} ({slot['day']}) — {slot['time']}")
        lines.append(f"**Topic:** {slot['topic']}")
        lines.append(f"**Platforms:** {', '.join(slot['platforms'])}")
        lines.append(f"**Image:** {slot['image']}")

        if "drafts" in slot:
            lines.append("**Drafts:**")
            for d in slot["drafts"]:
                lines.append(f"- {d}")

        if "image_file" in slot:
            lines.append(f"**Image file:** {slot['image_file']}")

        lines.append("")

    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with open(file_path, "w") as f:
        f.write("\n".join(lines))


def update_calendar_status(file_path, new_status):
    """Update the status field in a calendar file's frontmatter."""
    metadata, slots = parse_calendar(file_path)
    metadata["status"] = new_status
    write_calendar(file_path, metadata, slots)


def main(argv=None):
    """CLI entry point for calendar operations."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Calendar file utilities")
    sub = parser.add_subparsers(dest="action", required=True)

    parse_cmd = sub.add_parser("parse", help="Parse calendar file to JSON")
    parse_cmd.add_argument("--file", required=True, help="Calendar file path")

    update_cmd = sub.add_parser("update-status", help="Update calendar status")
    update_cmd.add_argument("--file", required=True, help="Calendar file path")
    update_cmd.add_argument("--status", required=True, help="New status")

    args = parser.parse_args(argv)

    if args.action == "parse":
        metadata, slots = parse_calendar(args.file)
        print(json.dumps({"metadata": metadata, "slots": slots}))
    elif args.action == "update-status":
        update_calendar_status(args.file, args.status)
        print(json.dumps({"success": True, "status": args.status}))


if __name__ == "__main__":
    main()
