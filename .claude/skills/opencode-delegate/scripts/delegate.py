#!/usr/bin/env python3
"""Safe-ish CLI adapter for delegating a task from Claude Code to OpenCode.

This script helps prevent accidental review->write escalation; OpenCode's real
permission policy remains the authority. No shell interpolation or --auto.
"""
from __future__ import annotations

import argparse
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path


def build_command(args: argparse.Namespace) -> list[str]:
    command = ["opencode", "run"]
    if args.mode == "review":
        if args.agent and args.agent != "claude-review":
            raise ValueError("Review mode requires the read-only claude-review agent")
        command += ["--agent", "claude-review"]
    else:
        if not args.approved:
            raise ValueError("Implementation requires --approved after explicit user permission")
        command += ["--agent", args.agent or "build"]
    if args.model:
        if "/" not in args.model or args.model.startswith("/") or args.model.endswith("/"):
            raise ValueError("Model must be a provider/model ID, optionally ending in #variant")
        command += ["--model", args.model]
    if args.session:
        command += ["--session", args.session]
    if args.format == "json":
        command += ["--format", "json"]
    if args.task_file:
        task = Path(args.task_file).expanduser().resolve().read_text(encoding="utf-8")
    else:
        task = args.task
    if not task or not task.strip():
        raise ValueError("Task cannot be empty")
    command.append(task)
    return command


def stream_command(command: list[str], cwd: Path, timeout: int) -> int:
    # Use argv, not a shell, to prevent injection from prompts and model names.
    proc = subprocess.Popen(
        command, cwd=str(cwd), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1,
    )
    events: queue.Queue[str | None] = queue.Queue()

    def read_stdout() -> None:
        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                events.put(line)
        finally:
            events.put(None)

    reader = threading.Thread(target=read_stdout, daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            proc.kill()
            proc.wait()
            print(f"[opencode-delegate] timed out after {timeout}s", file=sys.stderr)
            return 124
        try:
            line = events.get(timeout=min(remaining, 0.25))
        except queue.Empty:
            if proc.poll() is not None and not reader.is_alive():
                break
            continue
        if line is None:
            break
        print(line, end="", flush=True)
    try:
        return proc.wait(timeout=max(1, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        print("[opencode-delegate] timed out", file=sys.stderr)
        return 124


def main() -> int:
    parser = argparse.ArgumentParser(description="Call OpenCode from Claude Code's terminal")
    parser.add_argument("--project", default=".", help="Existing project directory")
    parser.add_argument("--mode", choices=("review", "implement"), default="review")
    parser.add_argument("--approved", action="store_true", help="Explicit approval for edits (implement only)")
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument("--task", help="Task instruction")
    task.add_argument("--task-file", help="UTF-8 file containing a task instruction")
    parser.add_argument("--model", help="Exact provider/model[#variant] from OpenCode")
    parser.add_argument("--agent", help="Implement: selected agent; review: claude-review only")
    parser.add_argument("--session", help="Continue a specific OpenCode session ID")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--timeout", type=int, default=900, help="Maximum seconds (default: 900)")
    parser.add_argument("--dry-run", action="store_true", help="Print invocation summary, not full task")
    args = parser.parse_args()
    try:
        project = Path(args.project).expanduser().resolve(strict=True)
        if not project.is_dir():
            raise ValueError("--project must refer to a directory")
        if args.timeout < 1 or args.timeout > 7200:
            raise ValueError("--timeout must be between 1 and 7200 seconds")
        if args.approved and args.mode != "implement":
            raise ValueError("--approved is valid only for implement mode")
        command = build_command(args)
        if args.dry_run:
            # Don't echo a possibly sensitive task or credentials.
            safe = ["<TASK>" if item == command[-1] and i == len(command)-1 else item
                    for i, item in enumerate(command)]
            print(f"cwd: {project}\ncommand: {safe!r}\nmode: {args.mode}")
            return 0
        if not shutil.which("opencode"):
            raise ValueError("OpenCode CLI not found in PATH. Install it and run opencode --version")
        print(f"[opencode-delegate] mode={args.mode}, project={project}", file=sys.stderr)
        code = stream_command(command, project, args.timeout)
        if code:
            print(f"[opencode-delegate] OpenCode exit code: {code}", file=sys.stderr)
        return code
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"[opencode-delegate] error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
