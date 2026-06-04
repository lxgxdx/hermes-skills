# v4 User Model Report Template

The canonical 8-section structure produced by the 2026-06-04 v4 run.
Use as the template for v5+ updates. Keep section ordering stable so
the file diff stays reviewable across versions.

## Header

```markdown
# 用户模型报告（v{n}）

**生成时间**：YYYY-MM-DD HH:MM AM（Cron 周期化任务）
**覆盖会话**：{N}+ 跨平台会话（飞书/微信/Telegram/CLI/Cron）
**数据周期**：{start_date} → {end_date}（{N} 天）
**本次相对 v{n-1}（YYYY-MM-DD）的新增**：
- ✅ {delta 1}
- ✅ {delta 2}
- ⚠️ {risk 1}
```

## Section 1: 基础画像 (Identity table)

Keep this table small and stable. Update values only when they change.

```markdown
| 项目 | 内容 |
|------|------|
| **用户名** | **lxgxdx**（"海参"是早年昵称，**用户已多次明确纠正不要再用**） |
| **真实身份** | **{org} {role}** |
| **通知渠道优先级** | **{ch1}（主）> {ch2}（日常）> {ch3}（备用/技术监控）** |
| **{ch1} open_id** | `{open_id}` |
| **作息** | **{pattern}** |
```

## Section 2: v(n) 增量 (Delta — most important)

This is the value-add. List every change since v(n-1) as a bullet.
- Use ✅ for completed work
- Use ⚠️ for unresolved risks
- Use 🔄 for in-progress transitions
- Quantify when possible ("+12 pages" or "5 个新选题")

## Section 3: 工作特征 (Work breakdown)

Organize by priority, not by chronology. Use 🔴/🟡/🟢 to mark urgency.
Each work line gets:
- A one-line summary
- A "key 说明" row explaining the workflow / deliverable / standards
- Sub-sections for major work products (information稿, PPT, etc.)

For the 信息稿 (information draft) sub-section, always include the
**docx 格式铁律** as a code table — this is referenced every time the
cron writes a new information稿.

## Section 4: 交互偏好 (Interaction preferences)

Two parallel lists:
- **喜欢 ✅** — direct, no fluff, real data
- **禁忌 ❌** — specific anti-patterns the user has called out

Then the corrections table. Each row:
- # (sequential, never renumber)
- "我犯的错" (the mistake)
- "用户纠正" (the correction)
- Optional: source session reference

## Section 5: 技术环境 (Tech environment)

Tables for:
- Hardware (Unraid / NAS / GPU)
- Services (with ports and purposes)
- Home Assistant / IoT devices
- AI model stack (with context window, key API params)
- Personal Wiki systems
- Backup paths

Always include the **GBrain CLI invocation** (`~/.bun/bin/bun run ...`)
because this is the most-failed step across sessions.

## Section 6: 生活习惯 & 兴趣 (Lifestyle)

Brief. Order by intensity (strongest interest first).

## Section 7: 关键路径速查 (Key paths)

Single code block. Easy to scan, copy-pasteable. Update whenever a
path changes.

```
TZB 工作目录：/mnt/nfs/2026年统战工作/
  ├─ 1.办公室/9.部务会/[日期]/     ← 会议记录
  ├─ 8.信息工作/选题库/            ← 每日 cron 生成
  ├─ 8.信息工作/范文/              ← 4 月份 8 篇范本（必读）
  └─ [数字编号]_[标题]/[版本].docx  ← 信息稿成品
```

## Section 8: 洞察 & 可主动帮助的点

Numbered list. Each point should be:
- Actionable (the agent can do this without asking)
- Specific (concrete enough to grep for in a future session)
- High-leverage (worth doing even if not asked)

## Section 9: 待用户决策

Numbered list. Each item should have:
- A short label
- A "为什么需要决策" (why it needs a decision)
- A "当前状态" if blocked

## Footer: 保存位置

Always include this 4-row table at the end so the user can find
where the report was written:

| 文件 | 路径 | 用途 |
|------|------|------|
| 用户模型主文件 | `~/.hermes/memories/USER.md` | v(n) 主报告 |
| 周期化归档 | `~/.hermes/memories/user_model_report_YYYYMMDD.md` | {N} 天数据快照 |
| 每日精简版 | `~/.hermes/memories/daily/YYYY-MM-DD-user-model-snapshot.md` | GBrain 同步版 |
| GBrain slug | `user-profile-YYYYMMDD` | {N} chunks embedded |

## Common mistakes to avoid in v(n+1)

- **Don't renumber corrections** — append new ones with new numbers
- **Don't drop old corrections** — even if they seem out of date,
  they're historically accurate and may still apply
- **Don't add unsubstantiated preferences** — every "喜欢" must trace
  to a session
- **Don't grow the file by more than ~20%** — if you need a major
  expansion, you're probably missing a v(n-1) section, not adding new
- **Don't write a generic "user model"** — the value is in the
  specific, dated, sourced entries
