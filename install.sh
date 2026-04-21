#!/usr/bin/env bash
# Install the architecture-first plugin.
#
# Installs skill/agents/commands into conventional ~/.claude/ locations and
# registers the pre-edit hook in ~/.claude/settings.json.
#
# Re-runs are idempotent: it overwrites the plugin's files and de-duplicates
# the hook entry in settings.json.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"
SETTINGS="${CLAUDE_HOME}/settings.json"

echo "==> architecture-first installer"
echo "    source: ${SRC}"
echo "    target: ${CLAUDE_HOME}"

mkdir -p "${CLAUDE_HOME}"/{agents,commands,skills}

# Skill bundle.
rm -rf "${CLAUDE_HOME}/skills/architecture-first"
cp -R "${SRC}/skills/architecture-first" "${CLAUDE_HOME}/skills/architecture-first"

# Agents — prefix file names so they don't clash with other plugins' agents.
for f in "${SRC}/agents"/*.md; do
  base="$(basename "$f")"
  cp "$f" "${CLAUDE_HOME}/agents/arch-${base}"
done

# Commands — prefix is already `arch-*` in file names.
for f in "${SRC}/commands"/*.md; do
  cp "$f" "${CLAUDE_HOME}/commands/$(basename "$f")"
done

# Hook script — keep canonical copy inside the bundle and reference it
# from settings.json by absolute path. User can also keep the repo where they
# want; re-running installer just updates the path.
chmod +x "${SRC}/hooks/pre-edit-gate.sh"
HOOK_CMD="${SRC}/hooks/pre-edit-gate.sh"

echo "==> registering PreToolUse hook → ${HOOK_CMD}"

python3 - "$SETTINGS" "$HOOK_CMD" <<'PY'
import json, os, sys, pathlib
settings_path = pathlib.Path(sys.argv[1])
cmd = sys.argv[2]
data = {}
if settings_path.exists():
    data = json.loads(settings_path.read_text() or "{}")
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Edit|Write|NotebookEdit",
    "hooks": [{"type": "command", "command": cmd}],
}
# Dedupe by command path.
pre[:] = [
    h for h in pre
    if not any(x.get("command") == cmd for x in h.get("hooks", []))
]
pre.append(entry)
settings_path.write_text(json.dumps(data, indent=2))
print(f"[ok] settings updated: {settings_path}")
PY

echo
echo "==> done."
echo
echo "Try it now:"
echo "  /arch-profile-init     # auto-detect stack, create .arch-profile.yaml"
echo "  /arch-hotspot          # scan repo for architectural hotspots"
echo "  /arch-clean            # scan repo for cleanup opportunities"
echo
echo "During normal coding, the pre-edit hook will force the 4-step architect"
echo "response. Run /arch-approve once the plan is agreed to unlock edits."
