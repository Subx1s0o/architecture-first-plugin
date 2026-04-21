#!/usr/bin/env bash
# Uninstall the architecture-first plugin.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"
SETTINGS="${CLAUDE_HOME}/settings.json"

echo "==> removing skill"
rm -rf "${CLAUDE_HOME}/skills/architecture-first"

echo "==> removing agents"
rm -f "${CLAUDE_HOME}/agents/arch-architect-reviewer.md" \
      "${CLAUDE_HOME}/agents/arch-hotspot-decomposer.md" \
      "${CLAUDE_HOME}/agents/arch-cleaner.md"

echo "==> removing commands"
rm -f "${CLAUDE_HOME}/commands/arch-"*.md

echo "==> de-registering hook"
if [[ -f "$SETTINGS" ]]; then
  python3 - "$SETTINGS" "$SRC" <<'PY'
import json, sys, pathlib, os
p = pathlib.Path(sys.argv[1])
src_dir = os.path.realpath(sys.argv[2])
data = json.loads(p.read_text() or "{}")
pre = data.get("hooks", {}).get("PreToolUse", [])
def owned(cmd: str) -> bool:
    if not cmd:
        return False
    try:
        return os.path.realpath(cmd).startswith(src_dir)
    except Exception:
        return False
pre[:] = [h for h in pre if not any(owned(x.get("command", "")) for x in h.get("hooks", []))]
data.setdefault("hooks", {})["PreToolUse"] = pre
p.write_text(json.dumps(data, indent=2))
print("[ok] hook removed from settings.json")
PY
fi

echo "==> clearing any live markers"
rm -rf "${TMPDIR:-/tmp}/architecture-first" 2>/dev/null || true

echo "==> done."
