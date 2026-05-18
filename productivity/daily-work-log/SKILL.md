---
name: daily-work-log
description: >
  每日工作日志生成与存储。直接查询 Hermes state.db 汇总前一天所有平台（飞书/微信/TG/cli/cron）
  所有 session 的对话内容，提炼为4块结构化日报存回 GBrain。触发词：今日工作/工作日报/总结今天/存日报/今天干了什么。
tags: [daily, log, work, gbrain, summary]
category: productivity
---

# 每日工作日志生成器

This skill positions the Agent as a senior executive assistant who maintains a
structured daily work log — tracking completed tasks, generated files, key decisions,
and important context — so nothing is ever lost and future self can search across time.

Core philosophy: **Every day is a project page. Consistency is memory.**

---

## Scope

✅ **Applicable**:
- End-of-day summary of completed work
- Storing generated file paths and their purpose
- Recording key decisions made during the day
- Logging important context (why something was done a certain way)
- Capturing unresolved items or follow-ups for next day

❌ **Not applicable**:
- Real-time task tracking during the day
- Personal journal or non-work notes
- Project management (Linear/Jira are better for that)

---

## 数据源（覆盖范围）

**直接查询** `~/.hermes/state.db`（SQLite），不依赖 GBrain 同步脚本。

**Cron 执行时间**：每天午夜 0:00，此时 date 参数为"新的一天"，需要用 `yesterday`（date - 1天）作为查询目标日期。

| 平台 | 覆盖 | session.source 值 |
|------|------|-------------------|
| 飞书 | ✅ | `feishu` |
| 微信 | ✅ | `weixin` |
| Telegram | ✅ | `telegram` |
| CLI | ✅ | `cli` |
| Cron | ✅（自动任务） | `cron` |

---

## Workflow

### Step 1: 查询昨天所有 session（直接查 state.db）

```python
import sqlite3
from datetime import date, datetime, timedelta

yesterday = date.today() - timedelta(days=1)
yesterday_start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
yesterday_ts_start = yesterday_start.timestamp()
yesterday_ts_end = yesterday_end.timestamp()

db = sqlite3.connect('/home/lxgxdx/.hermes/state.db')
c = db.cursor()

# sessions 表的时间列是 started_at（Unix epoch），不是 timestamp 或 created_at
sessions = c.execute("""
    SELECT id, source, started_at, message_count, title
    FROM sessions
    WHERE started_at >= ? AND started_at <= ?
    ORDER BY started_at
""", (yesterday_ts_start, yesterday_ts_end)).fetchall()
```

**⚠️ Pitfall 1**: `sessions` 表的时间列是 `started_at`（Unix epoch），不是 `timestamp`、`created_at` 或 `ended_at`。

**⚠️ Pitfall 2 (2026-05-19 实测 bug)**: `datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)` 正确，但 `date.replace()` 错误示范如下：

```python
# ❌ 错误：date.replace() 不接受 hour/minute/second/microsecond 参数
yesterday_ts_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
# TypeError: replace() takes at most 3 keyword arguments (4 given)

# ✅ 正确：用 datetime() 构造函数
from datetime import datetime
yesterday_start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
yesterday_ts_start = yesterday_start.timestamp()
```

这个 bug 会导致 cron 任务在 `gbrain put` 之前就报 TypeError 并中断，整个日志生成失败。

### Step 2: 读取每个 session 的消息

```python
for sid, source, ts in sessions:
    msgs = c.execute("""
        SELECT role, content FROM messages
        WHERE session_id = ?
        ORDER BY timestamp
    """, (sid,)).fetchall()
    # 拼接角色和内容用于提炼
```

### Step 3: 提炼并格式化

从所有对话中提取：
- 完成的工作（任务、修复、创建的内容）
- 生成的文件（路径+用途）
- 重要决定及其原因
- 未完成/待跟进的事项

**格式（4块结构，永远不变）：**

```markdown
# 每日工作日志 — {date}

## 完成的工作
- [任务] → [结果]

## 生成的文件
| 文件 | 路径 | 用途 |
|------|------|------|

## 重要决定
- [决定] — 原因：[为什么这样选]

## 未完成 / 待跟进
- [事项] — 状态：[卡在哪里/下一步]
```

### Step 4: 存入 GBrain

⚠️ **必须用 bun 方式**，compiled binary 的 PGLite write 有 bunfs bug（`/$bunfs/root/pglite.data` ENOENT，2026-05-19 回归）。

slug 格式：`daily/{date}`

```bash
cd ~/gbrain && /home/lxgxdx/.bun/bin/bun run src/cli.ts put daily/{date} --content '...'
cd ~/gbrain && /home/lxgxdx/.bun/bin/bun run src/cli.ts embed --slugs daily/{date}
```

**⚠️ GBrain 远程 PostgreSQL 不可用时的降级处理**：如果 `put` 报错 `database "gbrain" does not exist`（远程 Postgres 的 gbrain 数据库不存在）或 `relation "pages" does not exist`（数据库存在但 schema 未初始化），需要先初始化本地 PGLite：

```bash
# 初始化本地 PGLite（降级方案，不依赖远程 Postgres）
cd ~/gbrain && /home/lxgxdx/.bun/bin/bun run src/cli.ts init --engine pglite

# 然后重试 put（仍用 bun 方式）
cd ~/gbrain && /home/lxgxdx/.bun/bin/bun run src/cli.ts put daily/{date} --content '...'
cd ~/gbrain && /home/lxgxdx/.bun/bin/bun run src/cli.ts embed --slugs daily/{date}
```

### Step 5: 确认

告诉用户 slug（`daily/YYYY-MM-DD`）和查日志的命令。

---

## 查询过往日志

```bash
~/.bun/bin/bun run ~/gbrain/src/cli.ts search "daily 2026-05"  # 查某月
~/.bun/bin/bun run ~/gbrain/src/cli.ts search "daily 本周"     # 查本周
~/.bun/bin/bun run ~/gbrain/src/cli.ts search "daily 统战部"   # 查某主题
```

---

## Pre-delivery Checklist

- [ ] 覆盖了所有平台（飞书/微信/TG），不遗漏
- [ ] 覆盖了当天所有 session
- [ ] 覆盖了所有主要工作项
- [ ] 每个文件都有路径和用途
- [ ] 未完成事项有明确的下一步
- [ ] 已存入 GBrain，slug 格式为 `daily/YYYY-MM-DD`
- [ ] 告知用户 slug 名称
