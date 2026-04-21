# architecture-first — Cursor IDE

Cursor adaptation of the plugin. Key differences from Claude Code:

| Claude Code | Cursor | Consequence |
|---|---|---|
| `SKILL.md` auto-triggers on description | `.cursor/rules/*.mdc` with `alwaysApply: true` | full parity |
| Parallel sub-agents (architect + cleaner) | none | emulated in the rule text — model runs sequentially |
| Slash commands `/arch-*` | none | replaced with prompt snippets in `.cursor/prompts-architecture-first/` |
| `PreToolUse` hook blocks `Edit` | none | no-code gate is soft — lives only in the rule text |
| `~/.claude/settings.json` (global) | `.cursor/` per project | install into every repo you want it in |

## Install into a project

```bash
cd /path/to/your-project
~/Projects/architecture-first-plugin/cursor/install.sh
```

This creates:
- `.cursor/rules/architecture-first.mdc` — rule active on all source files.
- `.cursor/prompts-architecture-first/arch-*.md` — 9 command snippets.

Commit `.cursor/` so your whole team gets the same guardrail.

## How to use

**Daily editing.** Just ask. The rule is `alwaysApply: true`, so the model produces the 4-section response (Situation → Plan → Structure → Code) and waits for your confirmation before writing code. No hook — only a text-level reminder, so the model *usually* waits but can slip on short requests.

**Commands via snippets.** Open `.cursor/prompts-architecture-first/arch-hotspot.md`, copy its text into the chat, replace `<PATH>` / `<SCOPE>` / `<BATCH-ID>` where applicable. Same behaviour as `/arch-hotspot` in Claude Code.

**Better: Notepads.** Settings → Features → Notepads (enable). Create one Notepad per snippet. In chat, reference as `@arch-hotspot`. This is the closest thing Cursor has to slash commands.

**Strongest: Custom Mode.** Settings → Models → Custom Modes → New. Name it "Architect". System Prompt = the body of `rules/architecture-first.mdc` (without the YAML front-matter). Restrict tools: keep Edit/Search/Terminal, disable Web. Switch the mode on when you want strict architect behaviour; switch off for quick help. This is the most reliable way to enforce the workflow in Cursor.

## Honest limitations

1. **No hard edit gate.** The model usually waits for plan approval but can jump to `apply` under pressure from short requests like "just add this field". Mitigation: use the "Architect" Custom Mode on purpose for non-trivial work.
2. **No parallel sub-agents.** In Claude Code, `architect-reviewer` and `cleaner` run concurrently. In Cursor one model does both sequentially — tier-M responses cost a bit more time and tokens.
3. **No mass-deletion gate.** If you say "clean everything unused" the model may delete a lot at once. Mitigation: ask for `arch-clean` (manifest) first, pick one batch, then run `arch-clean-approve` for that specific batch.

## Update

```bash
cd ~/Projects/architecture-first-plugin && git pull
# then in each project where the plugin is installed:
~/Projects/architecture-first-plugin/cursor/install.sh /path/to/project
```
