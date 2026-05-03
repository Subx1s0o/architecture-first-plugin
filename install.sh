#!/usr/bin/env bash
# Install the architecture-first plugin (Claude Code).
# Idempotent: re-running refreshes files and de-duplicates the hook entry.
#
# Prerequisites: Python 3.8+, bash (Git Bash / WSL on Windows), git.
# Supported: macOS, Linux, Windows via WSL or Git Bash.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"
SETTINGS="${CLAUDE_HOME}/settings.json"
HOOK_CMD="${SRC}/hooks/pre-edit-gate.py"

echo "==> architecture-first installer"
echo "    source: ${SRC}"
echo "    target: ${CLAUDE_HOME}"

# --- Dependency check ---
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required (>=3.8) but was not found on PATH."
  echo "       macOS:   install via Homebrew: 'brew install python'"
  echo "       Linux:   install via your package manager (apt/dnf/pacman)"
  echo "       Windows: use WSL or install Python from python.org"
  exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PY_OK=$(python3 -c 'import sys; print(1 if sys.version_info >= (3,8) else 0)')
if [[ "$PY_OK" != "1" ]]; then
  echo "ERROR: python3 $PY_VERSION is too old. Need >= 3.8."
  exit 1
fi
echo "    python: $(command -v python3) (${PY_VERSION})"

# --- Copy artifacts ---
mkdir -p "${CLAUDE_HOME}"/{agents,commands,skills}

rm -rf "${CLAUDE_HOME}/skills/architecture-first"
cp -R "${SRC}/skills/architecture-first" "${CLAUDE_HOME}/skills/architecture-first"

for f in "${SRC}/agents"/*.md; do
  base="$(basename "$f")"
  cp "$f" "${CLAUDE_HOME}/agents/arch-${base}"
done

for f in "${SRC}/commands"/*.md; do
  cp "$f" "${CLAUDE_HOME}/commands/$(basename "$f")"
done

chmod +x "${HOOK_CMD}"

# --- Register hook ---
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

# Dedupe: drop any prior entry pointing at our hook (new or legacy .sh path).
cmd_dir = os.path.dirname(cmd)
legacy_names = {cmd, os.path.join(cmd_dir, "pre-edit-gate.sh")}
pre[:] = [
    h for h in pre
    if not any(x.get("command") in legacy_names for x in h.get("hooks", []))
]
pre.append({
    "matcher": "Edit|Write|NotebookEdit",
    "hooks": [{"type": "command", "command": cmd}],
})
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(data, indent=2))
print(f"[ok] settings updated: {settings_path}")
PY

echo
echo "==> done."
echo
echo "Marker location: ${TMPDIR:-/tmp}/architecture-first/"
echo "   (per-user, ephemeral, auto-pruned after 24h — never in your repo)"
echo
echo "Try it now in any project:"
echo "  /arch-profile-init     # detect stack, create .arch-profile.yaml"
echo "  /arch-hotspot          # scan for hotspots + cleanup debt"
echo "  /arch-clean            # scan for cleanup opportunities (run BEFORE decomposing)"
echo "  /arch-decompose ALL    # plan top-3 hotspots; emits act/defer/no-op verdict"
echo "  /arch-session-close    # honest ledger of what shipped vs ceremony"
