---
name: user-profile-curation
description: >
  Periodic user profile maintenance. Analyze conversation history across
  platforms, build/extend a structured user model report, persist durable
  insights to canonical files + GBrain, and handle the memory-tool-
  unavailable case in cron contexts. Triggers: cron "深度分析用户模型——
  从历史对话中学习用户" task running weekly/biweekly; user says
  "更新用户画像" / "user profile update" / "记住我的偏好"; major
  workflow change observed (new project, new persona). NOT for: one-off
  fact capture ("remember I have a cat"), single-session preference
  tracking, PII-only data dumps.
tags: [user-model, profile, periodic, cron, persistence, gbrain]
category: productivity
---

# User Profile Curation

Periodic user profile maintenance — turn conversation history into a
durable, structured, version-controlled user model that the next session
can start with.

## When to use this

| Trigger | Type |
|---------|------|
| Cron "深度分析用户模型——从历史对话中学习用户" | Periodic (weekly or after major changes) |
| User says "更新用户画像" / "user profile" / "记住我的偏好" | Interactive |
| Major workflow change (new project, new persona, new tools) | Event-driven |

Skip for: one-off fact capture, single-session preference tracking,
PII-only data dumps. Those belong in `memory` (if available) or in a
specific domain skill, not a periodic profile.

## Workflow

### 1. Read the baseline (don't start from scratch)

```bash
ls -la ~/.hermes/memories/USER.md ~/.hermes/memories/user_model_report_*.md
```

Read both the canonical `USER.md` and the latest dated
`user_model_report_YYYYMMDD.md`. They may differ — the dated snapshot is
ground truth; USER.md is the live editable copy. Identify:

- **Corrections list** — count actual rows in the table, not the v(n-1)
  self-claim. The meta-claim is often wrong (see Pitfalls).
- **Last analysis date** — this is your data window start.
- **Unchanged sections** — preserve verbatim; only update what changed.
- **New deltas to add** — list explicitly so v(n) has structure.

### 2. Compute the delta window

```python
import sqlite3
from datetime import datetime, date
c = sqlite3.connect('/home/lxgxdx/.hermes/state.db')
# Replace last_date with the v(n-1) analysis date
last_ts = datetime(2026, 6, 3).timestamp()
rows = c.execute(
    'SELECT id, source, started_at, message_count FROM sessions '
    'WHERE started_at >= ? ORDER BY started_at', (last_ts,)
).fetchall()
```

Sort by source before reading:
- `feishu` / `weixin` / `telegram` / `cli` — user-initiated, deep-read
- `cron` — automated tasks, read first+last assistant msg only

### 3. Broad keyword sweeps (5+ queries)

OR-join keywords per profile bucket. Run in parallel if possible:

```python
# Identity bucket
session_search(query="用户名 OR 名字 OR 纠正", limit=10)
# Workflow bucket
session_search(query="PPT OR 培训 OR 工作 OR 风格", limit=10)
# Tech env bucket
session_search(query="home assistant OR 服务器 OR 设备", limit=10)
# Preferences bucket
session_search(query="不要 OR 太长 OR 简单点 OR 风格", limit=10)
# Communication bucket
session_search(query="飞书 OR 微信 OR Telegram OR 通知", limit=10)
```

For non-Chinese users, swap the keywords. The point is broad OR coverage
across the four buckets the profile cares about.

### 4. Deep scroll on high-value sessions

A snippet match is a hint, not evidence. Scroll into the actual session
content for any session mentioning:
- a correction ("不要...", "错了", "应该是...", "以后都...")
- a persistent topic recurring across multiple sessions
- a tool/service first introduced (track when added)
- a recurring deliverable format (information稿, PPT style, etc.)

```python
session_search(session_id="...", around_message_id=12345, window=10)
```

#### ⚠️ Persisted-output session_search trap

`session_search` discovery mode returns up to ~220KB per query. When a
keyword hits a high-traffic topic (e.g. "统战", "政府", "用户"),
the result is auto-saved to `/tmp/hermes-results/call_function_<id>_<n>.txt`
and you see only a 1500-char preview. **The preview's `bookend_start` /
`messages` are the actual content — read them with `read_file` on
specific line ranges, do NOT try to re-query.** Reading the persisted
file directly is faster than re-running the same search.

Typical workflow:
1. Notice the "This tool result was too large" message + persisted path
2. `read_file(path, offset=N, limit=200)` to scan top of the result
3. Pick session IDs that match the buckets you care about (corrections,
   new discoveries, recurring topics)
