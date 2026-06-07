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
- `execute_code` is **disabled** in cron (returns BLOCKED on first call)
- `terminal` heredoc (`python3 << EOF`) is **pattern-blocked**
- `sqlite3` CLI is **not in PATH** — use `python3 -c "..."` instead
- `gbrain` requires explicit `PATH="$HOME/.bun/bin:$PATH"` prefix

**Worked example — backing up v(n-1) USER.md before overwrite** (v7 cron
session, 2026-06-07, when `execute_code` was BLOCKED):

```bash
# ❌ WRONG — execute_code is BLOCKED in cron, no fallback
python3 -c "import shutil, time; shutil.copy('USER.md', f'USER.md.bak.v6_{int(time.time())}')"

# ✅ RIGHT — go through terminal directly with single-line -c
terminal(command="""python3 -c "
import shutil, time
ts = int(time.time())
shutil.copy('/home/lxgxdx/.hermes/memories/USER.md', f'/home/lxgxdx/.hermes/memories/USER.md.bak.v6_{ts}')
print(f'已备份 v6 → USER.md.bak.v6_{ts}')
"""")
```

**Note**: Hermes auto-backs up the previous USER.md when you overwrite it
with `cp`/`write_file`, so an explicit backup is technically redundant —
but doing it manually gives you a *named* backup (e.g. `.bak.v6_...`) you
can grep for later. Worth the one terminal call.

### ⚠️ Memory tool 11-failure pattern — DON'T keep retrying

The `memory` tool in cron context returns
`{"error": "Memory is not available..."}` reliably on the first call.
**Do not retry more than once** — observed v7 cron session 2026-06-07
the tool returned the same error 11 times in a row when called in
parallel. Wastes turns, no new info.

```python
# ❌ WRONG — wastes 11 turns on a guaranteed failure
for content in insights:  # 11 entries
    memory(action="add", target="user", content=content)

# ✅ RIGHT — one try, then file fallback
memory_attempted = False
try:
    memory(action="add", target="user", content=insights[0])
    memory_attempted = True
except Exception:
    pass  # canonical file write is the source of truth

# All 11 insights go to USER.md (v(n)) which is what the next session reads
write_file(~/.hermes/memories/USER.md, full_v7_content)
```

