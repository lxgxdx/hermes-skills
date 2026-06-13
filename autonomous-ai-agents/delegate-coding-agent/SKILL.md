---
name: delegate-coding-agent
description: Class-level guide to delegating coding tasks to external autonomous CLI agents from Hermes — covers Claude Code, OpenAI Codex, OpenCode, and the Kanban-Codex integration pattern. Compares auth models, command surfaces, sandbox flags, background/PTY modes, worktree isolation, and PR review workflows. Load when choosing or orchestrating an external coding agent, integrating one into a Kanban worker, or comparing their command-line ergonomics.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [coding-agent, claude-code, codex, opencode, autonomous-coder, delegation, pr-review, worktree, pty, claude, openai]
    related_skills: [claude-code, codex, opencode, hermes-agent, hermes-kanban]
---

# Delegate Coding Agent — Class-Level Guide

Three terminal CLIs cover the "delegate a coding task to an external autonomous agent" use case from Hermes. All three read files, write code, run shell commands, and manage git workflows autonomously. They differ in vendor, command shape, auth model, and feature surface.

| Agent | Vendor | Command | Auth | Best for |
|-------|--------|---------|------|----------|
| **Claude Code** | Anthropic | `claude -p "..."` | `ANTHROPIC_API_KEY` or OAuth (`claude auth login`) | Mature print mode, `--json-schema` structured output, MCP servers, hooks, slash commands, worktrees |
| **Codex** | OpenAI | `codex exec "..."` | `OPENAI_API_KEY` or Codex OAuth | OpenAI-tuned, `--full-auto` / `--yolo` flags, multi-PR batch review, gateway-bubblewrap fallback |
| **OpenCode** | Provider-agnostic | `opencode run "..."` | Per-provider env vars (e.g. `OPENROUTER_API_KEY`) | Switch providers mid-session, JSON events, TUI Tab between build/plan agents, BYO model |

> **All three share the same shape: `terminal(command=<agent> <args>, workdir=<repo>, pty=true|false, background=true|false)`.** The differences are in the flag set, the auth model, and the edge-case handling. Use this umbrella to pick the right one and load the per-CLI recipe.

## Sections

1. [Claude Code](references/claude-code.md) — the `claude-code` skill. Print mode (`-p`), interactive tmux orchestration, dialog handling (workspace trust, permissions), full CLI flag reference, CLAUDE.md / settings hierarchy, custom subagents, hooks, MCP integration, cost tips, pitfalls.
2. [Codex](references/codex.md) — the `codex` skill. `codex exec` for one-shots, `--full-auto` / `--yolo` / `--sandbox danger-full-access` flags, the gateway bubblewrap caveat, multi-PR batch reviews with worktrees, the "must use `pty=true`" hard rule.
3. [OpenCode](references/opencode.md) — the `opencode` skill. `opencode run` for one-shots, interactive TUI in background, model/provider switching, TUI keybindings (Ctrl+P palette, Tab agents, Ctrl+X L/M/N/E), session resume with `-c` / `-s`, JSON output events, common pitfalls (NEVER use `/exit`).

## Decision: Which Agent When?

| Need | Best choice | Why |
|------|-------------|-----|
| `--json-schema` for structured extraction | **Claude Code** | Built-in `--json-schema` + `--output-format json` |
| Multi-PR batch review with worktrees | **Codex** | `--yolo` + `git worktree` + `gh pr` is the cleanest pattern |
| Switch model/provider mid-session | **OpenCode** | `--model provider/model` flag, session resumption with new model |
| TUI for long multi-turn interactive work | **Claude Code** (tmux) or **OpenCode** (background TUI) | Both work; Claude Code has more mature slash commands |
| OpenAI-tuned code | **Codex** | Native |
| Provider-agnostic / BYO model | **OpenCode** | First-class provider switching |
| Kanban worker lane | **Codex** (the `kanban-codex-lane` pattern) | See §4 below |
| Run in a non-interactive shell without PTY | **Claude Code (`-p`)** or **OpenCode (`run`)** | Both have a non-interactive mode |
| Run from a Hermes gateway (Telegram, etc.) | **Codex with `--sandbox danger-full-access`** | Bubblewrap fails in containerized contexts |

## Shared Patterns Across All Three

These patterns apply to all three CLIs and are worth knowing before diving into a per-CLI recipe:

### 1. Worktree isolation for parallel work
```python
# Create a worktree
git worktree add -b fix/issue-78 /tmp/issue-78 main

# Launch the agent in the worktree
terminal(command="<agent> exec '...'", workdir="/tmp/issue-78", background=True, pty=True)

# Cleanup
git worktree remove /tmp/issue-78
```

### 2. PR review from a temp clone
```python
REVIEW=$(mktemp -d)
git clone https://github.com/user/repo.git $REVIEW
cd $REVIEW && gh pr checkout 42
# Run agent in $REVIEW
```

### 3. Monitoring background runs
```python
# Start
result = terminal(command="<agent> ...", background=True, pty=True, notify_on_complete=True)
session_id = result["session_id"]

# Poll / read logs
process(action="poll", session_id=session_id)
process(action="log", session_id=session_id, limit=200)
```

### 4. The `pty=true` rule
- **Codex** — REQUIRES `pty=true` (interactive TUI). `exec` mode works without pty in some contexts but the loader refuses outside a git repo.
- **Claude Code** — `print` mode (`-p`) does NOT need pty. Interactive mode DOES.
- **OpenCode** — `run` mode does NOT need pty. Interactive TUI DOES.

### 5. Killing stuck lanes
```python
process(action="kill", session_id=session_id)
```

## The Kanban-Codex Lane Pattern

If you're a Hermes Kanban worker and you want to spawn Codex as an isolated implementation lane, use the `hermes-kanban` umbrella's §3 (the `kanban-codex-lane` recipe). The key points:

- Codex runs in an isolated git worktree, NOT the user's main checkout
- The `kanban_complete` metadata includes a `codex_lane` block with worktree path, branch, result, accepted commits, tests_run
- Hermes (not Codex) owns the Kanban lifecycle and the final test run
- PMB safety constraints are added to the Codex prompt verbatim when relevant

See `hermes-kanban` for the full pattern.

## When to Load This Umbrella

- Choosing which agent to install/use
- Setting up auth for one of them
- Debugging a launch failure (pty missing, auth not loaded, worktree dirty)
- Integrating one into a multi-agent workflow (Kanban worker, scheduled task, gateway-driven)
- Comparing their command surfaces for a specific task (PR review, batch fix, refactor)

## When to Load a Per-CLI Skill Instead

If you've already decided on Claude Code / Codex / OpenCode and need the full CLI flag reference, custom-agent examples, or specific pitfalls, load the per-CLI skill:

- Load `claude-code` for the full Claude Code reference (print mode, tmux orchestration, hooks, MCP, settings)
- Load `codex` for the Codex reference (`exec` vs `goal`, sandbox flags, gateway caveat, batch PR review)
- Load `opencode` for the OpenCode reference (TUI, model switching, session resume, format flags)

This umbrella is the "pick one" entry point; the per-CLI skills are the "use it well" deep-dives.

## Related Skills

- `hermes-agent` — parent umbrella for all Hermes internals
- `hermes-kanban` — Kanban multi-agent system; §3 has the Codex lane pattern
- `claude-code`, `codex`, `opencode` — the three per-CLI skills (still active as standalone skills for direct `--skills` loading)
