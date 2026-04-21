#!/usr/bin/env python3
"""
architecture-first PreToolUse gate.

Blocks Edit/Write/NotebookEdit when:
  (a) no architectural plan has been approved for this session, OR
  (b) the tool call would delete a lot of code without a cleanup-batch
      approval for this session.

Markers live under the OS temp directory, NEVER in the user's project tree:
  - macOS:   $TMPDIR/architecture-first/           (e.g. /var/folders/.../T/)
  - Linux:   /tmp/architecture-first/              (or tmpfs)
  - Windows: %TEMP%\architecture-first\            (e.g. %USERPROFILE%\AppData\Local\Temp)

Old markers (> 24h) are pruned on every invocation.

Dependencies: Python 3.8+ only. No jq, no md5 binary, no find.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

MASS_DELETION_THRESHOLD = 200  # lines
MARKER_TTL_SECONDS = 24 * 60 * 60  # 24h


def temp_root() -> Path:
    """Cross-OS per-user temp dir."""
    for var in ("TMPDIR", "TEMP", "TMP"):
        v = os.environ.get(var)
        if v:
            return Path(v)
    return Path("/tmp")


def prune_old_markers(marker_dir: Path) -> None:
    """Best-effort cleanup of stale markers. Silent on any error."""
    now = time.time()
    try:
        for f in marker_dir.iterdir():
            try:
                if f.is_file() and (now - f.stat().st_mtime) > MARKER_TTL_SECONDS:
                    f.unlink()
            except OSError:
                pass
    except OSError:
        pass


def count_lines(s: str) -> int:
    return s.count("\n") + (1 if s and not s.endswith("\n") else 0)


def removed_line_count(tool: str, tool_input: dict, path: str) -> int:
    old_s = tool_input.get("old_string") or ""
    new_s = tool_input.get("new_string") or tool_input.get("content") or ""
    if old_s and new_s:
        diff = count_lines(old_s) - count_lines(new_s)
        return max(0, diff)
    if tool == "Write" and not new_s and path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except OSError:
            return 0
    return 0


def is_trivial_doc(path: str) -> bool:
    """Trivial docs/config outside src/ bypass the plan gate."""
    if not path:
        return False
    p = path.replace("\\", "/").lower()
    if "/src/" in p:
        return False
    return p.endswith((".md", ".txt", ".json", ".yaml", ".yml", ".toml"))


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, OSError):
        # Unrecognized input shape — defer, do not block. The hook is
        # defense-in-depth, not a primary correctness gate.
        return 0

    tool = data.get("tool_name", "")
    if tool not in ("Edit", "Write", "NotebookEdit"):
        return 0

    session = data.get("session_id", "default")
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    proj_hash = hashlib.md5(proj.encode("utf-8")).hexdigest()

    marker_dir = temp_root() / "architecture-first"
    try:
        marker_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return 0  # cannot create temp dir — defer

    prune_old_markers(marker_dir)

    plan_marker = marker_dir / f"{proj_hash}-{session}.approved"
    clean_marker = marker_dir / f"{proj_hash}-{session}.clean-approved"

    tool_input = data.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "") or ""

    if not plan_marker.exists() and not is_trivial_doc(path):
        print(
            "[architecture-first] BLOCKED: no approved plan for this session.\n"
            "\n"
            "Before editing code, produce the 4-step architect response\n"
            "(Situation -> Plan -> Structure -> Code). Then run /arch-approve\n"
            "to unlock edits.\n"
            "\n"
            "For genuinely trivial edits (typos, formatting):\n"
            '  /arch-approve --trivial "<reason>"',
            file=sys.stderr,
        )
        return 2

    removed = removed_line_count(tool, tool_input, path)
    if removed >= MASS_DELETION_THRESHOLD and not clean_marker.exists():
        print(
            f"[architecture-first] BLOCKED: mass deletion ({removed} lines) "
            "without an approved cleanup batch.\n"
            "\n"
            "Produce a cleanup manifest via /arch-clean, then authorize the\n"
            "batch with:\n"
            "  /arch-clean-approve <batch-id>",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
