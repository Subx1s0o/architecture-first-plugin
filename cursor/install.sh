#!/usr/bin/env bash
# Installs architecture-first for Cursor IDE into the TARGET project.
# Usage: ./cursor/install.sh <path-to-project>  (default: current dir)
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$PWD}"
TARGET="$(cd "$TARGET" && pwd)"
echo "==> Cursor install"
echo "    source: $SRC"
echo "    target: $TARGET"
mkdir -p "$TARGET/.cursor/rules" "$TARGET/.cursor/prompts-architecture-first"
cp "$SRC/rules/architecture-first.mdc" "$TARGET/.cursor/rules/architecture-first.mdc"
cp "$SRC/prompts/"*.md "$TARGET/.cursor/prompts-architecture-first/"
echo "==> done."
echo
echo "In Cursor:"
echo "  - The rule is auto-applied on all source files (alwaysApply: true)."
echo "  - Prompt snippets live at .cursor/prompts-architecture-first/arch-*.md"
echo "  - To trigger any command, open chat and paste the content of the"
echo "    matching snippet (replace <PLACEHOLDERS>). Or add them as Notepads:"
echo "    Cursor Settings → Features → Notepads → paste each file."
