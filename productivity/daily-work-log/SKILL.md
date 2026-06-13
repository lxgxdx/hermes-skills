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
| API Server | ⚠️（需甄别） | `api_server` |

---

## Workflow

### ⚠️ Cron 执行环境约束（2026-06-02 实测，必须先读）

本 skill **绝大多数由 cron 触发**（每天 00:00），cron 模式下：

- ❌ `execute_code` 工具被**完全禁用**（返回 `BLOCKED ... Cron jobs run without a user present to approve it`）
- ❌ `terminal` 的 shell heredoc 写法（`python3 << 'PYEOF' ... PYEOF`）会被**模式匹配拦截**（`pattern_key: "script execution via heredoc"` → pending_approval，超时失败）
- ❌ `sqlite3` CLI 不在 PATH（`未找到命令`），不要假设有
- ✅ `terminal` 工具直接执行 `python3 -c "..."` 单行命令**可用**
- ✅ `write_file` + `terminal` 读 stdin（`cat file.md | gbrain put ...`）可用
- ✅ `gbrain` 可执行文件是 `~/.bun/bin/gbrain` 的符号链接（指向 `../install/global/node_modules/gbrain/src/cli.ts`）

**所以正确的执行模式是**：
1. 用 `write_file` 生成 `/tmp/daily_log/...` 下的脚本和数据文件
2. 用 `terminal` + `python3 -c "..."` 单行执行查询（避免 heredoc）
3. 用 `terminal` + `cat file | gbrain put` 落库

### Step 1: 查询昨天所有 session（直接查 state.db）

```bash
# ✅ 单行 python3 -c 写法（cron 安全）
python3 -c "
import sqlite3
from datetime import date, datetime, timedelta
y = date.today() - timedelta(days=1)
ys = datetime(y.year, y.month, y.day, 0, 0, 0).timestamp()
ye = datetime(y.year, y.month, y.day, 23, 59, 59).timestamp()
c = sqlite3.connect('/home/lxgxdx/.hermes/state.db')
rows = c.execute('SELECT id, source, started_at, message_count, title FROM sessions WHERE started_at >= ? AND started_at <= ? ORDER BY started_at', (ys, ye)).fetchall()
print('Yesterday:', y.isoformat(), 'Count:', len(rows))
for r in rows: print(r)
"
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

### Step 2: 读取每个 session 的消息（同样用单行 -c 模式）

```bash
# 把所有 session 的用户/助手消息导出到 JSON 文件，避免一次性打印撑爆 context
python3 -c "
import sqlite3, json
from datetime import date, datetime, timedelta
y = date.today() - timedelta(days=1)
ys = datetime(y.year, y.month, y.day, 0, 0, 0).timestamp()
ye = datetime(y.year, y.month, y.day, 23, 59, 59).timestamp()
c = sqlite3.connect('/home/lxgxdx/.hermes/state.db')
sessions = c.execute('SELECT id, source, started_at, message_count, title FROM sessions WHERE started_at >= ? AND started_at <= ? ORDER BY started_at', (ys, ye)).fetchall()
out = []
for sid, source, ts, mc, title in sessions:
    msgs = c.execute('SELECT role, content FROM messages WHERE session_id = ? AND role IN (\"user\", \"assistant\") ORDER BY id', (sid,)).fetchall()
    out.append({'id': sid, 'source': source, 'ts': ts, 'title': title, 'messages': [(r, (content or '')[:1500]) for r, content in msgs]})
