#!/usr/bin/env python
import sys
import json
import os
import subprocess
from datetime import datetime

LOG_FILE = "backend_changelog.md"
BACKEND_EXTENSIONS = (".py", ".go", ".rs", ".js", ".ts", ".java", ".sql")

def _initialize_log():
    try:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("# Backend Session Changelog\n\n")
                f.write("| Timestamp | Action | File | AI Summary |\n")
                f.write("|---|---|---|---|\n")
    except Exception:
        pass

def _append_log(content):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass

def _get_git_diff(file_path):
    """Extracts the git diff for the modified file."""
    try:
        repo_dir = subprocess.run(
            ["git", "-C", os.path.dirname(file_path) or ".", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=1
        ).stdout.strip()
        
        if repo_dir:
            rel_path = os.path.relpath(file_path, repo_dir)
            result = subprocess.run(
                ["git", "-C", repo_dir, "diff", rel_path],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
    except Exception:
        pass
    return ""

def _get_ai_summary(diff_text, file_name):
    """Passes the diff to the authenticated Claude CLI using safe standard input isolation."""
    if not diff_text:
        return f"Modified {file_name}"

    try:
        prompt = (
            f"Summarize this code change for file '{file_name}' in a single, crisp, "
            f"action-oriented one-liner (under 12 words, e.g., 'Added foreign key constraint to User model'). "
            f"Return ONLY the summary string with no quotes, markdown, or punctuation at the end:\n\n{diff_text[:2000]}"
        )

        # We use stdin=subprocess.DEVNULL to prevent hook pipe blockages
        result = subprocess.run(
            ["claude", "-p", prompt],
            input=None,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0 and result.stdout.strip():
            # Grab the last clean output line from Claude's response
            lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
            if lines:
                return lines[-1]
    except Exception:
        pass

    return f"Updated {file_name}"

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
        _append_log(
            f"\n## Session: `{session_id}` (`{timestamp}`)\n"
            f"| Timestamp | Action | File | AI Summary |\n"
            f"|---|---|---|---|\n"
        )

    elif event == "PostToolUse":
        tool_name = data.get("tool_name")
        tool_input = data.get("tool_input", {})

        file_path = ""
        if isinstance(tool_input, dict):
            file_path = tool_input.get("file_path", "")

        if tool_name in ("Edit", "Write") and file_path and file_path.endswith(BACKEND_EXTENSIONS):
            file_name = os.path.basename(file_path)

            diff_text = _get_git_diff(file_path)
            if not diff_text and tool_name == "Write":
                diff_text = tool_input.get("content", "")

            summary = _get_ai_summary(diff_text, file_name)

            row = f"| {timestamp} | `{tool_name}` | `{file_name}` | {summary} |\n"
            _append_log(row)

    elif event == "SessionEnd":
        reason = data.get("reason", "normal")
        _append_log(f"\n*Session Ended: {timestamp} ({reason})*\n\n---\n\n")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)