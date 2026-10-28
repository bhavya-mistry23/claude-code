#!/usr/bin/env python
import sys
import json
import os
import subprocess
from datetime import datetime

LOG_FILE = "backend_changelog.md"
BACKEND_EXTENSIONS = (".py", ".go", ".rs", ".js", ".ts", ".java", ".sql")

GIT_TIMEOUT_SECONDS = 5
MAX_SNIPPET_LINES = 60
MAX_SNIPPET_CHARS = 4000


def _initialize_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("# Backend Session Changelog\n\n")


def _append_log(content):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(content)


def _git(args, cwd):
    """Run a git command and return its stdout, or "" on any failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _git_diff(file_path):
    """Return the `git diff -U1` patch for a tracked file, or "" if unavailable."""
    abs_path = os.path.abspath(file_path)
    cwd = os.path.dirname(abs_path)
    file_name = os.path.basename(abs_path)

    if _git(["rev-parse", "--is-inside-work-tree"], cwd) != "true":
        return ""
    if not _git(["ls-files", "--", file_name], cwd):
        return ""

    # Everything uncommitted vs HEAD (plain working-tree diff if no commits yet).
    command = ["diff", "HEAD"] if _git(["rev-parse", "HEAD"], cwd) else ["diff"]
    return _git([*command, "-U1", "--", file_name], cwd)


def _strip_diff_headers(diff):
    """Drop git's file headers (the file name is in the heading), keeping the hunks."""
    lines = diff.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("@@"):
            return "\n".join(lines[i:])
    return ""


def _prefixed(text, prefix):
    return "\n".join(prefix + line for line in text.splitlines())


def _edit_fallback_diff(tool_input):
    """Build a -/+ patch from the Edit payload when git has nothing to show."""
    old = tool_input.get("old_string", "")
    new = tool_input.get("new_string", "")
    parts = [_prefixed(old, "-"), _prefixed(new, "+")]
    return "\n".join(p for p in parts if p)


def _write_content(file_path, tool_input):
    content = tool_input.get("content")
    if content is None:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    return content


def _truncate(text):
    lines = text.splitlines()
    truncated = len(lines) > MAX_SNIPPET_LINES
    text = "\n".join(lines[:MAX_SNIPPET_LINES])
    if len(text) > MAX_SNIPPET_CHARS:
        text = text[:MAX_SNIPPET_CHARS].rsplit("\n", 1)[0]
        truncated = True
    return text + "\n... (truncated)" if truncated else text


def _code_block(lang, text):
    # Use a fence longer than any backtick run inside the snippet.
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}{lang}\n{text}\n{fence}\n"


def _format_entry(timestamp, tool_name, file_path, tool_input):
    heading = f"### {timestamp} `{tool_name}` on `{os.path.basename(file_path)}`\n"

    if tool_name == "Write":
        lang = os.path.splitext(file_path)[1].lstrip(".")
        snippet = _truncate(_write_content(file_path, tool_input))
    else:
        lang = "diff"
        snippet = _strip_diff_headers(_git_diff(file_path))
        if not snippet:
            snippet = _edit_fallback_diff(tool_input)
        snippet = _truncate(snippet)

    return f"{heading}{_code_block(lang, snippet)}\n"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    event = data.get("hook_event_name")
    if not event:
        return

    _initialize_log()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if event == "SessionStart":
        session_id = data.get("session_id", "unknown")
        cwd = data.get("cwd", "")
        _append_log(
            f"## Session Started: `{timestamp}`\n"
            f"- **Session ID:** `{session_id}`\n"
            f"- **Working Directory:** `{cwd}`\n\n"
        )

    elif event == "PostToolUse":
        tool_name = data.get("tool_name")
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")

        if tool_name in ("Edit", "Write") and file_path.endswith(BACKEND_EXTENSIONS):
            _append_log(_format_entry(timestamp, tool_name, file_path, tool_input))

    elif event == "SessionEnd":
        reason = data.get("reason", "normal")
        _append_log(f"*Session Ended: {timestamp} (Reason: {reason})*\n\n---\n\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # A logging hook must never crash or block the terminal.
        pass
    sys.exit(0)
