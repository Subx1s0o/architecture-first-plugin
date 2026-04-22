#!/usr/bin/env python3
"""
architecture-first PreToolUse gate (non-intrusive by default).

Default mode: does NOT block routine edits. Only catches catastrophic ops:
  - mass deletion (>= 200 lines removed in a single call)

Strict mode (opt-in via .arch-profile.yaml `strict-gate: true`): also
requires /arch-approve for architecturally significant changes (new
modules, hotspot files, big diffs, migrations).

Markers live under the OS temp dir, NEVER in the user's project tree.
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

MAX_TRIVIAL_CHANGE_LINES = 30
MAX_TRIVIAL_FILE_LOC = 400
MAX_TRIVIAL_NEW_FILE_LOC = 50
HOTSPOT_FILE_LOC = 500
MASS_DELETION_THRESHOLD = 200

MARKER_TTL_SECONDS = 24 * 60 * 60

IGNORE_SEGMENTS = (
    "/dist/", "/build/", "/.next/", "/.nuxt/",
    "/__pycache__/", "/.venv/", "/venv/",
    "/node_modules/", "/.git/", "/coverage/", "/target/",
)
TEST_SEGMENTS = ("/tests/", "/test/", "/__tests__/", "/spec/")
TEST_SUFFIXES = (".spec.ts", ".spec.js", ".spec.tsx", ".spec.jsx",
                 ".test.ts", ".test.js", ".test.tsx", ".test.jsx",
                 ".spec.py", "_test.go", "_test.rs", "_spec.rb")
TRIVIAL_EXTS = (".md", ".txt", ".json", ".yaml", ".yml", ".toml",
                ".env", ".gitignore", ".editorconfig")
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


def is_strict_mode(proj: str) -> bool:
    """Read .arch-profile.yaml for `strict-gate: true` (regex parser — no PyYAML)."""
    try:
        p = Path(proj) / ".arch-profile.yaml"
        if p.is_file():
            content = p.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"^strict-gate:\s*(true|yes|1)\s*$", content,
                          re.MULTILINE | re.IGNORECASE)
            return m is not None
    except OSError:
        pass
    # Also honor env override for one-off sessions.
    return os.environ.get("ARCH_STRICT", "").lower() in ("1", "true", "yes")


def classify(tool: str, tool_input: dict, path: str) -> str:
    norm = (path or "").replace("\\", "/").lower()
    if any(seg in norm for seg in IGNORE_SEGMENTS):
        return "trivial"
    ext = os.path.splitext(norm)[1]
    if ext in TRIVIAL_EXTS:
        return "trivial"
    if any(seg in norm for seg in TEST_SEGMENTS):
        return "trivial"
    if any(norm.endswith(suf) for suf in TEST_SUFFIXES):
        return "trivial"
    if any(seg in norm for seg in ARCHITECTURAL_SEGMENTS):
        return "significant"

    old_s = tool_input.get("old_string") or ""
    new_s = tool_input.get("new_string") or tool_input.get("content") or ""
    file_loc = file_line_count(path)

    if tool == "Write" and file_loc == 0:
        return "trivial" if count_lines(new_s) <= MAX_TRIVIAL_NEW_FILE_LOC else "significant"
    if file_loc >= HOTSPOT_FILE_LOC:
        return "significant"
    change_lines = max(count_lines(old_s), count_lines(new_s))
    if change_lines > MAX_TRIVIAL_CHANGE_LINES:
        return "significant"
    if file_loc <= MAX_TRIVIAL_FILE_LOC:
        return "trivial"
    if change_lines > 10:
        return "significant"
    return "trivial"


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw else {}
    except (json.JSONDecodeError, OSError):
        return 0

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

    # --- Mass-deletion gate — always active (real safety net) ---
    removed = 0
    new_s = tool_input.get("new_string") or tool_input.get("content") or ""
    old_s = tool_input.get("old_string") or ""
    if old_s and new_s:
        removed = max(0, count_lines(old_s) - count_lines(new_s))
    elif tool == "Write" and not new_s and path and os.path.isfile(path):
        removed = file_line_count(path)
    if removed >= MASS_DELETION_THRESHOLD and not clean_marker.exists():
        print(
            f"[architecture-first] BLOCKED: mass deletion ({removed} lines).\n"
            "\n"
            "Large deletions should go through a cleanup manifest:\n"
            "  /arch-clean                    # produce a manifest\n"
            "  /arch-clean-approve <batch-id> # execute a batch",
            file=sys.stderr,
        )
        return 2

    # --- Plan gate — only in strict mode (opt-in) ---
    if not is_strict_mode(proj):
        return 0

    if plan_marker.exists():
        return 0

    verdict = classify(tool, tool_input, path)
    if verdict == "trivial":
        return 0

    print(
        "[architecture-first strict] This change looks architecturally significant.\n"
        "\n"
        f"  file:    {path or '<new file>'}\n"
        f"  size:    {file_line_count(path)} LoC\n"
        f"  diff:    ~{max(count_lines(old_s), count_lines(new_s))} lines\n"
        "\n"
        "Produce the 4-step response, then /arch-approve to proceed.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
