# Dream Cycle 2026-06-09

## Session Profile
- 7 cron sessions, 0 human conversations (8th consecutive all-cron day)
- 3 sessions with content: 00:00 daily-work-log (22), 01:00 tongzhan-info-workflow (16), 01:30 tongzhan-wiki-build (116)
- 4 sessions at 02:00:50 are 0-message guards/placeholders (same pattern as 6/2, 6/6, 6/8)

## Cron Sub-task Skills Identified
| Session | Skill | Outcome |
|---------|-------|---------|
| 00:00 daily-work-log | daily-work-log | ✅ 6/8 daily log written |
| 01:00 tongzhan-info-workflow | tongzhan-info-workflow | ❌ **FAILURE — 5th time** (6/5+6/6+6/7 fail, 6/8 success, 6/9 fail) — abnormally short session (16 msgs vs normal 72+) |
| 01:30 tongzhan-wiki-build | tongzhan-wiki-build | ✅ P01 案例深化 (P01 was the only "零案例" page in 5 priority pages) |

## ⚠️ New Failure Mode: 01:00 cron abnormally short session

**Old failure mode (6/5-6/7)**: 72+ messages, stuck in wiki 挖掘 + 新闻抓取, NFS file not written
**6/8 success**: simplified strategy worked (skip wiki mining, limit browser ops, prioritize NFS write)
**6/9 failure**: session **only 16 messages**, last assistant output was "Good. Now I have full context. Let me check today's experience topic..." (interrupted while reading experience topic history)

This is a **different** failure mode from 6/5-6/7. Hypotheses:
1. Cron 触发链路问题 (trigger chain / early-exit)
2. session message budget异常 low (config change?)
3. Pre-emption at the OS/cron level

**Action item for 6/10**: verify cron trigger is firing normally + check `~/.hermes/state.db` for the 01:00 session structure + consider if `daily-work-log` session is consuming the same message budget (00:00 already used 22 msgs of "yesterday's context", so 01:00 starts depleted?).

**No 6/9 NFS file**: `/mnt/nfs/2026年统战工作/8.信息工作/选题库/问题类选题_20260609.md` was NOT generated.

## Wiki→Brain Bridge (today)
| Wiki file | Operation | Brain slug | Size change |
|-----------|-----------|------------|-------------|
| `entities/policy-religion-regulations.md` | **NEW to brain** (wiki existed, but slug not yet imported) | `entities/policy-religion-regulations` | 5.9KB → 12.6KB wiki; +3 chunks brain |
| `entities/policy-guangcai.md` | content drift check | (no reimport) | wiki 295 lines ≈ brain 307 lines — ok |
| `entities/policy-taiwan-investment.md` | content drift check | (no reimport) | wiki 282 lines ≈ brain 292 lines — ok |

**Drift detection pattern**: `wc -l` on wiki file vs `gbrain get <slug>` byte count. If wiki > brain by >500 bytes → delete + reimport. Today: only `policy-religion-regulations` was missing, the other 2 were in sync.

## Project Page Update
`projects/tongzhan-info-topics` appended `## 2026-06-09 执行状态` with:
- 01:00 失败详情 (5th failure, abnormally short session)
- 01:30 成功详情 (P01 案例深化 113→218 行)
- "连续全 cron 日：第 8 日"
- Removed stale "关键突破" line from 6/8 (was misleading after 6/9 re-failure)

## New Person Page
- `people/li-ganjie/page` — 李干杰 (中央政治局委员、中央统战部部长, 2026-04 甘肃四川调研讲话)
- 出现场景: 2026-06-09 01:30 cron 案例 1
- 制度意义: 中央层级首次明确承认基层宗教执法"权小事多"问题
- 来源: `~/wiki/raw/religion-li-ganjie-gansu-sichuan-2026-04.md`

**Person page pattern**: 6/9 is the **2nd person page** (first was `song-jianhai` 5/19). Triggered by 01:30 cron citing 3 new real cases that name a high-level official not previously in brain.

## Staging Dir Sharing Pattern (confirmed working)

The wiki-bridge script `dream-cycle-wiki-bridge.sh` stages to `/tmp/gbrain-dream-YYYY-MM-DD/entities/<slug>/page.md`. Dream cycle can **add more files to the same dir** (people/, projects/, concepts/) and run `gbrain import <dir>` once at the end.

**Import output today**:
```
Found 3 markdown files
imported: 2 | skipped: 1 (1 unchanged) | errors: 0
3 chunks created
```
The "1 skipped" was `entities/policy-religion-regulations` which the bridge script had already imported 30 seconds earlier — correct behavior, not a bug.

**Validation before import** (avoid the YAML pitfalls):
```python
import yaml
content = open('/tmp/gbrain-dream-2026-06-09/people/li-ganjie/page.md').read()
fm = content.split('---', 2)[1]
yaml.safe_load(fm)  # raises if YAML malformed
```

## Brain Stats Delta
| Metric | 6/8 end | 6/9 end | Δ |
|--------|---------|---------|---|
| Pages | 110 | 113 | +3 |
| Chunks | 223 | 231 | +8 |
| Embedded | 223 | 231 | +8 (100%) |
| Tags | 114 | 121 | +7 |
| entity | 16 | 17 | +1 (policy-religion-regulations) |
| person | 4 | 5 | +1 (li-ganjie) |
| project | 17 | 17 | 0 (tongzhan-info-topics updated) |

## Doctor (06/09)
- health_score: 85 (consistent baseline 6/2-6/8)
- connection: 113 pages
- embeddings: 100% coverage, 0 missing
- resolver_health: warn (Could not find skills directory) — false positive
- pgvector/RLS: warn — false positive (PGLite doctor 已知 bug)

## Embed --stale
- 113/113 pages, 0 chunks embedded (100% coverage — Infinity 192.168.88.68:8081 unreachable from cron, expected env limit)

## ⚠️ `gbrain get` gotcha (re-discovered)

When verifying brain content size with `gbrain get <slug>`, the **first line is a YAML frontmatter** (`type: ...`) and the rest is markdown body. The `wc -l` of `get` output should reflect **both frontmatter and body lines**, not just the header.

**Wrong reading** (today's mistake): I saw "2 lines 109 bytes" from `wc -lc` and concluded the page was empty. Actually the full content was there — `get` returns the **whole page** plus the body. Always re-check with `head -30` or `wc` against the wiki source, not just the byte count.

**Better verification pattern**:
```bash
cd ~/gbrain && /home/lxgxdx/.bun/bin/bun run src/cli.ts get entities/<slug>/page 2>&1 | head -30
# Confirm the title and first content section are present
```

## Key Learnings for Next Dream Cycle

1. **01:00 cron has a NEW failure mode** (16-msg early exit, not the 72-msg exhaustion). 6/10 must verify trigger chain.
2. **Drift check pattern**: `wc -l` wiki vs `wc -lc` of `gbrain get` output. If drift > 500 bytes → delete + reimport.
3. **Staging dir sharing is safe**: bridge script + dream cycle can write to same `/tmp/gbrain-dream-YYYY-MM-DD/`, single `import` at end handles both.
4. **`gbrain get` always returns full content** — never trust byte count alone, always `head -30` to verify.
5. **Person page trigger**: a new 01:30 cron case citing a high-level official is the main signal to add a new `people/<name>/page` (only 2 person pages ever: song-jianhai 5/19, li-ganjie 6/9).
6. **policy-religion-regulations** was always a "in wiki" but "not in brain" state — wiki files are not auto-pushed. The bridge script catches this, but only runs with `--days N` so a longer-modified-but-missing page can slip through.
