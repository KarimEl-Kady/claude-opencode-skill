#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == "--project" ]]; then
  PROJECT="${2:?Usage: bash install.sh --project /absolute/path/to/project}"
  [[ -d "$PROJECT" ]] || { echo "Project does not exist: $PROJECT" >&2; exit 1; }
  SKILLS_DIR="$PROJECT/.claude/skills"
  AGENTS_DIR="$PROJECT/.opencode/agents"
elif [[ $# -eq 0 ]]; then
  SKILLS_DIR="$HOME/.claude/skills"
  AGENTS_DIR="$HOME/.config/opencode/agents"
else
  echo "Usage: bash install.sh [--project /path/to/project]" >&2
  exit 1
fi
mkdir -p "$SKILLS_DIR/opencode-delegate/scripts" "$AGENTS_DIR"
cp "$ROOT/.claude/skills/opencode-delegate/SKILL.md" "$SKILLS_DIR/opencode-delegate/SKILL.md"
cp "$ROOT/.claude/skills/opencode-delegate/scripts/delegate.py" "$SKILLS_DIR/opencode-delegate/scripts/delegate.py"
cp "$ROOT/.opencode/agents/claude-review.md" "$AGENTS_DIR/claude-review.md"
printf 'Installed Claude skill: %s\nInstalled read-only OpenCode agent: %s\n' "$SKILLS_DIR/opencode-delegate" "$AGENTS_DIR/claude-review.md"
echo 'Restart Claude Code, then invoke /opencode-delegate.'
