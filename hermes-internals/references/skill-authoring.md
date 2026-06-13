---
name: hermes-agent-skill-authoring
description: "Author in-repo SKILL.md: frontmatter, validator, structure."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, hermes-agent, conventions, skill-md]
    related_skills: [writing-plans, requesting-code-review]
---

# Authoring Hermes-Agent Skills (in-repo)

## Overview

There are two places a SKILL.md can live:

1. **User-local:** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal, not shared. Created via `skill_manage(action='create')`.
2. **In-repo (this skill is about this case):** `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` — committed, shipped with the package. Use `write_file` + `git add`. `skill_manage(action='create')` does NOT target this tree.

## When to Use

- User asks you to add a skill "in this branch / repo / commit"
- You're committing a reusable workflow that should ship with hermes-agent
- You're editing an existing skill under `/home/bb/hermes-agent/skills/` (use `patch` for small edits, `write_file` for rewrites; `skill_manage` still works for patch on in-repo skills, but not for `create`)

## Required Frontmatter

Source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`. Hard requirements:

- Starts with `---` as the first bytes (no leading blank line).
- Closes with `\n---\n` before the body.
- Parses as a YAML mapping.
- `name` field present.
- `description` field present, ≤ **1024 chars** (`MAX_DESCRIPTION_LENGTH`).
- Non-empty body after the closing `---`.

Peer-matched shape used by every skill under `skills/software-development/`:

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

`version` / `author` / `license` / `metadata` are NOT enforced by the validator, but every peer has them — omit and your skill sticks out.

## Size Limits

- Description: ≤ 1024 chars (enforced).
- Full SKILL.md: ≤ 100,000 chars (enforced as `MAX_SKILL_CONTENT_CHARS`, ~36k tokens).
- Peer skills in `software-development/` sit at **8-14k chars**. Aim for that range. If you're pushing past 20k, split into `references/*.md` and reference them from SKILL.md.

## Peer-Matched Structure

Every in-repo skill follows roughly:

```
# <Title>

## Overview
One or two paragraphs: what and why.

## When to Use
- Bulleted triggers
- "Don't use for:" counter-triggers

## <Topic sections specific to the skill>
- Quick-reference tables are common
- Code blocks with exact commands
- Hermes-specific recipes (tests via scripts/run_tests.sh, ui-tui paths, etc.)

## Common Pitfalls
Numbered list of mistakes and their fixes.

## Verification Checklist
- [ ] Checkbox list of post-action verifications

## One-Shot Recipes (optional)
Named scenarios → concrete command sequences.
```

Not every section is mandatory, but `Overview` + `When to Use` + actionable body + pitfalls are the minimum for the skill to feel like a peer.

## Directory Placement

### In-repo (shipped with hermes-agent)
```
skills/<category>/<skill-name>/SKILL.md
```
Use `write_file` + `git add` + `git commit`. `skill_manage(action='create')` does NOT write here.

### User-local (`~/.hermes/skills/`)
```
~/.hermes/skills/<maybe-category>/<skill-name>/SKILL.md
```
Use `skill_manage(action='create')` (auto-writes to this tree) or `write_file` directly. Personal, not committed, not shared. **This is where personal automation skills live** — e.g. a SkillOpt-Sleep integration that adapts an upstream tool to your own session format.

### In-repo categories
Categories currently in repo (confirm with `ls skills/`): `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `leisure`, `mcp`, `media`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Pick the closest existing category. Don't invent new top-level categories casually.

For user-local skills, the category is optional — `~/.hermes/skills/<name>/SKILL.md` is just as valid as `~/.hermes/skills/<category>/<name>/SKILL.md`. Use a category only when you already have 3+ skills in the same domain (e.g. `~/.hermes/skills/productivity/` has gbrain-ops, daily-work-log, meeting-minutes-generator, etc.).

## Workflow

1. **Survey peers** in the target category:
   ```
   ls skills/<category>/
   ```
   Read 2-3 peer SKILL.md files to match tone and structure.
2. **Check validator constraints** in `tools/skill_manager_tool.py` if unsure.
3. **Draft** with `write_file` to `skills/<category>/<name>/SKILL.md`.
4. **Validate locally**:
   ```python
   import yaml, re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = yaml.safe_load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 1024
   assert len(content) <= 100_000
   ```
5. **Git add + commit** on the active branch.
6. **Note:** the CURRENT session's skill loader is cached — `skill_view` / `skills_list` will not see the new skill until a new session. This is expected, not a bug.

## Cross-Referencing Other Skills

`metadata.hermes.related_skills` unions both trees (`skills/` in-repo and `~/.hermes/skills/`) at load time. You CAN reference a user-local skill from an in-repo skill, but it won't resolve for other users who clone the repo fresh. Prefer referencing only in-repo skills from in-repo skills. If a frequently-referenced skill lives only in `~/.hermes/skills/`, consider promoting it to the repo.

## Editing Existing In-Repo Skills

- **Small fix (typo, added pitfall, tightened trigger):** `skill_manage(action='patch', name=..., old_string=..., new_string=...)` works fine on in-repo skills.
- **Major rewrite:** `write_file` the whole SKILL.md. `skill_manage(action='edit')` also works but requires supplying the full new content.
- **Adding supporting files:** `write_file` to `skills/<category>/<name>/references/<file>.md`, `templates/<file>`, or `scripts/<file>`. `skill_manage(action='write_file')` also works and enforces the references/templates/scripts/assets subdir allowlist.
- **Always commit** the edit — in-repo skills are source, not runtime state.

## User-Local Skills (the OTHER tree)

The in-repo tree above is for skills that ship with hermes-agent. But most of the skills in this user's `~/.hermes/skills/` tree are **personal automation** — wrappers around upstream tools (SkillOpt-Sleep, gbrain, Wiki, etc.) tuned to their own environment. Those follow a DIFFERENT (simpler) convention:

### Frontmatter shape for user-local skills

```yaml
---
name: my-automation-skill
description: <trigger words in Chinese or English, comma-separated>。触发词：xxx/yyy/zzz
---
```

That's it. **No** `version` / `author` / `license` / `metadata.hermes` block required. The validator only enforces `name` + `description` + frontmatter syntax. The validator's MAX_DESCRIPTION_LENGTH (1024) still applies. Personal skills are shorter (often 4-10k chars), often in Chinese, and trigger on imperative phrases the user actually types.

### When to use user-local vs in-repo

| Use **user-local** (`~/.hermes/skills/`) when... | Use **in-repo** (`/home/bb/hermes-agent/skills/`) when... |
|---|---|
| Skill references YOUR local paths/credentials | Skill is generally useful across all hermes users |
| Skill is in your native language | Skill is in English (or multilingual by design) |
| Skill is a wrapper around an upstream tool (SkillOpt, gbrain, Wiki) | Skill teaches hermes itself how to do X |
| Skill is WIP / not yet stable | Skill is stable, tested, peer-reviewed |
| Quick: just `skill_manage(action='create', ...)` | Slower: `write_file` + `git add` + `git commit` + PR |

### User-local skill file layout

A well-shaped user-local skill looks like:

```
~/.hermes/skills/<category>/<name>/
├── SKILL.md                      # 4-15k chars, frontmatter + body
├── references/
│   └── cheatsheet.md             # speed-dial commands, error tables
├── templates/
│   └── <boilerplate>.<ext>       # starter files to copy+modify
└── scripts/
    └── <runner>.<sh|py>          # statically re-runnable actions
```

This 4-folder shape mirrors in-repo skills (see "Peer-Matched Structure" above). The user's home-tree skills in `~/.hermes/skills/productivity/` (gbrain-ops, daily-work-log, etc.) all follow this pattern.

### Special case: adapting an upstream tool's session format

A common user-local pattern is "wrap a tool that speaks Claude Code format so it works with my Hermes Agent sessions". Template:

1. **Don't fork the upstream tool.** It will rot.
2. **Write an adapter** that reads YOUR format and emits THEIRS. E.g. `hermes_session_adapter.py` reads `~/.hermes/sessions/*.jsonl` and emits Claude Code-shaped jsonl into a "bridge" directory.
3. **Document the format difference** at the top of the adapter — both record schemas, field-by-field mapping, what's lossy.
4. **Incremental sync state** so cron doesn't re-convert 149 unchanged files on every run. Use a `mtime:size` signature.
5. **Default to DRY-RUN / MOCK** for any expensive LLM step in the upstream tool. The user's safety instinct: "看产出再决定开不开真 API".
6. **Default `auto_adopt=false`** on any output that modifies live state. Always.

See `references/upstream-tool-adapter-pattern.md` for a worked example (Hermes sessions → SkillOpt-Sleep).

## Common Pitfalls

1. **Using `skill_manage(action='create')` for an in-repo skill.** It writes to `~/.hermes/skills/`, not the repo tree. Use `write_file` for in-repo creation.

2. **Leading whitespace before `---`.** The validator checks `content.startswith("---")`; any leading blank line or BOM fails validation.

3. **Description too generic.** Peer descriptions start with "Use when ..." and describe the *trigger class*, not the one task. "Use when debugging X" > "Debug X".

4. **Forgetting the author/license/metadata block.** Not validator-enforced, but every peer has it; omitting makes the skill look half-finished.

5. **Writing a skill that duplicates a peer.** Before creating, `ls skills/<category>/` and open 2-3 peers. Prefer extending an existing skill to creating a narrow sibling.

6. **Expecting the current session to see the new skill.** It won't. The skill loader is initialized at session start. Verify in a fresh session or via `skill_view` using the exact path.

7. **Linking to skills that don't exist in-repo.** `related_skills: [some-user-local-skill]` works for you but breaks for other clones. Prefer only in-repo links.

8. **User-local skills have a SIMPLER frontmatter** (no version/author/license/metadata block required). See "User-Local Skills" below. The validator's required fields are only `name` + `description`; in-repo peers add the metadata block to look uniform, but personal skills don't need it.

9. **`pip install pkg` succeeded but `import pkg.subpackage` fails with ModuleNotFoundError.** Common with research tools that keep "decoupled" subpackages out of the PyPI distribution (e.g. microsoft/SkillOpt ships `skillopt` on PyPI but `skillopt_sleep` is GitHub-only). **Diagnostic**: `pip show -f pkg | grep subpackage` returns empty. **Fix**: `pip install -e /path/to/github/clone` (editable install from source).

10. **Ubuntu 24.04 (and Debian 12+) `python3 -m venv` fails with "ensurepip not available".** The system Python ships without ensurepip. **Fix**: `sudo apt install -y python3.12-venv` (match the version), then re-run. PEP 668 also blocks system-wide `pip install` — always use a venv on modern Ubuntu.

11. **Mistaking `accept_all=false` for a bug.** When you wire a tool that has a "review-then-adopt" gate (e.g. SkillOpt-Sleep's `gate_mode=on`), the first run WILL show `accepted=False` with mock data — that's the design, not a failure. The gate is supposed to reject when validation score doesn't improve. Only escalate if real-LLM runs (with real replay) also reject for several nights in a row.

## Verification Checklist

- [ ] File is at `skills/<category>/<name>/SKILL.md` (not in `~/.hermes/skills/`)
- [ ] Frontmatter starts at byte 0 with `---`, closes with `\n---\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Name ≤ 64 chars, lowercase + hyphens
- [ ] Description ≤ 1024 chars and starts with "Use when ..."
- [ ] Total file ≤ 100,000 chars (aim for 8-15k)
- [ ] Structure: `# Title` → `## Overview` → `## When to Use` → body → `## Common Pitfalls` → `## Verification Checklist`
- [ ] `related_skills` references resolve in-repo (or are explicitly OK to be user-local)
- [ ] `git add skills/<category>/<name>/ && git commit` completed on the intended branch

## Appendix: Evolving an Existing Skill from Historical Conversations

When the user says "optimize this skill based on historical conversations" or similar, follow the workflow in `references/skill-evolution-from-history.md`:

1. Read the full SKILL.md
2. Search broadly across sessions for lessons
3. Categorize into: workflow corrections, preferences, fallback updates, validation gaps, context checks
4. Apply targeted patches (not full rewrites)
5. Record evolution in `references/YYYY-MM-DD-evolution-notes.md`

Key insight: self-evolution tools can only optimize invocation wrappers, not skill content. Content improvements are manual.
