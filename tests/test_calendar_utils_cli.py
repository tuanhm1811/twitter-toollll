import json
import os
import sys
import tempfile

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_cli_parse():
    """calendar_utils CLI parse action outputs JSON with metadata and slots."""
    content = """---
created_at: "2026-04-02 10:00"
period: "2026-04-03 → 2026-04-04"
posts_per_day: 1
status: draft
---

## 2026-04-03 (Thu) — 09:00
**Topic:** Topic A
**Platforms:** twitter, threads
**Image:** ai
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        from scripts.calendar_utils import main
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["parse", "--file", path])

        output = json.loads(buf.getvalue())
        assert output["metadata"]["status"] == "draft"
        assert len(output["slots"]) == 1
        assert output["slots"][0]["topic"] == "Topic A"
    finally:
        os.unlink(path)


def test_cli_update_status():
    """calendar_utils CLI update-status action changes the calendar status."""
    content = """---
created_at: "2026-04-02 10:00"
period: "2026-04-03 → 2026-04-04"
posts_per_day: 1
status: draft
---

## 2026-04-03 (Thu) — 09:00
**Topic:** Topic A
**Platforms:** twitter
**Image:** ai
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        path = f.name

    try:
        from scripts.calendar_utils import main, parse_calendar

        main(["update-status", "--file", path, "--status", "generated"])

        meta, slots = parse_calendar(path)
        assert meta["status"] == "generated"
        assert len(slots) == 1
    finally:
        os.unlink(path)
