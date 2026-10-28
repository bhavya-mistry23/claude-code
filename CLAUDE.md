# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a minimal Python project with a simple entry point. The main application logic lives in `app.py`.

## Running the Project

- **Run the app:** `python app.py`
- The application will execute the `main()` function and print output to the console.

## Development Setup

### Session Tracking Hook

The `.claude/settings.json` configures a PostToolUse hook that automatically logs all backend file modifications (Edit/Write operations on .py, .go, .rs, .js, .ts, .java, .sql files) to `backend_changelog.md`. This provides an audit trail of development activity.

The hook is implemented in `.claude/hooks/session_changelog.py` and runs on every file edit/write operation during the session.

## Code Style

- Follow PEP 8 conventions for Python code
- Use descriptive function and variable names
- Keep functions focused and single-purpose

## Notes for Future Work

- This is a skeleton project; expand the application structure under `app.py` as needed
- The session changelog will automatically track changes for audit purposes
- Use the Claude Code settings in `.claude/settings.json` to configure future hooks or customizations
