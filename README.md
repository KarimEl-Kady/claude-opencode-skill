# Claude Code → OpenCode Skill

Delegate code review or approved implementation to the OpenCode CLI from inside Claude Code Chat (including Claude Code extension in Antigravity IDE), without manually switching chat windows.

## Requirements
- Claude Code with access to a terminal/command-execution tool (skills alone cannot grant terminal access).
- OpenCode CLI installed, authenticated with the desired provider/model, and visible in the same terminal `PATH`.
- Python 3.9+ (standard library only).
- The `claude-review` agent in this archive uses **OpenCode V2 permissions**. Review the config if your CLI is an older version.

## Install OpenCode
See https://opencode.ai/docs for the current official install method, then launch `opencode` once and connect your provider. Verify:

```bash
opencode --version
opencode run --agent plan 'Explain this project'
```

Do not assume Claude Code and OpenCode share auth; OpenCode's model catalog and credentials are scoped to its own provider connections.

## Install this Skill globally

Unzip and from the extracted folder run:

```bash
bash install.sh
```

This copies the Skill to `~/.claude/skills/opencode-delegate/` and the read-only reviewer agent to `~/.config/opencode/agents/claude-review.md`.

Alternatively install for only one project:

```bash
bash install.sh --project /absolute/path/to/your-project
```

That installs under `<project>/.claude/skills/` and `<project>/.opencode/agents/`.

Restart Claude Code / reload the extension. Invoke `/opencode-delegate`, or ask Claude to use it naturally.

## Example prompts in Claude Chat

- `Use /opencode-delegate to ask OpenCode for an independent READ-ONLY review of my authentication code, then summarize the findings.`
- `Use /opencode-delegate with model provider/model#high to review the current changes and compare with your own review.`
- `I approve editing only src/auth/*. Ask OpenCode to fix the token refresh bug, run focused tests, and show me the diff. Use /opencode-delegate.`
- `Continue OpenCode session ses_123 for the previously approved task.`

## Terminal examples

```bash
python3 ~/.claude/skills/opencode-delegate/scripts/delegate.py \
  --mode review --project "$PWD" \
  --task 'Audit authentication without editing any files.'

python3 ~/.claude/skills/opencode-delegate/scripts/delegate.py \
  --mode implement --approved --project "$PWD" \
  --model 'provider/model#high' \
  --task 'Make only the explicitly approved changes and run tests.'
```

`--approved` is a deliberate guard; it is NOT a replacement for OpenCode permission settings. The script never adds `--auto`. Review mode requires a custom agent that denies edit/shell. A terminal-based noninteractive run cannot answer interactive permission prompts; adjust the OpenCode permission rules carefully if a task needs approval.

## Limitations
- This invokes a fresh `opencode run` command or an existing CLI session **by ID**, not a remote control hook into the visible OpenCode GUI/IDE chat.
- Working tree is shared when targeting the same path; running multiple write agents in the same directory risks conflicting edits.
- OpenCode must actually run for results to exist. No provider account or model availability is guaranteed by installing this Skill.
- OpenCode output may contain untrusted project content; Claude should interpret and verify it, not blindly obey it.
- OpenCode V2 agent permissions are defined in `.opencode/agents/claude-review.md`; inspect if behavior changes in future releases.

Sources: https://opencode.ai/docs/cli/commands , https://opencode.ai/docs/agents/ , https://code.claude.com/docs/en/skills .
