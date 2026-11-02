# Claude Code Features and Concepts

## Core Configuration

**claude.md** — Loaded every time. Keep it concise and global. Use `/init` for claude.md generation via Claude itself.
(Adds persistent context Claude sees every session)

**skills/** — For individual roles.
(Add reusable knowledge and invocable workflows)

**rules/** — For setting boundaries (e.g., migrations)

**commands/** — For server startup and testing commands the agent should run.
(Commands and skills are now similar)

**hooks/**
- Pre tool use
- Post tool use
- Event-based (session start, session end, file changed, permission request)
- Exit codes: 0, 1, 2

## Advanced Features

**/mcps** — Model Context Protocol Servers

**agents/** — Isolated, mutually exclusive tasks that use memory for context optimization across runs.

**agent teams** (BETA) — Interconnected agents

**/loop** — For automatic iteration

**Plugins & Marketplace** — Ship reusable configurations (.claude packages)

## Headless Mode

`-p` for headless mode (UI-less; permissions still required)

```bash
claude -p 'create a dummy.py file' --dangerously-skip-permissions

claude -p "if dummy.py exists" >> claude-tasks.log 2>&1
```

## When to Use Each Feature

| Situation | Solution |
|-----------|----------|
| Claude gets a convention or command wrong twice | Add it to `CLAUDE.md` |
| You keep asking Claude to be shorter/longer or use same format | Set an output style |
| You keep typing the same prompt to start a task | Save it as a user-invocable skill |
| You paste the same playbook or multi-step procedure three times | Capture it as a skill |
| You keep copying data from a browser Claude can’t access | Connect that system as an MCP server |
| Claude reads many files to find where a symbol is used | Install a code intelligence plugin for your language |
| A side task floods chat with output you won’t reference | Route it through a subagent |
| You want something to happen every time without asking | Write a hook |
| A second repository needs the same setup | Package it as a plugin