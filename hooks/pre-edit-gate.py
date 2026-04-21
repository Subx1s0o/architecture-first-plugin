#!/usr/bin/env python3
"""
architecture-first PreToolUse gate (smart).

Classifies every Edit/Write/NotebookEdit as one of:
  - trivial:     allowed silently (docs, tests, build artifacts, tiny changes
                 in modest-sized files, small new files)
  - significant: blocked, requires /arch-approve (new modules, large refactors,
                 changes to probable hotspots, big line-count deltas)

Users never see a block prompt for routine edits. The gate only interrupts
when the change has enough architectural weight to merit a plan.

Markers live under the OS temp dir, never in the user's project:
  macOS:   $TMPDIR/architecture-first/
  Linux:   /tmp/architecture-first/
  Windows: %TEMP%\architecture-first\

Old markers (>24h) prune on every invocation.
Dependencies: Python 3.8+ only.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

# Thresholds — deliberately permissive so routine edits flow through.
MAX_TRIVIAL_CHANGE_LINES = 30       # diff affecting <= 30 lines is trivial
MAX_TRIVIAL_FILE_LOC = 400          # in a file <= 400 LoC
MAX_TRIVIAL_NEW_FILE_LOC = 50       # new files <= 50 LoC are trivial
HOTSPOT_FILE_LOC = 500              # files >= 500 LoC are hotspots → block
MASS_DELETION_THRESHOLD = 200       # deleting 200+ lines → block even if approved

MARKER_TTL_SECONDS = 24 * 60 * 60

IGNORE_SEGMENTS = (
    "/dist/", "/build/", "/.next/", "/.nuxt/",
    "/__pycache__/", "/.venv/", "/venv/",
    "/node_modules/", "/.git/", "/coverage/",
    "/target/",
)

TEST_SEGMENTS = ("/tests/", "/test/", "/__tests__/", "/spec/")
TEST_SUFFIXES = (".spec.ts", ".spec.js", ".spec.tsx", ".spec.jsx",
                 ".test.ts", ".test.js", ".test.tsx", ".test.jsx",
                 ".spec.py", "_test.go", "_test.rs", "_spec.rb")

TRIVIAL_EXTS = (".md", ".txt", ".json", ".yaml", ".yml", ".toml",
                ".env", ".gitignore", ".editorconfig")

# Path markers that almost always indicate architectural concern.
ARCHITECTURAL_SEGMENTS = ("/migrations/", "/migration/", "/schema/")


def temp_root() -> Path:
    for var in ("TMPDIR", "TEMP", "TMP"):
        v = os.environ.get(var)
        if v:
            return Path(v)
    return Path("/tmp")


def prune_old_markers(marker_dir: Path) -> None:
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
    if not s:
        return 0
    return s.count("\n") + (0 if s.endswith("\n") else 1)


def file_line_count(path: str) -> int:
    try:
        if path and os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
    except OSError:
        pass
    return 0


def classify(tool: str, tool_input: dict, path: str) -> str:
    """Return 'trivial' or 'significant'."""
    norm = (path or "").replace("\\", "/").lower()

    # Build artifacts, vendored code, etc.
    if any(seg in norm for seg in IGNORE_SEGMENTS):
        return "trivial"

    # Docs / config files anywhere — user owns these, not architectural.
    ext = os.path.splitext(norm)[1]
    if ext in TRIVIAL_EXTS:
        return "trivial"

    # Test files are edited freely; architecturally meaningful tests are rare.
    if any(seg in norm for seg in TEST_SEGMENTS):
        return "trivial"
    if any(norm.endswith(suf) for suf in TEST_SUFFIXES):
        return "trivial"

    # Migrations / schema changes — always architectural.
    if any(seg in norm for seg in ARCHITECTURAL_SEGMENTS):
        return "significant"

    old_s = tool_input.get("old_string") or ""
    new_s = tool_input.get("new_string") or tool_input.get("content") or ""

    file_loc = file_line_count(path)

    # Write on a non-existent file = creating something new.
    if tool == "Write" and file_loc == 0:
        new_lines = count_lines(new_s)
        if new_lines <= MAX_TRIVIAL_NEW_FILE_LOC:
            return "trivial"
        return "significant"  # new large file — probably a new module

    # Existing file in a probable-hotspot range → architectural decision.
    if file_loc >= HOTSPOT_FILE_LOC:
        return "significant"

    # Diff size
    change_lines = max(count_lines(old_s), count_lines(new_s))
    if change_lines > MAX_TRIVIAL_CHANGE_LINES:
        return "significant"

    # Small change in a normal-sized file → let it flow.
    if file_loc <= MAX_TRIVIAL_FILE_LOC:
        return "trivial"

    # File somewhere between 400–500 LoC with >10-line change — borderline.
    # Err on the side of blocking so the architect sees it.
    if change_lines > 10:
        return "significant"

    return "trivial"


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, OSError):
        return 0  # defer on malformed input

    tool = data.get("tool_name", "")
    if tool not in ("Edit", "Write", "NotebookEdit"):
        return 0

    tool_input = data.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "") or ""

    session = data.get("session_id", "default")
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    proj_hash = hashlib.md5(proj.encode("utf-8")).hexdigest()

    marker_dir = temp_root() / "architecture-first"
    try:
        marker_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return 0
    prune_old_markers(marker_dir)

    plan_marker = marker_dir / f"{proj_hash}-{session}.approved"
    clean_marker = marker_dir / f"{proj_hash}-{session}.clean-approved"

    # Mass-deletion gate runs regardless of plan approval.
    removed = 0
    new_s = tool_input.get("new_string") or tool_input.get("content") or ""
    old_s = tool_input.get("old_string") or ""
    if old_s and new_s:
        removed = max(0, count_lines(old_s) - count_lines(new_s))
    elif tool == "Write" and not new_s and path and os.path.isfile(path):
        removed = file_line_count(path)
    if removed >= MASS_DELETION_THRESHOLD and not clean_marker.exists():
        print(
            f"[architecture-first] BLOCKED: mass deletion ({removed} lines) "
            "without an approved cleanup batch.\n"
            "\n"
            "Run /arch-clean to produce a manifest, then\n"
            "  /arch-clean-approve <batch-id>",
            file=sys.stderr,
        )
        return 2

    # If the user already approved this session, trust them.
    if plan_marker.exists():
        return 0

    # Smart classification — only interrupt on significant changes.
    verdict = classify(tool, tool_input, path)
    if verdict == "trivial":
        return 0

    print(
        "[architecture-first] This change looks architecturally significant.\n"
        "\n"
        f"  file:    {path or '<new file>'}\n"
        f"  size:    {file_line_count(path)} LoC\n"
        f"  diff:    ~{max(count_lines(old_s), count_lines(new_s))} lines\n"
        "\n"
        "Produce the 4-step response (Situation -> Plan -> Structure -> Code),\n"
        "then /arch-approve to proceed.\n"
        'For a one-off exception: /arch-approve --trivial "<reason>"',
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
