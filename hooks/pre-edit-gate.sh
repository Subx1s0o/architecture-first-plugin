#!/usr/bin/env bash
# architecture-first: PreToolUse gate.
# Blocks Edit/Write/NotebookEdit when:
#   (a) no architectural plan has been approved for this session, OR
#   (b) the tool call would delete a lot of code without a cleanup batch approval.
# Unlock via slash commands: /arch-approve and /arch-clean-approve.

set -euo pipefail

input="$(cat)"
tool="$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null || echo '')"

case "$tool" in
  Edit|Write|NotebookEdit) ;;
  *) exit 0 ;;
esac

session_id="$(printf '%s' "$input" | jq -r '.session_id // "default"' 2>/dev/null || echo 'default')"
proj="${CLAUDE_PROJECT_DIR:-$PWD}"
mkdir -p "${proj}/.claude" 2>/dev/null || true
plan_marker="${proj}/.claude/.arch-approved-${session_id}"
clean_marker="${proj}/.claude/.clean-approved-${session_id}"

path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo '')"

# --- Plan gate ---
if [[ ! -f "$plan_marker" ]]; then
  # Trivial docs/config outside src/ are allowed.
  if [[ "$path" =~ \.(md|txt|json|ya?ml|toml)$ ]] && [[ "$path" != *"/src/"* ]]; then
    :
  # Plugin's own files are always allowed (so /arch-approve can write markers).
  elif [[ "$path" == *"/.claude/.arch-"* ]] || [[ "$path" == *"/.claude/.clean-"* ]]; then
    :
  else
    cat >&2 <<EOF
[architecture-first] BLOCKED: no approved plan for this session.

Before editing code, produce the 4-step architect response:
  1. Situation / architecture    2. Plan
  3. File-structure proposal     4. Code

Then run /arch-approve to unlock edits for this session.
For genuinely trivial edits (typos, formatting), use:
  /arch-approve --trivial "<one-line reason>"
EOF
    exit 2
  fi
fi

# --- Mass-deletion gate ---
new_content="$(printf '%s' "$input" | jq -r '.tool_input.new_string // .tool_input.content // empty' 2>/dev/null || echo '')"
old_content="$(printf '%s' "$input" | jq -r '.tool_input.old_string // empty' 2>/dev/null || echo '')"
removed=0
if [[ -n "$old_content" && -n "$new_content" ]]; then
  old_n=$(printf '%s\n' "$old_content" | wc -l | tr -d ' ')
  new_n=$(printf '%s\n' "$new_content" | wc -l | tr -d ' ')
  (( old_n > new_n )) && removed=$(( old_n - new_n )) || removed=0
fi
if [[ "$tool" == "Write" && -z "$new_content" && -n "$path" && -f "$path" ]]; then
  removed=$(wc -l < "$path" 2>/dev/null | tr -d ' ' || echo 0)
fi

if (( removed >= 200 )) && [[ ! -f "$clean_marker" ]]; then
  cat >&2 <<EOF
[architecture-first] BLOCKED: mass deletion (${removed} lines) without an approved cleanup batch.

Produce a cleanup manifest via /arch-clean, then authorize the batch with:
  /arch-clean-approve <batch-id>
EOF
  exit 2
fi

exit 0
