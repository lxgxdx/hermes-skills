# Upstream Tool Adapter Pattern (worked example)

## The problem

You have an upstream tool (e.g. `microsoft/SkillOpt`) that assumes one agent's session format (e.g. Claude Code's `~/.claude/projects/<slug>/<sessionId>.jsonl`). Your agent (Hermes Agent) stores sessions in a different place and schema (`~/.hermes/sessions/*.jsonl` with a flatter record format).

You want to use the upstream tool on YOUR sessions without forking it.

## The pattern: write an adapter, don't fork the tool

**Three principles**:

1. **Adapter sits between YOUR data source and the tool's expected input.** The tool stays unchanged. The adapter reads your format, emits theirs, into a "bridge" directory the tool reads from.

2. **One-way data flow, no shared state.** Adapter writes only to the bridge dir. Tool reads only from the bridge dir. Neither touches the other's source paths. This means re-running the adapter is idempotent and safe.

3. **Default to no-op / mock** for any expensive or mutating operation the upstream tool provides.

## Worked example: Hermes sessions → SkillOpt-Sleep

### Format difference (hermes vs claude code)

| Hermes record | Claude Code record | Mapping |
|---|---|---|
| `{"role": "user", "content": "..."}` | `{"type": "user", "message": {"role": "user", "content": "..."}}` | Flattened → nested, add `type` |
| `{"role": "assistant", "content": "", "tool_calls": [...]}` | `{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": ""}, {"type": "tool_use", "name": "...", "input": {...}}]}}` | tool_calls list → tool_use content blocks |
| `{"role": "tool", "content": "[view] ..."}` | (no direct equivalent) | **DROPPED** — tool results add no training signal |
| (no `cwd`/`gitBranch` field) | `cwd`, `gitBranch` per record | Inject user's home dir, empty gitBranch |

### Adapter file shape

```python
# hermes_session_adapter.py
HERMES_SESSIONS = Path("~/.hermes/sessions").expanduser()
BRIDGE_DIR = Path("~/.skillopt-sleep/hermes_bridge").expanduser()
SLUG = "hermes-agent"  # single synthetic "project" — all sessions collapse here

def _hermes_to_claude_records(hermes_records): ...
def _bridge_path(src): ...  # stable hash so re-runs overwrite
def _atomic_write_jsonl(path, records): ...  # write to .tmp, rename
def _iter_hermes_jsonl(since_iso): ...  # rglob + filter
def run(since, dry_run): ...
```

### Sync state (incremental, not destructive)

```python
def _load_sync_state(path): ...   # {abs_path: "mtime:size"}
def _save_sync_state(path, state): ...
```

Key rule: **use a content-signature like `f"{mtime:.3f}:{size}"`** as the state value. Don't hash content — mtime+size is 1000x faster and identical for the cron use case (files only change when appended to).

### Filter list (very important)

Exclude paths that look like sessions but aren't real user activity:

```python
_EXCLUDE_PATH_SUBSTRINGS = (
    "/.dreams/",        # hermes's own dream event log
    "/dreams/",
    "/memory/.events",
    "/migration/openclaw",  # historical imports
)
```

This is the difference between training on **149 real sessions** vs **158 noisy files including internal events**.

### Default safety flags

| Flag | Value | Why |
|---|---|---|
| `dry_run=True` initially | yes | See what tool would do before spending API budget |
| `auto_adopt=False` | yes | Tool's gate should be the ONLY thing that auto-applies changes |
| `gate_mode="on"` | yes | Bounded-edit validation gate (the whole point of the tool) |
| `edit_budget=4` | yes | Cap on edits per night = "textual learning rate" |
| `val_fraction=0.34` | yes | 34% of mined tasks held out as gate validation set |

### One-shot wrapper shell script

```bash
#!/usr/bin/env bash
# sync-and-run.sh
SKILLOPT_VENV="${SKILLOPT_VENV:-/tmp/skillopt/.venv}"
source "$SKILLOPT_VENV/bin/activate"
python adapter.py --since "$HERMES_SINCE" --incremental
python -m upstream_tool "$@" --claude-home "$BRIDGE_DIR"
```

Single entry point. Cron calls one command. Logs are grep-friendly with timestamps.

## What you DON'T do

- ❌ Don't fork the upstream tool to add a "hermes backend" — it rots.
- ❌ Don't symlink `~/.claude` → `~/.hermes/sessions` — the schemas differ, the tool will read garbage and silently fail.
- ❌ Don't add a "hermes mode" flag to the upstream tool's config — it's a maintenance burden you don't own.
- ❌ Don't convert 149 files every cron run — without incremental state you'll burn 30s on every tick.
- ❌ Don't `pip install pkg` and assume subpackages are included — many research tools ship the bare bones on PyPI.

## Files this pattern produces

```
~/.hermes/skills/<category>/<name>/
├── SKILL.md                              # 4-10k chars, trigger + overview + commands + pitfalls
├── references/
│   └── cheatsheet.md                     # speed-dial command table + error→fix table
├── scripts/
│   ├── <thing>_adapter.py                # the format bridge
│   └── sync-and-run.sh                   # one-shot wrapper
└── (optional) templates/                 # starter config files
```

## Verification checklist

- [ ] `python adapter.py --dry-run` shows correct N sessions scanned
- [ ] `python adapter.py` (real run) produces N output files in bridge dir
- [ ] `python -m upstream_tool harvest` reports `N sessions -> M tasks` with M > 0
- [ ] `python -m upstream_tool dry-run` completes without API error
- [ ] Re-running `python adapter.py` reports `skipped (unchanged)` for all but the newest files
- [ ] Cron logs show the wrapper exits 0 within the time budget
