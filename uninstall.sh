#!/usr/bin/env bash
# Uninstall the architecture-first plugin.
set -euo pipefail

CLAUDE_HOME="${HOME}/.claude"
SETTINGS="${CLAUDE_HOME}/settings.json"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_CMD="${SRC}/hooks/pre-edit-gate.sh"

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
  python3 - "$SETTINGS" "$HOOK_CMD" <<'PY'
import json, sys, pathlib
p = pathlib.Path(sys.argv[1]); cmd = sys.argv[2]
data = json.loads(p.read_text() or "{}")
pre = data.get("hooks", {}).get("PreToolUse", [])
pre[:] = [h for h in pre if not any(x.get("command") == cmd for x in h.get("hooks", []))]
if pre or "hooks" in data:
    data.setdefault("hooks", {})["PreToolUse"] = pre
p.write_text(json.dumps(data, indent=2))
print("[ok] hook removed from settings.json")
PY
fi

echo "==> done."
