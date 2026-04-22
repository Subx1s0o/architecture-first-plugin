#!/usr/bin/env python3
"""
architecture-first: optional pre-commit LoC gate.

Install (one-time per repo):
    ln -sf $HOME/.claude/plugins/architecture-first/hooks/arch-precommit-check.py .husky/arch-check
    # then in .husky/pre-commit, add:  ./.husky/arch-check

Or wire it into whatever pre-commit system you use.

Reads `.arch-profile.yaml` thresholds if present, otherwise uses stack defaults.
Checks every staged source file's LoC. Warns on warn threshold, blocks on xl
threshold. Never blocks via LoC alone if .arch-profile.yaml has `precommit: warn-only`.

Zero LLM cost. Pure stdlib.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_WARN = 400
DEFAULT_XL = 600
SOURCE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs", ".scala", ".swift"}


def staged_files() -> list[Path]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
        check=False, capture_output=True, text=True,
    )
    return [Path(p) for p in out.stdout.splitlines() if p]


def read_profile() -> dict:
    p = Path(".arch-profile.yaml")
    if not p.exists():
        return {}
    # Hand-rolled tiny YAML extractor — avoid PyYAML dep
    text = p.read_text(encoding="utf-8", errors="ignore")
    warn = DEFAULT_WARN
    xl = DEFAULT_XL
    warn_only = False
    m = re.search(r"file-loc:\s*\{[^}]*\bwarn:\s*(\d+)", text)
    if m: warn = int(m.group(1))
    m = re.search(r"file-loc:\s*\{[^}]*\bxl:\s*(\d+)", text)
    if m: xl = int(m.group(1))
    if re.search(r"^\s*precommit:\s*warn-only\b", text, re.MULTILINE):
        warn_only = True
    return {"warn": warn, "xl": xl, "warn_only": warn_only}


def line_count(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def main() -> int:
    cfg = read_profile()
    warn = cfg.get("warn", DEFAULT_WARN)
    xl = cfg.get("xl", DEFAULT_XL)
    warn_only = cfg.get("warn_only", False)

    warns: list[tuple[Path, int]] = []
    blocks: list[tuple[Path, int]] = []

    for f in staged_files():
        if f.suffix not in SOURCE_EXTS:
            continue
        if not f.exists():
            continue
        loc = line_count(f)
        if loc >= xl:
            blocks.append((f, loc))
        elif loc >= warn:
            warns.append((f, loc))

    if warns:
        print("[architecture-first] files approaching hotspot territory:", file=sys.stderr)
        for f, loc in warns:
            print(f"  ⚠ {f} — {loc} LoC (warn at {warn})", file=sys.stderr)
    if blocks:
        print("[architecture-first] files past XL threshold:", file=sys.stderr)
        for f, loc in blocks:
            print(f"  ✗ {f} — {loc} LoC (xl at {xl})", file=sys.stderr)
        print("", file=sys.stderr)
        print("Run /arch-refactor <file> or /arch-decompose <file> when you have time.", file=sys.stderr)

    if blocks and not warn_only:
        print("\nThis commit is blocked. To proceed anyway:", file=sys.stderr)
        print('  - set `precommit: warn-only` in .arch-profile.yaml, or', file=sys.stderr)
        print("  - git commit --no-verify (not recommended)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