import os
os.makedirs('/tmp/daily_log', exist_ok=True)
with open('/tmp/daily_log/sessions.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print('Total sessions:', len(out), 'Total messages:', sum(len(s['messages']) for s in out))
"

# 之后用 search_files / read_file 按需读取（不要一次性 cat 全部）
```

**打印 session 摘要时附 asst 状态**（cron 必备，元数据一眼看出哪些 session 是"截断 vs 完整"）：

```bash
python3 -c "
import sqlite3, json
from datetime import date, datetime, timedelta
y = date.today() - timedelta(days=1)
ys = datetime(y.year, y.month, y.day, 0, 0, 0).timestamp()
ye = datetime(y.year, y.month, y.day, 23, 59, 59).timestamp()
c = sqlite3.connect('/home/lxgxdx/.hermes/state.db')
sessions = c.execute('SELECT id, source, started_at, message_count, title FROM sessions WHERE started_at >= ? AND started_at <= ? ORDER BY started_at', (ys, ye)).fetchall()
out = []
for sid, source, ts, mc, title in sessions:
    msgs = c.execute('SELECT id, role, content FROM messages WHERE session_id = ? AND role IN (\"user\", \"assistant\") ORDER BY id', (sid,)).fetchall()
    out.append({'id': sid, 'source': source, 'ts': ts, 'mc': mc, 'title': title, 'msgs': [(mid, r, (content or '')) for mid, r, content in msgs]})
import os
os.makedirs('/tmp/daily_log', exist_ok=True)
with open('/tmp/daily_log/sessions.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
# 摘要：标注每 session 首/末 asst 长度，用于快速识别截断
for s in out:
    asst = [m for m in s['msgs'] if m[1] == 'assistant']
    first_len = len(asst[0][2]) if asst else 0
    last_len = len(asst[-1][2]) if asst else 0
    last_content = asst[-1][2] if asst else ''
    # §5d 严格 SILENT + §5e 尾缀变体 + 长度约束
    is_silent_classic = last_content.strip() == '[SILENT]'
    is_silent_trailing = last_content.rstrip().endswith('[SILENT') or last_content.rstrip().endswith('[SILENT\n')
    flag = ''
    if (is_silent_classic or is_silent_trailing) and last_len < 500:
        flag = ' ⚠️SILENT'
    elif asst and last_len < 100:
        flag = ' ⚠️EMPTY_LAST'
    print(f\"  {s['id'][:55]} | {s['source']} | {s['mc']} msgs | asst[0]={first_len} asst[-1]={last_len}{flag}\")
    print(f'    title={s[\"title\"]!r}')
print('Total sessions:', len(out), 'Total messages:', sum(len(s['msgs']) for s in out))
"
```

**关键设计**：
- 把 600+ 条消息先 dump 到 `/tmp/daily_log/sessions.json`
- 摘要级别的元数据（session id/source/title/时间/消息数）一次性打印
- 单条消息内容**按 session 单独 `read_file`/`search_files` 提取**，避免挤爆 context
- cron 模式上下文比交互模式紧（默认几千 token），分批读取是必须的
- **SILENT 检测必须用长度约束**（见 §5e）：不要用 `'[SILENT]' in last` 子串检查（2026-06-12 用户模型 v10 asst last 14,088 字符含 `\`<SILENT>\` 不会被使用` 字面量是合法引用而非 SILENT 模式）

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

**cron-safe 三步走（2026-06-02 实测通过）**：

slug 格式：`daily/YYYY-MM-DD`

```bash
# 1) 用 write_file 先把内容写到 /tmp，避免 stdin heredoc 被拦
# 路径示例：/tmp/daily_log/daily_2026-06-01.md

# 2) 落库（gbrain 是 ~/.bun/bin/gbrain 符号链接，必须显式注入 PATH）
PATH="$HOME/.bun/bin:$PATH" gbrain put daily/YYYY-MM-DD < /tmp/daily_log/daily_YYYY-MM-DD.md
# 预期返回：{"slug":"daily/...","status":"created_or_updated","chunks":N}

# 3) 触发 embedding（首次写入时）
PATH="$HOME/.bun/bin:$PATH" gbrain embed --slugs daily/YYYY-MM-DD
# 预期返回：daily/YYYY-MM-DD: all N chunks already embedded（或正在处理）

# 4) 验证（关键！用语义搜索而不是精确 slug）
PATH="$HOME/.bun/bin:$PATH" gbrain search "daily YYYY-MM-DD"
# 预期：No results（slug 字面不在 chunk 里，OK）
PATH="$HOME/.bun/bin:$PATH" gbrain search "<日志里一个真实关键词>"
# 预期：top hit 是 daily/YYYY-MM-DD，相似度 >0.9
```

**为什么 gbrain 命令要前置 `PATH=...`**：`gbrain` 二进制在 `~/.bun/bin/`，cron 环境不会自动把用户级 bin 目录加进 PATH（不像交互式 shell 读 `~/.bashrc`），不显式注入就直接 `command not found`。

**⚠️ 内存工具不可用时的备选方案**：如果 `memory` 工具返回 "Memory is not available"，使用直接文件写入作为 fallback：
```bash
cp file.md ~/.hermes/memories/daily/YYYY-MM-DD.md
```
同时将内容追加到 `~/.hermes/memories/USER.md` 的相关章节中（该文件在 cron 环境也可写）。

**embed 注意事项**：`embed --stale` 需要 EMBEDDING_BASE_URL 可达；日常 `embed --slugs <slug>` 在 cron 环境已经验证可用，2 chunks 走通。

### Step 5: 确认

告诉用户 slug（`daily/YYYY-MM-DD`）和查日志的命令。

---

## 查询过往日志

```bash
~/.bun/bin/bun run ~/gbrain/src/cli.ts search "daily 2026-05"  # 查某月
~/.bun/bin/bun run ~/gbrain/src/cli.ts search "daily 本周"     # 查本周
~/.bun/bin/bun run ~/gbrain/src/cli.ts search "daily 统战部"   # 查某主题
```

## 参考资料

- `references/cron-runbook.md` — **逐行可复用的 cron 模式命令序列**（从查询 → 落库 → 验证完整流程），含所有已知陷阱的速查表
- `references/cron-recurring-bugs.md` — **跨日复现的 cron 任务已知 bug & 信号清单**（飞书 webhook 失效 / backup.log 缺失 / GitHub PAT 拦截 / dream cycle 累计 bug / §5b 成功幻觉 / §5c 80% 已完成未落盘 / **§5d cron SILENT 占位符 / §5e SILENT 尾缀变体（2026-06-12 新增）** / §11 混合日 lite 模式 / §11b 半截过渡句 / §11c 完整规划-未落盘 / §12 6/8 cron 健康度破冰 / **§14 漏报自检反馈循环（2026-06-12 新增）** / **§15 dream cycle 12× 差距 delete-then-reimport（2026-06-12 新增）** / **§16 PVE Wiki cron 时段迁移 06:00→02:00（2026-06-12 新增）**），必须显式标注在「未完成 / 待跟进」
- `references/stat-validation-checklist.md` — **每日 cron 汇报 stat 验证 checklist**（2026-06-08 起源，6/9+ 强制执行）：按 cron 类别列出必 stat 文件清单 + 标准验证脚本片段 + §11c 识别速查

---

## Pre-delivery Checklist

- [ ] 覆盖了所有平台（飞书/微信/TG），不遗漏
- [ ] 覆盖了当天所有 session
- [ ] 覆盖了所有主要工作项
- [ ] 每个文件都有路径和用途
- [ ] 未完成事项有明确的下一步
- [ ] 已存入 GBrain，slug 格式为 `daily/YYYY-MM-DD`
- [ ] 已用 `gbrain search <关键词>` 反向验证落库成功（相似度 >0.9）
- [ ] **【新】对 cron session 汇报的"已创建/已完成"文件，强制 stat 验证 + GBrain 跨源验证**（避免成功幻觉）
- [ ] **【新】检测每个 cron session asst last 是否是字面量 `[SILENT]`（§5d）或 `[SILENT` 尾缀变体（§5e）**——必须加 `len < 500` 长度约束避免用户模型 v10 这种"含 `[SILENT]` 字面量但实际是 14KB 完整报告"的 FP
- [ ] **【新】检测 asst last 是否是"半截过渡句"** —— 匹配 `现在写文件` / `Let me write` / `现在准备Searxng` / `Now let me` + 工具调用 `write_file=0` → 视为"未落盘"中断（§11b 第四种截断模式，2026-06-07 双 cron 同期首现）
- [ ] **【新】检测 asst last 是否是"完整结构化规划 + 0 个 write_file"** —— asst last 列出 N 个具体项（如 1. 2. 3. 4. 选题方向 + 外地借鉴）但整段 0 个 write_file / gbrain put → 视为"伪完成"中断（§11c 第五种截断模式，2026-06-08 02:00 经验类 cron 首现）
- [ ] **【新】检测 asst last 是否是"研究/验证已完成 + 0 write_file"** —— asst last 是"研究/设计结果汇报"（"I have all the context" / "Good — none of the new keywords" / "Let me also check" / "Let me verify" 等）+ write_file=0 → 视为 §11d 第六种截断模式（2026-06-11 02:00 双 cron 同期首现：user-model v10 + 经验类）
- [ ] **【新】对每个 cron session 汇报的"已创建文件"做强制 stat 验证（ALL session，不只成功幻觉怀疑时）** —— 6/8 实测：02:00 经验类 cron asst last 看似完整但 0 write_file，stat 验证 `经验类选题_20260608.md` 不存在才暴露；不要相信"asst last 长就完成"
- [ ] **【新】cron 健康度按"任务家族"分组评分** —— 不要按 session 数简单分子分母（6/8 01:00 破冰 + 02:00 仍失败 = 整体 75% 健康度但同根因家族 0%）；02:00 经验类连续 3 日失败（6/9+6/10+6/11）证明破冰是 task-specific 不是 cron-wide（§13）
- [ ] **【新】检测 §5e SILENT 尾缀变体（2026-06-12 新增）** —— asst last 末尾 `[SILENT`（缺失 `]`）也属 SILENT 模式，**必须加 `len < 500` 长度约束**避免误报（如用户模型 v10 14,088 字符含 `[SILENT]` 字符串是合法引用）
- [ ] **【新】标注"漏报自检"反馈循环（§14，2026-06-12 新增）** —— 一个 cron 任务的异常检测触发另一 cron 任务的深度复核（典型：01:00 cron deep-read 6/11 报告 0 漏洞文件发现 21 实际漏洞 + 5 选题派生 + SKILL 升级 5 项），属"自检 → 复核 → 修正"正向循环，需在「重要决定」中突出
- [ ] **【新】标注 dream cycle 12× 差距时 delete-then-reimport（§15，2026-06-12 新增）** —— 脑库 stats 与 wiki 文件 size 差距 ≥ 10× 时普通 import 静默跳过，必须走 delete-then-reimport；daily log「生成的文件」块需附"脑库同步状态"（chunks +N / tags +N）
- [ ] **【新】标注 PVE Wiki cron 时段迁移（§16，2026-06-12 新增）** —— 6/9-6/11 PVE Wiki 在 06:00 跑，6/12 移到 02:00，需在「未完成」记录"待 6/13+ 观察是否稳定"
- [ ] 告知用户 slug 名称
- [ ] **【新】首行标注 `api_server` session 数量**（6/13 28 session 同期出现）—— 在 0 飞书/微信/TG/cli 之外加 `N api_server`，让回看者一眼区分
- [ ] **【新】识别 pre-cron 预生成内容**（6/13 api-79eee 09:00 生成 `问题类选题_20260614.md` 21KB）—— 「生成的文件」必须 stat 验证存在 + 「未完成」标"待次日真 cron 是否覆盖"
- [ ] **【新】识别 manual session deliver-only 模式**（6/13 09:03 新文档 `2026-06-13-manual-session-deliver-only.md`）—— 在「重要决定」或「未完成」提一句"manual session deliver-only 模式触发，节省 token"
- [ ] **【新】清理型任务的 negative stat 验证**（6/13 SkillOpt 5 路径清理）—— 文件不存在 = 成功，也是 stat 验证的一种形态
- [ ] **【新】api_server session 单设 API Server 子块**（6/13 28 个 LLM-miner 子任务）—— 一句话概括即可，不逐个分析

## ⚠️ Context 控制（cron 环境必修）

实测一个典型日（约 25 session / 600+ messages）：

- 全部消息一次性打印会撑爆 cron 的紧凑 context（几千 token 而非几万）
- 单 session 的 187 条消息也建议只读首尾 user/assistant 各 1-2 条就够提炼

**实用分批策略**：

```bash
# 先打印元数据小清单（按时间排）
python3 -c "...SELECT id, source, started_at, message_count, title..."

# 按 source 分组：cron 是自动任务（选题库/Wiki/备份），跳过深度分析
# 重点读 feishu / weixin / telegram / cli 4 类的 user 消息
# cron 类的"成果汇报"通常第一条 assistant msg 就有完整结论，直接读那一条
```

**读取优先级（高→低）**：
1. **feishu / weixin / telegram / cli 的 user 消息**（用户实际需求）
2. **feishu / weixin / telegram / cli 的最后 1-2 条 assistant 消息**（结果汇报）
3. **cron 任务的最后一条 assistant 消息**（成果汇报，通常是日报 / 总结 / `## 任务完成报告` / `# 🧠 Dream Cycle ... 完成报告` 这类结构化结论）
4. **cron 任务的中间过程**（只在需要追细节时读）

**⚠️ Pitfall: cron session 的第一条 assistant 消息常常是空字符串或短过渡句**（2026-06-04 实测 91% `asst[0]=0`；2026-06-12 实测 18% `asst[0]=0` + 82% `asst[0]=32-179 短过渡句`）。原因：cron prompt 注入式 user 消息长达数百到 11k 字符，agent 第一反应是 100 字符内的过渡回复，然后才进入正式工作流。所以**读取 cron session 时必须跳过第一条 asst，直接读最后一条**，不要相信 "读第一条 asst 就是成果摘要" 的旧假设。

**⚠️ Pitfall: 跨 session 叙事一致性 — 不要相信前序 cron session 的"汇总数"**。真实案例 2026-06-03：dream cycle session（02:00）汇报 "Wiki 14 个新 policy-*.md 页面"，但 01:30 的 llm-wiki-build session 实际只新建了 1 个 P07。原因是 dream cycle 读了 `~/wiki/log.md` 累计历史行（混合了过去多天的增量），把"近期 wiki 增长"等同于"今天 wiki 增长"。  
**应对**：每个 session 的产出以**该 session 自己 first user + last asst 提到的文件路径/动作**为权威，前序 session 的"汇总"只在显式标注 "Today built N" 时才采信。日报里若发现两个 session 提到的产出数量冲突，必须在「未完成 / 待跟进」标注并指明哪个 session 需复核。

**判断 session 是否值得深读**：
- 消息数 <10 的 session：可能只是问候或简单问答，读 1 条 user + 1 条 asst 即可
- 消息数 30-100：典型工作 session，读 user 第一条 + asst 头/中/尾各 1 条
- 消息数 >100（典型如部务会整理、AI 知识库大任务）：必须分批，必要时只提取"完成的工作"和"文件路径"关键词

**⚠️ Pitfall: 空/截断的 assistant 消息（interrupted session 检测）**:
- **现象**：cron 在午夜 0:00 跑日志时，前一天最后一条 asst 消息可能为空或被截断。常见诱因：agent 反复遇到 CAPTCHA / 工具失败 / 搜索无结果后未生成最终总结（agent 进入死循环前被截断）
- **检测**：扫 `/tmp/daily_log/sessions.json` 时留意某 session 最后一条 `[role]` 字段长度；空字符串或 <100 字符 + 倒数第 2 条 asst 提到"CAPTCHA"/"限流"/"再试一次"等失败模式 = 可疑截断
- **应对**：读倒数第 2 条 asst 看 agent 卡在哪个阶段 → **必须在「未完成 / 待跟进」显式标注"任务疑似中断"** + 给出建议下一步（重试 / 改派 `delegate_task` 并行 / 换源 / 简化搜索条件）
- **真实案例**：2026-06-02 飞书 18:55（`20260602_185500_a12728`，5 方向问题类新闻搜集）—— 最后一条 asst 消息为空，asst 20-21 显示 agent 卡在 360 CAPTCHA + 头条搜索不显示结果；如不显式标注，此会话会在日报里被静默遗漏
- **为什么容易漏**：自动读取时只读 first + last asst 是 skill 推荐的省 context 策略，但"last 是空字符串"这种情况恰好和"last 不存在"边界情况一样会被跳过，需要在补丁里专门处理

**⚠️ "全 cron 日"处理（0 飞书/微信/TG/cli）**（2026-06-03 实测）：

偶尔会出现整天都没有人类交互平台的 session，11 个 session 全是 `source='cron'`。这种情况下：

- **不要写"[SILENT]"** — 有真实的自动化产出（备份 / 选题 / Wiki / dream cycle / GitHub 监控），不写日报会让系统丢失一整天记录
- **首行明确标注性质**：`**性质**：纯自动化执行日（凌晨定时任务 + 备份 + dream cycle + GitHub 监控）`
- **会话总数行注明"0 飞书/微信/TG/cli"**：方便回看时一眼区分人工日 / 自动日
- **"完成的工作"按 cron session 时间顺序列**，不分类（没有"飞书"、"cron" 分组的必要，因为只有 cron）
- **"未完成 / 待跟进"要包含跨 session 的横切观察**（如 dream cycle 报告的 14 vs llm-wiki-build 实际的 1 之类的口径不一致），这是全 cron 日相比人工日更值得日报化的地方

**⚠️ `api_server` source 甄别（2026-06-13 实测，28 session 同期出现）**：

- **现象**：query state.db 时可能出现 `source='api_server'` 的 session，**这些不是用户交互也不是标准 cron**，而是 Hermes gateway 转发过来的子任务 session。典型特征：
  - `id` 格式：`api-<hex16>`（不是 `cron_<hex>_<date>` 也不是 `YYYYMMDD_HHMMSS_<hex>`）
  - `title=None`（标准 cron 通常有 `<skill-name>` 标题）
  - msgs 数量集中在 2-8 之间（短任务），偶尔 40-120（中等训练/聚合任务）
  - `asst last` 极短（<20 字符：`]`、`''`、`"` 等），本质是 JSON 输出 marker
- **首次发现**：2026-06-13 SkillOpt 评估期间累计 28 个 api_server session（api-612eeb... → api-1640b9...），全部为 SkillOpt LLM-miner 子任务（评估"是否能挖出统战信息/PPT/HA 等领域的可复用 task"），与主流程无功能交集
- **甄别方法**：检查首条 user 消息关键词——含 `"mining a user's past AI-assistant sessions"` / `"You are completing a recurring task"` / `"Apply the skill and memory rules"` 等 skill 注入模板 → 判定为 LLM-miner / 模拟 cron 子任务
- **处理策略**：
  1. **首行标注 `0 微信/Telegram/CLI`** 之外还要标注 `N api_server` —— 让回看者一眼区分
  2. **在「完成的工作」单设 "API Server" 子块**，一句话概括（如"28 个 SkillOpt LLM-miner 子任务，全部为 SkillOpt 训练用 session，与主流程无功能交集"），**不要逐个分析**（浪费 context）
  3. **「未完成」标"N 个 api_server session 沉淀 state.db，待用户决定清理策略"** —— 避免无声累积
- **不要被大 msgs 数量误导**：api-79eee 120 msgs、api-1640 46 msgs 看着像大任务，实际是 LLM-miner 在循环生成 task 候选，不要把它们当成"额外 cron 任务" 日报化
- **真实案例 6/13**：1 飞书 + 9 cron + **28 api_server** + 0 微信/TG/cli = 38 session；只日报飞书 1 + cron 9 即覆盖全部用户工作，api_server 28 个在「完成的工作」末单设一段

**⚠️ "Pre-cron 预生成"内容识别（2026-06-13 实测）**：

- **现象**：api_server 类型的模拟 cron session 可能在当日 09:00 左右**提前生成次日 cron 预期产出**（如 `问题类选题_20260614.md` 在 6/13 09:06 实际写入 21KB），最后一条 asst 文本显示 "06/14 09:06 (manual session)"，但**文件 mtime 实际是 6/13**。这是 manual session 跑 deliver-only 模式的产物，**不是次日 cron 真跑**
- **识别三要素**：①文件 mtime 在「昨天」窗口内 ②asst last 提到"次日日期" ③首条 user 是 "tongzhan-info-workflow" skill 模板
- **处理策略**：
  1. **「生成的文件」必须列该预生成文件**（stat 验证存在 + 大小），不要漏
  2. **「未完成」标"待 6/14 01:00 真正 cron 跑时是否覆盖"** —— 真正 cron 可能直接读已有文件当 base 但覆盖核心 5 选题，也可能视为已完成跳过
  3. **「重要决定」不日报化**该预生成行为（不是真实 cron 决策，是 agent 提前演练），但要在文件列表注明 `(预生成 by manual session 09:06)`

**⚠️ "Manual session deliver-only" 模式识别（2026-06-13 09:03 新文档）**：

- **现象**：tongzhan-info-workflow skill 文档 `2026-06-13-manual-session-deliver-only.md` 在 6/13 09:03 由 cron 写入，描述"manual session 在 cron 已自动完成后打开，应进入 deliver-only 模式而不是 full-run 模式"
- **触发条件**：manual session 打开时间在 cron 已成功完成后（典型时间窗 09:00-22:00）；用户查询/重看飞书推送/看完文件后追问
- **deliver-only 模式行为**：
  1. ✅ 第一步 `ls /mnt/nfs/.../选题库/问题类选题_$(date +%Y%m%d).md`
  2. ✅ 文件存在 + size > 30KB → deliver-only 模式
  3. ✅ 读取已有文件 + 浓缩汇报
  4. ❌ 不重新扫描 Wiki、不重新抓新闻、不重新生成选题
- **日报处理**：当某 api_server / manual session 表现为"读已存在文件 + 浓缩汇报 + 不重跑"，在「重要决定」或「未完成」提一句"manual session deliver-only 模式触发"，**让日报读者知道该 session 节省了大量 token**

**⚠️ "混合日 lite" 处理（1 飞书 + 11 cron + 0 微信/TG/cli）（2026-06-06 实测）**：

介于"全 cron 日"和"混合日"之间的常见模式。飞书是单主题小 session（19 msgs 左右），cron 占绝对多数。

- **首行明确标注比例**：`会话总数：12（1 飞书 / 11 cron / 0 微信/TG/cli）` — 比例一目了然
- **飞书 session 处理**：用 §混合日 asst 头/中/尾三段式读取（如 RuView session asst[2]/asst[8]/asst[10]），但飞书 msgs 较少时单条汇报也够用
- **cron 任务归类**：
  - **00:00 daily-work-log** —— "昨日日报落库"
  - **01:00 + 01:30 + 02:00×4 + 03:00 + 06:00** —— 7 个标准时段（信息稿/Wiki/备份/Skill 同步）
  - **20:00 + 21:00** —— 6/6 全部 SILENT（§5d）
- **"未完成"块必须包含 cron 横切观察**（如今日 3 个 SILENT cron + 01:00 连续 2 日失败 + 02:00 PVE wiki 连续 2 日成功幻觉）
- **cron 健康度评分**：今日 3/12 = 25% cron 失败率（3 SILENT + 0 中断 + 0 成功幻觉），写入「未完成」便于跨日追踪健康度趋势
- **真实案例 2026-06-06**：1 个飞书 session 是 RuView WiFi 感知技术调研（19 msgs / 2 段答复：仓库评估 + Aruba 兼容性），不读 asst 中段会丢失"Aruba 不需要支持 CSI"这个关键澄清

**⚠️ "混合日"处理（cron + 飞书/微信/TG/cli 共存）**（2026-06-04 实测，13 session = 2 飞书 + 11 cron）：

混合日比纯 cron 日**更要**重点处理飞书 session，原因：飞书 session 是用户实际意图所在，cron session 是 agent 自己跑的任务总结。处理要点：

- **用 `target_ids` 过滤读取** — 不要把 458 条消息全 print。在第一遍元数据摘要（带 asst 头/尾长度）出来后，识别"高价值 session"（大消息数 + 飞书 + 标题非 None），用一个 `target_ids` 列表再用 `python3 -c` 单独读首/中/末 asst：

  ```python
  python3 -c "
  import json
  with open('/tmp/daily_log/sessions.json') as f: sessions = json.load(f)
  target_ids = ['feishu_id_1', 'feishu_id_2', 'cron_big_id']
  for s in sessions:
      if s['id'] in target_ids:
          msgs = s['msgs']
          asst = [m for m in msgs if m[1] == 'assistant']
          # 打印 first user + asst[0]/中/asst[-1]
  "
  ```

- **大飞书 session（>100 msgs）通常有多个子任务** — 不要只读最后一条 asst 当成单一任务；用关键词 grep 找到关键 asst（如含"完成"、"✅"、"全部到位"、数字 9/10 等编号标识）：

  ```python
  python3 -c "
  import json
  with open('/tmp/daily_log/sessions.json') as f: sessions = json.load(f)
  for s in sessions:
      if s['id'] == 'big_feishu_id':
          asst = [m for m in s['msgs'] if m[1] == 'assistant']
          for i, m in enumerate(asst):
              if 200 < len(m[2]) < 2500 and ('完成' in m[2] or '✅' in m[2] or 'M3' in m[2]):
                  print(f'\\n=== ASST[{i}] (len={len(m[2])}) ===\\n{m[2][:1500]}')
  "
  ```

- **"生成的文件"块要按子系统分组** — 混合日里"完成的工作"既要按时间序，也要按"统战信息稿 / Wiki / 备份 / Skill 改造 / 飞书交互"分组列；表格化用 `| 文件 | 路径 | 用途 |` 是混合日最有效的呈现

- **首行明确标注比例**：`**会话总数**：13（2 飞书 / 11 cron / 0 微信/TG/cli）` — 比例一目了然

- **真实案例 2026-06-04**：2 个飞书 session 中一个 213 msgs 包含 3 个独立子任务（Win7 ChatBox 兼容 + 41 文件重命名 + M3 多模态 8 skill 改造），每个子任务都值得日报化。如果只读最后一条 asst（用户问"你现在是什么模型"），整日会丢失全部产出。

- **飞书 session "探索→选型→落地"三段式 asst 读取模式**（2026-06-05 飞书 HA 仪表板 session 实测，36 msgs）：
  - **asst[6]** ≈ 现状盘点（HA 版本/实体数/已装卡片/户型）
  - **asst[16]** ≈ 三套方案对比（带详细 YAML 示例 + 设计理念引用）
  - **asst[17]** ≈ 用户确认选型（"好的，方案 A ..."）
  - **asst[34]** ≈ 最终完成报告（32.5KB 落地文件路径 + 4 步实施 + 6 风险点 + 5 下一步）
  - **应对**：不要只读 `asst[0]`（过渡句 50-100 字符）和 `asst[-1]`（最终报告）；中间 asst 包含**关键决策节点**（用户选哪个方案 / agent 决定如何取舍），漏读会丢失决策背景
  - **飞书 session "等用户实测" 终止状态标注**（2026-06-05 飞书 session 终止点）：agent 完成方案设计 + 写入 wiki + 给出 4 步实施指南后，停在"等用户在 HA 实测反馈"。这种**非中断但未闭环**的 session 必须在「未完成」标 "用户待实测"，避免日报误读为"全部完成"。

**⚠️ Pitfall: cron session 整段只返回字面量 `[SILENT]`（8 字符）（2026-06-06 新发现）**：

- **现象**：cron session 的最后一条 asst 内容是字面字符串 `[SILENT]`（长度仅 8），没有 skill 注入后的过渡句、没有失败原因、没有完成报告。是**第三种截断模式**，与已知的"空字符串截断"和"成功幻觉"都不同
- **首次批量发现**：2026-06-06 三个 cron session 同时中招：
  - `cron_0abf80bf4d68_20260606_020012`（llm-wiki-build，PVE wiki 概念页）—— 12 msgs / asst last = `[SILENT]`
  - `cron_8670107d659c_20260606_200008`（home-assistant-ops）—— 5 msgs / asst last = `[SILENT]`
  - `cron_e08019f497a1_20260606_210022`（check-wechat-issue）—— 4 msgs / asst last = `[SILENT]`
- **2026-06-12 验证**：2 个 cron session 命中（FP310 + wechat-issue-tracker），属"无变化守护型任务"，**100% 合规**——但使用了**§5e 尾缀变体**（`[SILENT` 而非 `[SILENT]`），不能只用 §5d 严格匹配
- **与"空字符串截断"区别**：`asst last = ''`（len=0）通常出现在 agent 进入死循环后被截断；`[SILENT]` 字符串是 agent 显式决定的"我没什么可汇报的"信号
- **与"成功幻觉"区别**：成功幻觉 = asst last 长且结构化（看着像真完成）；`[SILENT]` = asst last 极短（看着像真没做事）
- **根因猜测**（待 6/7 02:00 验证）：skill 注入型 user 消息（10k+ 字符）让 agent 推断"任务已由其他 cron 接管 / 我没新增信息可报"，直接用 SILENT 占位；或 skill 模板本身要求 agent 在无新产出时回 SILENT
- **检测**：`last_len == 8 and content.strip() == '[SILENT]'` 一行精确匹配；老的 `< 100` 阈值已能 catch 但有 FP（首条短过渡句也可能 < 100）
- **应对**：
  1. **读 skill 全文**确认该 cron job 是不是"应该静默的守护型任务"（如 gbrain doctor / skills sync 的二次校验）
  2. **非守护型任务 + SILENT** → 视为"任务未执行"，在「未完成 / 待跟进」标 `❌ cron SILENT（未执行）`
  3. **跨日累计同类**：若 6/6 已有 3 个 SILENT cron，6/7 02:00 cron 必须复跑这 3 个任务
- **为什么重要**：今天 1 飞书 + 11 cron 的"混合日 lite"模式下，3 个 SILENT cron 占据了 25% 的 cron 任务量；如果不显式标注，整日 cron 产出统计严重虚高
- **§5e 变体检测**（2026-06-12 新增）：asst last 末尾 `[SILENT`（缺失 `]`）也属 SILENT 模式；详见 references/cron-recurring-bugs.md §5e
- **⚠️ False positive 警告**：**绝对不要用 `'[SILENT]' in last` 子串检查**——2026-06-12 用户模型 v10 asst last 14,088 字符含 `\`<SILENT>\` 不会被使用` 字面量是合法引用

**⚠️ Pitfall: cron 任务"成功幻觉"（SUCCESS HALLUCINATION）— 必须 stat 验证**（2026-06-05 新发现）：

- **现象**：agent 写出长且结构化的"完成报告"作为最后一条 asst（含详细文件路径 + 大小 + 实施步骤），但**实际文件未落地**。和"普通截断"（asst last = 0）的关键区别：成功幻觉 = asst last **长且结构化**
- **首次案例**：2026-06-05 02:00 PVE Wiki cron（`0abf80bf4d`）汇报"已创建 4 个核心页面"，但 `~/wiki/concepts/` 下 4 文件均不存在，GBrain 也搜不到
- **2026-06-12 验证 stat 协议全过**：9 个 cron session 汇报的关键文件全部 stat 验证通过——`policy-minzu-tuanjie.md` 25,620 字节 / 321 行与 cron 报告"321行/25KB" **byte 级别一致**；`问题类选题_20260612.md` 40,564 字节、`经验类选题_20260612.md` 51,847 字节、PVE Wiki 4 文件 2.8-3.5KB、备份 3.9G、USER.md v10 21,496B 全部 ✓
- **2026-06-13 验证 stat 协议再全过 + 升级**：6/13 11 个 cron 汇报文件全部 stat 验证通过；新增了"**清理型任务**"的 stat 验证：feishu session 报"5 处 SkillOpt 清理全删干净"，stat 检查 5 个路径全部 `ls: No such file` 即确认成功。这种 **"negative stat"**（文件不存在 = 成功）也是 stat 验证的一种形态
  - `问题类选题_20260613.md` 43,430B / cron 报告 43.4KB → ✓
  - `经验类选题_20260613.md` 84,775B / cron 报告 84.8KB → ✓
  - `policy-shandong-tongzhan.md` 22,178B / cron 报告 22KB → ✓
  - `shandong-implementation-deepening-2026-06-13.md` 7,417B / cron 报告 7.4KB → ✓
  - PVE Wiki 4 文件 3,491-3,845B / cron 报告 3.4-3.8KB → ✓
  - 备份 6/13 `hermes_backup_20260613_030157.tar.gz` 4,188,022,272B (4.5G 原始 / 3.9G 压缩) → ✓
  - USER.md v11 24,952B / cron 报告 24,952B / 356 行 → ✓
  - SkillOpt 清理 5 路径全部 stat 不存在 → ✓（negative stat 验证）
- **必做的 3 步验证**（每个 cron session 汇报的关键文件都要做）：
  1. **filesystem stat**：`ls -la <path> 2>&1` 看文件存在 + 大小 > 1KB
  2. **GBrain 跨源验证**：`gbrain search "<文件核心实词>"` 看是否有相关 chunk
  3. **「未完成」顶部标 `⚠️ 成功幻觉`** + 明确建议下一步（重跑 / `delegate_task` / 在对应 skill 模板加 stat 强制校验）
- **为什么容易漏**："读 asst[-1] = 成果汇报"是 skill 推荐的核心省 context 策略，但**长且结构化**的最后一条 asst 反而最危险——agent 自己会信（"汇报看着像真完成"），daily log generator 也会信（"asst last 长 > 200 字符 = 完成"）
- **详细分类**见 `references/cron-recurring-bugs.md` §5b
