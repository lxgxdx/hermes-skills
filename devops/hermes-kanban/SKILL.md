---
name: hermes-kanban
description: Class-level guide to the Hermes Kanban multi-agent board system — covers the worker/orchestrator roles, the shared lifecycle, integration with external coding CLIs (Codex, Claude Code, OpenCode), handoff metadata schemas, retry diagnostics, and the auto-injected KANBAN_GUIDANCE system prompt. Load this skill when working with the Kanban dispatcher, designing task graphs, debugging task failures, or coordinating multiple Hermes profiles.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, worker, codex-lane, delegation, hermes]
    related_skills: [hermes-agent, claude-code, codex, opencode]
---

# Hermes Kanban — Class-Level Guide

The Hermes Kanban system is a multi-agent task board that lives in a SQLite DB (`~/.hermes/kanban.db`) and is dispatched by the `hermes_kanban` plugin. A dispatcher claims ready tasks and spawns workers — each worker is a Hermes run in its own process, isolated config, isolated workspace, isolated toolset. The board is the durable handoff layer; the workers are the actors.

This umbrella covers everything you'd want to know about working with the Kanban system: the shared worker lifecycle, the orchestrator's decomposition playbook, handoff metadata conventions, the Codex-lane integration pattern, and the pitfalls that catch every new user.

> The basic 6-step worker lifecycle (`orient → work → heartbeat → block/complete`) and the orchestrator's "decompose, don't execute" rule are auto-injected into every kanban process as the `KANBAN_GUIDANCE` system-prompt block. This skill is the deeper detail when you need more than the lifecycle — handoff shapes, retry diagnostics, multi-CLI integration, edge cases.

## Sections

1. [Worker Pitfalls & Handoff Patterns](references/worker-pitfalls.md) — the auto-loaded `kanban-worker` skill content. Workspace handling, tenant isolation, `kanban_complete` metadata shapes, claim semantics, block reasons, retry scenarios, "do NOT" rules, CLI fallbacks.
2. [Orchestrator Decomposition Playbook](references/orchestrator-playbook.md) — the auto-loaded `kanban-orchestrator` skill content. Profile discovery, when to use the board vs `delegate_task`, anti-temptation rules, the task-graph sketch, gating with `parents=`, fan-out patterns.
3. [Codex Lane Pattern](references/codex-lane-pattern.md) — running Codex CLI as an isolated implementation lane inside a Kanban worker. Worktree isolation, PMB safety constraints, prompt construction, monitoring, reconciliation checklist, `kanban_complete.metadata.codex_lane` schema.

## When to Load This Umbrella

- Designing or debugging a Kanban workflow
- Spawning workers from an orchestrator profile
- Choosing between `kanban_create`, `delegate_task`, and `clarify` for handoffs
- Diagnosing why a task is `running` forever, `timed_out`, or `crashed`
- Integrating an external coding CLI (Codex, Claude Code, OpenCode) as a worker lane
- Auditing a board for stuck/orphaned tasks

## Shared Concepts (the lifecycle)

Both `kanban-worker` and `kanban-orchestrator` skills (and the supporting `kanban-codex-lane` skill) share the same lifecycle block. If you've read the `KANBAN_GUIDANCE` auto-injection you already have most of what you need — these three reference files add the deeper patterns.

The shared lifecycle in 6 steps:

1. **Orient** — `kanban_show(task_id)` to read the task body, status, and any comment thread (especially the unblock comment if you're a retry).
2. **Work** — use the workspace, write artifacts, run tests. For orchestrators, this means `kanban_create` (fan-out), not implementation.
3. **Heartbeat** — `kanban_heartbeat(note=...)` every few minutes for long tasks. Skip for sub-2-minute tasks.
4. **Block or Complete** — `kanban_complete(summary=..., metadata=...)` when terminal; `kanban_comment(...) + kanban_block(reason=...)` when a human decision is needed.
5. **Reconcile** (orchestrator) — aggregate child card results, write a synthesis card or summarize to the user.
6. **Cleanup** — kill stuck processes, remove temp worktrees, archive orphaned workspaces.

## Tool vs CLI Quick Reference

Every Kanban tool has a CLI equivalent. Use tools from inside an agent (they work across all terminal backends: Docker, Modal, SSH); use the CLI for human operators and shell scripts.

| Tool | CLI |
|------|-----|
| `kanban_show(id)` | `hermes kanban show <id> --json` |
| `kanban_complete(id, summary, metadata)` | `hermes kanban complete <id> --summary "..." --metadata '{...}'` |
| `kanban_block(id, reason)` | `hermes kanban block <id> "reason"` |
| `kanban_create(title, assignee, parents)` | `hermes kanban create "title" --assignee <profile> [--parent <id>]` |
| `kanban_heartbeat(note)` | `hermes kanban heartbeat --note "..."` |
| `kanban_comment(task_id, body)` | `hermes kanban comment <id> "body"` |
| `kanban_list(assignee, state)` | `hermes kanban list [--assignee <name>] [--state <state>]` |

> CLI doesn't exist in containerized backends (Docker, Modal, SSH) — when the worker runs in a container, the `hermes` CLI isn't on PATH. Always use the tool from inside an agent; the CLI is for the human at the terminal.

## How This Umbrella Was Built

This umbrella was assembled from three previously-separate skills (`kanban-worker`, `kanban-orchestrator`, `kanban-codex-lane`) that all target the same Hermes Kanban system but from different role perspectives. The originals are preserved in `references/` for back-compat with `--skills` invocations. New agents should load this umbrella for the cross-role view.

## Related Skills

- `hermes-agent` — the meta-umbrella for all Hermes internals (CLI, gateway, profiles, voice)
- `claude-code`, `codex`, `opencode` — external coding CLIs; the Codex lane pattern in §3 is one of the integration recipes
- `delegate-coding-agent` — broader class for "delegate coding to an external CLI" workflows
