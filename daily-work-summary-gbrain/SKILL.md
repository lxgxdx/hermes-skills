---
name: daily-work-summary-gbrain
description: Trigger when the user wants Hermes to automatically summarize its own daily work (tasks performed, files generated, key info) on a schedule, typically storing into a personal knowledge base like GBrain. Covers both the skill design conversation and the cron-job implementation.
---

# Daily Work Summary Skill

## When to use
User asks for: "daily summary", "每天总结工作", "总结当天干了啥", "自动复盘", or wants periodic self-reporting into GBrain / Notion / Obsidian / a knowledge base.

## Design conversation checklist (before building)
The user often wants to think through structure first. Surface these decisions:
1. **Target store**: GBrain? Notion? Obsidian? Local file?
2. **Time**: 22:00? 00:00 (previous day)? Morning?
3. **Granularity**: detailed log vs. executive summary
4. **Scope**: single platform (CLI) vs. all platforms (Feishu + WeChat + TG + CLI + cron)
5. **Format chunks**: what blocks matter most (tasks done / files generated / locations stored / decisions made)

## Recommended default structure (4 chunks)
1. **Tasks completed** — major actions taken
2. **Files generated** — paths to artifacts
3. **Key info / decisions** — non-obvious outcomes worth recalling
4. **Locations** — where things were stored (cron paths, skill paths, output paths)

## Implementation pattern (verified)
- **Cron at 0:00 daily**, summarizing the *previous* day (avoids incomplete-data problem of summarizing "today" before it ends)
- **Query `~/.hermes/state.db`** directly — covers ALL platforms in one query, no need for per-platform sync
- **Push to GBrain via**: `~/.bun/bin/bun run ~/gbrain/src/cli.ts put < <content>` (must use stdin — bunfs bug)
- **Tag convention**: `daily/YYYY-MM-DD` for queryability

## Common pitfalls
- ❌ Don't summarize "today" at midnight — it's incomplete; summarize yesterday
- ❌ Don't ask user for "what to include" without offering a default structure first
- ❌ Don't depend on per-platform sync scripts; state.db is the single source of truth
- ❌ Don't use Jira/Notion API without confirming — user often pivots (Jira → GBrain in the reference session)
- ✅ Always let user see the chunk structure BEFORE implementing, so they can adjust

## Verification
After cron fires once:
- `bun run ~/gbrain/src/cli.ts search "daily"` should return the entry
- Entry should have 4 sections matching the chunks
- Date tag should match "yesterday"