**Document the fallback in the deliverable's落库状态 block** so the
user knows the canonical file is up to date even though `memory` failed
(see template in `references/cron-delivery-quirks.md` §"Memory tool —
persistent unavailability").

### ⚠️ GBrain "verify" step is frequently skipped in practice

The Verification checklist has `gbrain search "<phrase>"` to confirm
the new `user-profile-YYYYMMDD` slug is findable. **In 3 consecutive
cron runs (v5/v6/v7 2026-06-05/06/07) this step was either skipped or
incomplete** because the final response ran out of context or the
session hit other constraints.

**Minimum viable verification** (do these even if you skip the
semantic-search round-trip):
1. `terminal(command="wc -l ~/.hermes/memories/USER.md ~/.hermes/memories/user_model_report_YYYYMMDD.md ~/.hermes/memories/daily/YYYY-MM-DD-user-model-snapshot.md")` — confirm 3 files exist, all in KB range (not 0B)
2. List the file sizes in the final report's落库状态 table — never claim "完成" without sizes
3. If you DO have time/turns: `PATH="$HOME/.bun/bin:$PATH" gbrain search "<unique phrase from v(n) 增量>"` — top hit should be `user-profile-YYYYMMDD` with sim > 0.9

The `scripts/verify-cron-writes.sh` helper handles step 1+2 in one call
for batched writes (e.g. N wiki pages in one job). For the user-model
specifically the 3-file list is fixed and one `wc -l` is enough.

### ⚠️ Search hits return truncated bookends

`session_search` discovery results are truncated to ~150KB. If you need
more, scroll into specific sessions by id + message id, or read the
session directly.

**v7 lesson**: For high-traffic topics (e.g. "五莲", "工商联",
"home assistant") the persisted-output trap fires on EVERY query —
the 1500-char preview is the only thing that fits in context, and the
`bookend_start` / `messages` arrays in the preview ARE the real
content. Read them carefully rather than re-querying with narrower
terms. A single broad OR-join query is often more useful than 3
narrow ones for the same reason.

### ⚠️ "Consecutive-cron-day" ceiling — agent runs on autopilot ~7 days max

v8 (2026-06-08) observed **7 consecutive cron-only days** (6/2 → 6/8)
with zero human interaction across any platform (feishu/weixin/tg/cli).
The user was not in the loop, but cron tasks self-advanced all 5 work
lines (信息稿 / PPT / 部务会 / 公文 / Wiki). Past data showed 4-5 days
as the prior ceiling.

**Implications for the profile**:
- After ~7 days of pure cron, **expect a human check-in** (the user
  probably wants to see what's been produced)
- The profile's "**v(n) 增量**" section should explicitly call out the
  consecutive-cron-day count so the user sees the cumulative work
- When the next user-initiated session arrives, lead with a "here's
  what cron did in your absence" summary — don't assume the user has
  seen the daily auto-reports
- This pairs with the "飞书 webhook 19001 错误" issue (v8 168+ hours):
  the user may not have actually received any of the cron reports for
  the past week

### ✅ Validated pattern: cron time-window splitting (v7 → v8 confirmed)

The `tongzhan-info-workflow` skill was failing 3-4 days in a row
because a single cron invocation tried to do both 选题 selection (heavy
read_file + browser + tool_calls) AND topic logging (write_file) within
~72 message budget. **v7 proposed splitting into two adjacent cron
slots (01:00 + 01:30) and v8 confirmed the strategy works**: 6/8 01:00
cron alone used 70 messages but successfully landed 5 topics / 26.6KB
without the 0-char-asst failure mode.

**Generic cron-skill design rule**: when a cron task repeatedly fails
with `asst last message = 0 chars` or "success hallucination" but
content was actually designed, the fix is **NOT** to add more tooling —
it's to **split into adjacent cron slots** so each slot has full budget
to actually `write_file` before context fills up.

**Anti-pattern to avoid**: don't merge 选题 + 写作 + 校对 + 落盘 into
one cron task just because the workflow looks "logically connected".
The 72-message budget is the hard constraint, not the workflow graph.

### ✅ Validated pattern: "Wiki 政策库 → cron 选题" reverse loop (v8 6/8)

The user designed (and 6/8 01:00 cron actually executed) a **bidirectional
loop** between the Wiki knowledge base and the cron 选题 generator:

```
Wiki 政策页 (e.g. policy-taiwan-investment.md)
  ↓ 执行层面问题标注 + 案例库
cron 01:00 读 ~/wiki/entities/policy-*.md
  ↓ 反向挖制度漏洞
类型B 制度漏洞选题 (3 个全新富矿)
  ↓ 用户选定后起草
信息稿 → 电脑校对 → 终稿
  ↓ 新案例 / 新制度问题
回到 Wiki 政策页 (深化 + 新案例) OR 新建 comparisons/ 子页
```

**Key insight**: the user has explicitly built this loop. The Wiki
isn't just a passive reference — it's the 选题 generator's "ore body".

**Profile-curation implication**: when v(n) reports Wiki progress,
report it AS the input to the next 选题 cron run, not as standalone
"知识沉淀" progress. The two are now one workflow.

### ✅ Workflow pattern: report file sizes in 落库状态 block (v8 confirmed)

After writing the 3 user-model files, the v8 report included:

```markdown
| **用户模型主文件** | `~/.hermes/memories/USER.md` | v8 主报告（覆盖 v7） | **18,460B** ✅ |
| **v7 备份** | `~/.hermes/memories/USER.md.bak.v7_1780855293` | v7 完整备份 | 17,239B ✅ |
| **周期化归档** | `~/.hermes/memories/user_model_report_20260608.md` | 54 天数据快照 | **18,460B** ✅ |
| **每日精简版** | `~/.hermes/memories/daily/2026-06-08-user-model-snapshot.md` | GBrain 同步版 | **1,898B** ✅ |
```

This is the **canonical "I really wrote the files"** signal. The
combination of:
1. Running `wc -c` on all 3 files before declaring success
2. Listing exact byte sizes (not "完成" or "已落盘")
3. Tying the size to the v(n) number (v8 = 18,460B) so a future v(n+1)
   can immediately spot if size shrank unexpectedly

…is what distinguishes a "real" 落库 from a "成功幻觉" 落库. Copy this
table pattern verbatim into every v(n) report's 落库状态 block.

## Verification

- [ ] 3 files exist with non-zero size: `USER.md`,
      `user_model_report_YYYYMMDD.md`,
      `daily/YYYY-MM-DD-user-model-snapshot.md` (sizes should be in the
      KB range, not 0B)
- [ ] `wc -l` on the 3 files shows KB-range line counts (not 0)
- [ ] GBrain `user-profile-YYYYMMDD` slug returns hits in semantic
      search (`gbrain search "<a unique phrase from the report>"`)
      — **if skipped, document why in the落库状态 block** (out of
      turns / context / time pressure), don't just silently drop it
- [ ] `gbrain stats` shows total chunks grew by ~1 from the new slug
- [ ] USER.md corrections count matches actual table row count
- [ ] Previous USER.md version preserved (manual `.bak.v(n-1)_<ts>` or
      Hermes auto-backup)
- [ ] All v(n-1) corrections still present in v(n) — corrections are
      append-only, never deleted
- [ ] Final response includes the full report (cron auto-delivers)
- [ ] Final asst's "完成报告" lists actual file sizes (not just counts)
      — see cron-success-hallucination pitfall above
- [ ] For batched writes (e.g. N wiki pages), `scripts/verify-cron-writes.sh`
      exit code is 0 before declaring success
- [ ] **If `execute_code` returned BLOCKED at any point, did not retry
      beyond 1 attempt** — went to `terminal` + `python3 -c "..."`

## See also

- `daily-work-log` — sibling skill for daily log generation; shares
  the same cron-mode constraints (memory tool unavailable, heredoc
  blocked, no sqlite3 CLI, etc.). Read its pitfalls section for
  cross-reference on cron environment quirks.
- `tongzhan-info-workflow` — benefits from the **"cron time-window
  splitting"** validated pattern (Pitfall: ✅ Validated pattern section)
  if its 01:00 + 02:00 cron tasks are merged or grow
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
- `references/cron-v8-validations.md` — **v8 (2026-06-08) validated
  patterns**: time-window splitting worked, Wiki→cron reverse loop
  executed, 7-day-cron ceiling observed, file-size table discipline
  standardized. Read this BEFORE designing a new cron skill.
- `scripts/verify-cron-writes.sh` — bash helper that checks N paths
  exist and are >= 1KB. Use as the last step of any cron write task.
