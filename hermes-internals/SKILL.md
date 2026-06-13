---
name: hermes-internals
description: Class-level guide to Hermes Agent internals — authoring SKILL.md files, debugging the s6-overlay container supervision tree, fixing the TUI/CLI/gateway slash-command layer, and tracing per-model capability resolution (context window, max output tokens, pricing). Load when contributing to Hermes, debugging slash-command issues, patching model_metadata.py, or diagnosing container supervision failures.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, hermes-internals, s6, supervisor, docker, tui, slash-commands, model-metadata, skill-authoring, context-window, gateway]
    related_skills: [hermes-agent, hermes-agent-skill-authoring, hermes-s6-container-supervision, debugging-hermes-tui-commands, hermes-model-metadata-debugging]
---

# Hermes Internals — Engineering & Debugging

This umbrella covers the engineering side of Hermes Agent: the SKILL.md format, the s6-overlay container tree, the TUI/gateway slash-command layer, and per-model capability resolution. If you're using Hermes from the user's perspective, load `hermes-agent` instead. If you're patching, debugging, or extending Hermes internals, load this.

> The four original skills folded into this umbrella (`hermes-agent-skill-authoring`, `hermes-s6-container-supervision`, `debugging-hermes-tui-commands`, `hermes-model-metadata-debugging`) cover distinct Hermes subsystems. They're preserved as references below so you can deep-dive into any one of them.

## Sections

1. [SKILL.md Authoring](references/skill-authoring.md) — the original `hermes-agent-skill-authoring` skill. Frontmatter schema, validator, structure conventions, the peer-skill length target (8-14k chars), the `references/` / `templates/` / `scripts/` / `assets/` subdir allowlist, and worked examples of upstream-tool-adapter patterns.
2. [s6-overlay Container Supervision](references/s6-container-supervision.md) — the original `hermes-s6-container-supervision` skill. Adding/removing supervised services, debugging profile gateways that won't start, understanding the Architecture B main-program pattern (`/opt/hermes/docker/main-wrapper.sh` + leading-dash args).
3. [TUI Slash Command Debugging](references/tui-commands-debugging.md) — the original `debugging-hermes-tui-commands` skill. The 3-layer architecture (Python registry → tui_gateway JSON-RPC → Ink/TypeScript UI), why commands work in CLI but not TUI, the autocomplete miss, the config-persistence/UI-update race.
4. [Model Metadata Debugging](references/model-metadata-debugging.md) — the original `hermes-model-metadata-debugging` skill. Where the 200K/32K/1M context window comes from, how to override it, the `agent/model_metadata.py` and `agent/models_dev.py` tables, the layering order (override → table → models.dev → fallback).
5. [MiniMax-M3 Case Study](references/minimax-m3-case.md) — the actual 2026-06-01 session trace of a metadata resolution problem, showing the search commands and the layering findings applied to a real model.
6. [Upstream Tool Adapter Pattern](references/upstream-tool-adapter-pattern.md) — worked example: how to wrap a third-party CLI tool as a Hermes skill (Hermes sessions → SkillOpt-Sleep pattern).
7. [Skill Evolution from History](references/skill-evolution-from-history.md) — how to mine session history for skill patterns and persist them.

## When to Load This Umbrella

- Writing or reviewing a new SKILL.md (or fixing an existing one)
- Debugging a Hermes Docker container (s6 service won't start, gateway won't boot)
- Diagnosing why a slash command works in CLI but not in TUI (or vice versa)
- Resolving a model metadata disagreement (Hermes says 200K, the provider says 1M)
- Contributing a tool, plugin, or platform adapter
- Auditing a Hermes installation for internal consistency

## Scripts

- `scripts/trace-context-window.py` — runs the Hermes context-window resolver end-to-end and prints which layer (override / table / models.dev / fallback) supplied the number. **Use this when debugging a new model — saves you from re-grepping the source.**

## Decision: Load `hermes-agent` or This Umbrella?

| Task | Skill to load |
|------|---------------|
| Configure Hermes (CLI, profile, gateway, voice) | `hermes-agent` |
| Use a Hermes feature (cron, kanban, webhook) | `hermes-agent` |
| Write a new SKILL.md | **this umbrella** (§1) |
| Debug a container service | **this umbrella** (§2) |
| Fix a TUI slash command | **this umbrella** (§3) |
| Resolve model metadata | **this umbrella** (§4) |
| Spawn another Hermes instance | `hermes-agent` |
| Troubleshoot the Kanban board | `hermes-kanban` |

## Related Skills

- `hermes-agent` — the user-facing umbrella (CLI, setup, gateway, profiles). Load this for "how do I use Hermes?" questions.
- `hermes-kanban` — the Kanban multi-agent system (worker/orchestrator/codex-lane).
- `hermes-agent-skill-authoring`, `hermes-s6-container-supervision`, `debugging-hermes-tui-commands`, `hermes-model-metadata-debugging` — the four original skills that were merged into this umbrella. Now archived; their full content lives in the `references/` above.
