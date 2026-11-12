---
name: opencode-delegate
description: Delegate coding tasks from Claude Code to OpenCode CLI. Use when asked to run OpenCode for implementation, independent review, debugging, tests, or to continue an OpenCode session inside an IDE chat.
argument-hint: "[review|implement] [task]"
---

# OpenCode Delegate

You are the user's coordinator. Delegate a bounded task to the installed OpenCode CLI, and report its *observed* results; never claim OpenCode ran if it did not.

## Before delegating

1. Confirm your chat has a working terminal/command-execution tool, and run `opencode --version` if the binary is not already known to be available. If it is missing, explain setup using the top-level README; do not invent results.
2. Work in the correct repository. Determine its absolute project directory, and preserve the same working tree unless the user explicitly requests a separate worktree.
3. Ask for approval before authorizing code edits, installs, database changes, commits, pushes, destructive operations, or arbitrary shell execution. For review-only requests do not request implementation approval.
4. Use the user's requested provider/model ID exactly (e.g. `provider/model#high`). Do not guess what models or variants are available; if unspecified, let OpenCode use its configured default. Model availability depends on OpenCode's provider connection.
5. For read-only code review, prefer the `claude-review` agent installed with this package. It denies OpenCode `edit` and `shell` actions. Don't treat a plain natural-language promise of read-only behavior as a permission boundary.
6. Don't use the OpenCode `--auto` flag. It would auto-approve permissions not explicitly denied.

## Tool entrypoint

The script is located at `scripts/delegate.py`, relative to this SKILL.md. Use Python 3.9+; it uses only the standard library.

For a read-only audit (preferred default):

```bash
python3 ~/.claude/skills/opencode-delegate/scripts/delegate.py \
  --mode review --project "$PWD" \
  --task 'Review authentication and report concrete findings with paths and lines.'
```

For approved implementation only:

```bash
python3 ~/.claude/skills/opencode-delegate/scripts/delegate.py \
  --mode implement --approved --project "$PWD" \
  --task 'Implement the explicitly approved change, run focused checks, and summarize the diff.'
```

Optional flags: `--model provider/model#variant`, `--agent build` (implement mode only), `--session ses_ID`, `--format json`, `--task-file /path/to/task.txt`, `--timeout 900`, `--dry-run`. For a project-local installation, use `.claude/skills/opencode-delegate/scripts/delegate.py` instead of the home path.

## Required behavior

- Choose `review` when the user requests analysis, architecture advice, bug triage, or independent verification; choose `implement` only when they explicitly permit edits.
- Pass clear acceptance criteria, important project constraints, relevant paths, and the specific question to OpenCode; do not delegate a vague instruction without context.
- Never run competing write-capable agents concurrently in the same working tree. Use separate worktrees for parallel implementations only with user authorization.
- When OpenCode returns, inspect the exit code and its actual tool output. For implementation, inspect changed files (`git status`, `git diff` when available), run appropriate verification, and distinguish pre-existing from introduced changes. Don't commit/push/deploy unless explicitly authorized.
- If OpenCode hangs or fails with a permission/credential/model error, stop and report the error. Do not automatically escalate privileges or enable `--auto`.
- Return a short handoff: what OpenCode attempted, agent and model requested (or default), what changed, tests, remaining concerns, and any OpenCode session ID reported. Avoid exposing credentials and private model reasoning.
- The skill invokes the OpenCode *CLI* from Claude Code's terminal; it does not directly control or read an existing OpenCode GUI chat/extension session. `--session` works only for a session ID available to that CLI account/project.