4. `session_search(session_id=<id>, around_message_id=<anchor>, window=10)`
   to deep-scroll the high-value ones

Also: large results are deduped per `session_id` + snippet, so a single
broad query can be more useful than 5 narrow ones if you cast a wide
net deliberately.

### 5. Generate the v(n) report

8-section Markdown structure. See `references/v4-template.md` for the
full template with section-by-section authoring notes.

Sections in order:
1. **基础画像** — identity table
2. **v(n) 增量** — delta from v(n-1) (the most important section)
3. **工作特征** — work breakdown by priority
4. **交互偏好** — likes/dislikes + corrections table
5. **技术环境** — hardware/software/services
6. **生活习惯 & 兴趣**
7. **关键路径速查** — key paths in a code block (easy to scan)
8. **洞察 & 可主动帮助的点** — proactive-help opportunities
9. **待用户决策** — open questions

**Size target** (nuanced, not a hard ±20%):
- **Routine update** (no major new discoveries since v(n-1)): target ±10%. v3→v4 was 19KB→18KB (this pattern).
- **Major new discovery** (new AI model capability, new class of work, new tech stack addition, 3+ new corrections): up to +30% acceptable. v4→v5 was 18.7KB→23.4KB (+25%) — legitimate growth from M3 multimodal section + 8-skill refactor table + 3 new corrections, NOT re-invention.
- **Major restructure** (new section added without removing any): create the new section, do NOT duplicate existing content. Growth is fine if content is genuinely new.
- Hard rule: if growth exceeds 30%, you almost certainly re-invented a field — re-read v(n-1) sections and prune.
- Smaller than v(n-1) means you lost context.

**Size target**: ±20% of v(n-1). v3 was 19KB, v4 was 18KB — that's the
right range. Bigger means you re-invented fields; smaller means you
lost context.

### 6. Persist (3 files + 1 GBrain slug)

```bash
# 1) Dated archive snapshot
write_file(~/.hermes/memories/user_model_report_YYYYMMDD.md, <v(n)>)

# 2) GBrain-friendly mini snapshot (≤ 5KB, dense)
write_file(~/.hermes/memories/daily/YYYY-MM-DD-user-model-snapshot.md, <mini>)

# 3) Update canonical USER.md in place
cp ~/.hermes/memories/user_model_report_YYYYMMDD.md ~/.hermes/memories/USER.md

# 4) Ingest to GBrain for semantic search
PATH="$HOME/.bun/bin:$PATH" gbrain put user-profile-YYYYMMDD \
  < ~/.hermes/memories/daily/YYYY-MM-DD-user-model-snapshot.md
PATH="$HOME/.bun/bin:$PATH" gbrain embed --slugs user-profile-YYYYMMDD
```

Hermes auto-backs up the previous USER.md to `USER.md.bak.<timestamp>`
when overwritten, so v(n-1) is preserved.

### 7. Deliver

- **Cron**: Just produce the report as the final response. The system
  auto-delivers it. Do NOT call `send_message` or `feishu:...` —
  the cron system prompt overrides the task spec: "do NOT use
  send_message or try to deliver the output yourself."
- **Interactive**: Send the full report via the user's preferred
  channel (typically Feishu for government-vertical users; ask if
  unsure). The profile should record the open_id.

## Pitfalls

### ⚠️ Memory tool almost certainly unavailable in cron

The `memory` tool returns `"Memory is not available. It may be disabled
in config or this environment."` in cron contexts — this is normal, not
an error. Fall back to direct file write on the first failed call:

```python
# ❌ WRONG: keep retrying
for i in range(3):
    try: memory(action="add", target="user", content=...)
    except: continue  # wastes turns

# ✅ RIGHT: one try, then fall back
try:
    memory(action="add", target="user", content=...)
except Exception:
    write_file(~/.hermes/memories/USER.md, ...)
```

Document the fallback in the deliverable so the user knows the
canonical file is up to date even though the memory tool failed.

### ⚠️ v(n-1) self-claim drift

If v(n-1) says "12 corrections" but the table body has 14 rows, the
self-claim is wrong. v(n) should report the **actual** count from the
body. This drift is normal — the meta-claim gets out of date as new
corrections are added incrementally. Always cross-reference the body,
not the header.

### ⚠️ Don't fabricate corrections

Every correction in the v(n) list must trace to a specific session +
message. If you can't find the source, mark it `[unverified]` or drop
it. Real corrections are rare (~1 per week); do not pad the list with
synthetic entries to make it look "rich."

### ⚠️ Cron task spec may ask for "send via Feishu"

