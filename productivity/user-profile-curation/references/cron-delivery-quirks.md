# Cron Delivery Quirks (for user profile curation)

Specific patterns observed when running the user-profile-curation
workflow in cron context. These overlap with `daily-work-log`'s
constraints but apply to the user-model artifact specifically.

## Memory tool — persistent unavailability

**Symptom**: `memory(action="add", target="user", content=...)` returns:

```json
{"error": "Memory is not available. It may be disabled in config or
this environment.", "success": false}
```

**Observed frequency**: 100% in cron context (2026-06-03, 2026-06-04 runs).
Expected to persist — the memory tool is not wired into the cron gateway.

**Resolution**: Direct file write to `~/.hermes/memories/USER.md`. The
canonical file is what the next interactive session reads via
`cat ~/.hermes/memories/USER.md`, so it works regardless of the memory
tool state.

**Pattern**:

```python
try:
    memory(action="add", target="user", content=summary)
    memory_used = True
except Exception as e:
    if "Memory is not available" in str(e):
        # Fallback: write to canonical file directly
        write_file("~/.hermes/memories/USER.md", full_report)
        memory_used = False
    else:
        raise
```

**Document in the deliverable**: when the memory tool fails, the
report should say "memory 工具不可用 — 用直接写文件方案" so the user
knows the artifact is still up to date.

## GBrain CLI — invocation pattern

`gbrain` is a bun-based CLI, not a compiled binary. Calling it from
cron requires explicit PATH injection:

```bash
# ❌ WRONG — command not found in cron PATH
gbrain put user-profile-20260604 < file.md

# ✅ RIGHT — bun binary path injected
PATH="$HOME/.bun/bin:$PATH" gbrain put user-profile-20260604 < file.md
PATH="$HOME/.bun/bin:$PATH" gbrain embed --slugs user-profile-20260604
```

The path `~/.bun/bin/` is not auto-injected in cron (unlike
interactive shell which reads `~/.bashrc`).

After put, the slug needs an explicit `embed` call to be
semantically searchable:

```bash
PATH="$HOME/.bun/bin:$PATH" gbrain search "lxgxdx 用户身份"
# Expected: top hit user-profile-20260604 with similarity > 0.9
```

## Feishu webhook — typical failure mode

`oc_7c656031826c26b15f17d010097f3619` has been returning
**19001 "invalid access token"** for 48+ hours as of 2026-06-04.
This affects ALL cron notification delivery.

**Don't try to fix the webhook from a cron job** — there's no
interactive user present to re-authorize. Just deliver the report as
the final response (system auto-routes it) and document the issue
in the "待用户决策" section of the report.

**When the user does fix it**, the next interactive session should
update the canonical `USER.md` open_id line to note the fix date.

## The "send via Feishu" step in cron task spec

Cron task descriptions often include steps like "通过飞书发送给用户
(feishu:oc_...)". **The system prompt for cron jobs overrides this**:

> "Your final response will be automatically delivered to the user —
> do NOT use send_message or try to deliver the output yourself. Just
> produce your report/output as your final response and the system
> handles the rest."

The agent must NOT call `send_message` or any other delivery tool
in cron context. The gateway handles routing.

## File backup — automatic

When `cp` overwrites `~/.hermes/memories/USER.md`, Hermes auto-backs
up the previous version to `~/.hermes/memories/USER.md.bak.<timestamp>`.
You do not need to `cp` to a `.bak` first — the system handles it.

Observed backups as of 2026-06-04:
- `USER.md.bak.1780392841` (2026-06-02 17:34)
- `USER.md.bak.20260603_1780423406` (2026-06-03 02:03)

## State.db — direct read

`/home/lxgxdx/.hermes/state.db` is the cross-platform session
database. In cron context:

- `sqlite3` CLI is **not in PATH** — use `python3 -c "..."` instead
- Sessions table has a `started_at` column (Unix epoch), not
  `timestamp` / `created_at` / `ended_at`
- The `date()` SQL function works on `started_at` directly

```python
# ✅ Correct pattern
import sqlite3
from datetime import date, datetime, timedelta
y = date.today() - timedelta(days=1)
ys = datetime(y.year, y.month, y.day, 0, 0, 0).timestamp()
ye = datetime(y.year, y.month, y.day, 23, 59, 59).timestamp()
c = sqlite3.connect('/home/lxgxdx/.hermes/state.db')
rows = c.execute(
    'SELECT id, source, started_at, message_count FROM sessions '
    'WHERE started_at >= ? AND started_at <= ? ORDER BY started_at',
    (ys, ye)
).fetchall()
```

## Pitfall: empty assistant messages

When reading sessions.json for the daily log, some sessions have
empty/short final assistant messages. This indicates the previous
cron cycle was interrupted (CAPTCHA, tool failure, no final summary).
Always check the last asst message length and flag in
"未完成 / 待跟进" if it's empty.
