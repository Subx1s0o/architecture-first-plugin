#!/usr/bin/env bash
# architecture-first: PreToolUse gate.
# Blocks Edit/Write/NotebookEdit when:
#   (a) no architectural plan has been approved for this session, OR
#   (b) the tool call would delete a lot of code without a cleanup-batch
#       approval for this session.
#
# Markers live in ${TMPDIR:-/tmp}/architecture-first/<project-hash>-<session>.*
# NEVER in the user's project tree.

set -euo pipefail

input="$(cat)"
tool="$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null || echo '')"

case "$tool" in
  Edit|Write|NotebookEdit) ;;
  *) exit 0 ;;
esac

session_id="$(printf '%s' "$input" | jq -r '.session_id // "default"' 2>/dev/null || echo 'default')"
proj="${CLAUDE_PROJECT_DIR:-$PWD}"
proj_hash="$(printf '%s' "$proj" | md5 -q 2>/dev/null || printf '%s' "$proj" | md5sum | cut -c1-32)"

marker_dir="${TMPDIR:-/tmp}/architecture-first"
mkdir -p "$marker_dir" 2>/dev/null || true
plan_marker="${marker_dir}/${proj_hash}-${session_id}.approved"
clean_marker="${marker_dir}/${proj_hash}-${session_id}.clean-approved"

# Best-effort cleanup: drop markers older than 24h on every invocation.
# Cheap enough and keeps /tmp tidy.
find "$marker_dir" -type f -mmin +1440 -delete 2>/dev/null || true

path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo '')"

# --- Plan gate ---
if [[ ! -f "$plan_marker" ]]; then
  # Allow trivial docs/config outside src/.
  if [[ "$path" =~ \.(md|txt|json|ya?ml|toml)$ ]] && [[ "$path" != *"/src/"* ]]; then
    :
  else
    cat >&2 <<EOF
[architecture-first] BLOCKED: no approved plan for this session.

Before editing code, produce the 4-step architect response (Situation → Plan
→ Structure → Code). Then run /arch-approve to unlock edits.

For genuinely trivial edits (typos, formatting): /arch-approve --trivial "<reason>".
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