Cron task descriptions often include "send to user via Feishu" steps.
The system prompt for cron jobs overrides this: "do NOT use send_message
or try to deliver the output yourself. Just produce your report/output
as your final response and the system handles the rest." The user's
notification channel is the gateway's job, not the agent's.

### ⚠️ Cron "成功幻觉" — agent 汇报与现实脱节

In cron mode, agent sometimes reports "已创建 N 个文件" in the final
asst message but the files don't actually exist on disk. Two real
patterns observed in 2026-06-05 alone:

1. **PVE Wiki cron** (`llm-wiki-build`): asst said "4 core pages created"
   but `ls ~/wiki/concepts/` showed all 4 missing. GBrain search also
   returned no hits.
2. **Problem-class topics cron** (`tongzhan-info-workflow`): asst last
   message was 0 chars, the target file was never written even though
   intermediate asst messages had completed the content design.

The user-profile report itself is a cron write — v(n) MUST verify
the 3 files have non-zero size AND GBrain has a `user-profile-YYYYMMDD`
slug before declaring success.

**Mitigation (defense-in-depth)**:
- After every `write_file`, run `os.path.getsize()` to confirm > 1KB
- Add a verification step to the final asst report (show actual file
  sizes, not the count)
- Use the shared `scripts/verify-cron-writes.sh` helper for batched
  writes (see See also)

See `references/cron-success-hallucination.md` for full analysis +
3 affected skills + the verification script.

### ⚠️ Don't make the file much bigger without justification

If v(n) jumps from 19KB to 40KB, you probably re-invented fields
instead of doing a delta update. The nuanced target is ±10% for routine
updates and up to +30% only when justified by major new discoveries
(new model capability, new class of work, 3+ new corrections, new tech
stack addition). Document the growth reason in the v(n) 增量 section so
future you can audit. If you need a major restructure, create a new
section but don't duplicate existing content.

### ⚠️ Cron env has additional constraints

Inherited from `daily-work-log` pitfalls:
- `execute_code` is **disabled** in cron (returns BLOCKED)
- `terminal` heredoc (`python3 << EOF`) is **pattern-blocked**
- `sqlite3` CLI is **not in PATH** — use `python3 -c "..."` instead
- `gbrain` requires explicit `PATH="$HOME/.bun/bin:$PATH"` prefix

### ⚠️ Search hits return truncated bookends

`session_search` discovery results are truncated to ~150KB. If you need
more, scroll into specific sessions by id + message id, or read the
session directly.

## Verification

- [ ] 3 files exist with non-zero size: `USER.md`,
      `user_model_report_YYYYMMDD.md`,
      `daily/YYYY-MM-DD-user-model-snapshot.md` (sizes should be in the
      KB range, not 0B)
- [ ] GBrain `user-profile-YYYYMMDD` slug returns hits in semantic
      search (`gbrain search "<a unique phrase from the report>"`)
- [ ] `gbrain stats` shows total chunks grew by ~1 from the new slug
- [ ] USER.md corrections count matches actual table row count
- [ ] Previous USER.md version preserved (Hermes auto-backs up)
- [ ] All v(n-1) corrections still present in v(n) — corrections are
      append-only, never deleted
- [ ] Final response includes the full report (cron auto-delivers)
- [ ] Final asst's "完成报告" lists actual file sizes (not just counts)
      — see cron-success-hallucination pitfall above
- [ ] For batched writes (e.g. N wiki pages), `scripts/verify-cron-writes.sh`
      exit code is 0 before declaring success

## See also

- `daily-work-log` — sibling skill for daily log generation; shares
  the same cron-mode constraints (memory tool unavailable, heredoc
  blocked, no sqlite3 CLI, etc.). Read its pitfalls section for
  cross-reference on cron environment quirks.
- `references/v4-template.md` — full v4 report structure with
  section-by-section authoring notes for v5+ updates
- `references/cron-delivery-quirks.md` — deeper notes on memory tool
  unavailability, GBrain ingestion, and the system auto-deliver override
- `references/gbrain-ingestion-quirks.md` — two real GBrain verification
  gotchas ("already embedded" ≠ findable; stats lag); read this BEFORE
  the GBrain step in the workflow, not after panicking
- `references/cron-success-hallucination.md` — **cron task "成功幻觉"
  failure pattern + 3-layer defense**; relevant for any write-bearing
  cron skill (wiki builder, info workflow, etc.), not just this one
- `scripts/verify-cron-writes.sh` — bash helper that checks N paths
  exist and are >= 1KB. Use as the last step of any cron write task.
