---
name: hermes-to-gbrain-sync
description: 把 Hermes 的微信/Telegram 对话自动同步到 GBrain 个人知识库。触发：同步对话/brain/GBrain/对话记录存入脑库。脚本位置：~/scripts/sync-conversations-to-brain.py
---

# hermes-to-gbrain-sync — Hermes → GBrain 对话同步

把 Hermes 的微信/Telegram 对话自动同步到 GBrain 个人知识库，实现长期记忆和语义搜索。

## 核心架构

```
Hermes state.db (sessions + messages 表)
        ↓
Python 同步脚本 (读取 → 格式化 → stdin 写入 GBrain)
        ↓
GBrain (向量化存储到 PGLite)
        ↓
可语义搜索 / 关键词搜索
```

---

## 依赖声明

**必需命令：** `python3`, `bun`
**必需Python库：** `sqlite3`（内置）, `subprocess`（内置）, `pathlib`（内置）
**环境变量：** `SILICONFLOW_API_KEY`（硅基流动API key，用于embedding）
**运行方式：** 直接运行脚本，或通过 cron 自动触发

---

## 关键路径

| 路径 | 说明 |
|------|------|
| `~/.hermes/state.db` | Hermes 会话数据库 |
| `~/brain/` | GBrain 页面存储目录 |
| `~/.gbrain/brain.pglite` | GBrain 向量数据库 |
| `~/scripts/sync-conversations-to-brain.py` | 同步脚本 |

---

## 踩坑记录（必读）

### GBrain put 必须用 stdin，不能直接写文件
### GBrain put 两种方式对比

**方式A（CLI，快但可能超时）**：stdin 传入内容 + `--content` flag：
```python
result = subprocess.run(
    [GBRAIN_BIN, 'run', GBRAIN_SCRIPT, 'put', slug, '--content'],
    input=content,
    capture_output=True, text=True
)
```
注意：不用 `--content` flag 会报错 `Unknown command: put`。

**方式B（文件系统，绕过 embedding 超时）**：直接写 brain 目录：
```python
page_path = Path('/home/lxgxdx/brain') / (slug.replace('/', os.sep) + '.md')
page_path.parent.mkdir(parents=True, exist_ok=True)
page_path.write_text(content, encoding='utf-8')
```
⚠️ `gbrain put` 在内容多时 embedding 会超时（60s 仍不够），**推荐用方式B**直接写文件。

### Python pathlib 操作符优先级陷阱

```python
# 报错！
BRAIN_DIR / slug.replace('/', os.sep) + '.md'

# 正确（括号优先）
BRAIN_DIR / (slug.replace('/', os.sep) + '.md')
```

### GBrain CLI 必须用 bun run

compiled binary 有 bunfs bug，直接运行会报 `ENOENT: no such file or directory, open '/$bunfs/root/pglite.data'`  \
正确命令：
```bash
/home/lxgxdx/.bun/bin/bun run /home/lxgxdx/gbrain/src/cli.ts <command>
```

注意：`/home/lxgxdx/gbrain/bin/gbrain` 是编译后的 binary，但有路径 bug；`bun run` 读取 `~/.gbrain/config.json` 正常，binary 不读取配置。

### gbrain query 中文搜索质量不稳定

- 日期查询（如 `2026-04-17`）稳定有效
- 自然语言查询（如 `项目 任务 待办`）可能返回空结果，即使内容存在
- 对话内容搜索建议用 `gbrain list` 配合人眼判断，或用 `search` 关键词搜索
- `gbrain doctor --fast` 是最可靠快速的命令（5s 内完成）

---

## 同步工作流（4步）

### 步骤1：查询当天会话

**输入：** Hermes state.db
**输出：** 当天所有 weixin/telegram 会话列表

```python
import sqlite3
from datetime import datetime as dt

db_path = '/home/lxgxdx/.hermes/state.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

today_start = dt.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
cur.execute("""
    SELECT id, source, user_id, started_at 
    FROM sessions 
    WHERE started_at >= ? AND source IN ('weixin', 'telegram')
    ORDER BY started_at ASC
""", (today_start,))
sessions = cur.fetchall()
conn.close()
```

### 步骤2：加载每个会话的消息

```python
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("""
    SELECT role, content, timestamp 
    FROM messages 
    WHERE session_id = ? AND role IN ('user', 'assistant')
    ORDER BY timestamp ASC
""", (session_id,))
messages = cur.fetchall()
conn.close()
```

### 步骤3：格式化为 markdown 并通过 stdin 写入 GBrain

```python
content = f"""---
type: conversation
title: "{first_msg}"
platform: {source_label}
date: {date_str}
tags:
  - daily-log
  - {source}
---

## 对话摘要

{first_msg}

## 完整记录

{full_text}

## 元数据

- 平台：{source_label}
- 用户ID：{user_id or '未知'}
- 会话ID：{session_id}
"""

# 通过 stdin 写入 GBrain（不能用文件写入！）
rc, stdout, stderr = gbrain_run(['put', slug], input_text=content)
```

### 步骤4：触发 embedding

`gbrain put` 会在写入时自动触发 embedding（如果用了 stdin），否则手动执行：
```bash
/home/lxgxdx/.bun/bin/bun run /home/lxgxdx/gbrain/src/cli.ts embed <slug>
```

---

## Brain 页面格式规范

```markdown
---
type: conversation
title: "对话摘要（首个用户消息的前80字）"
platform: 微信/Telegram
date: 2026-04-17
tags:
  - daily-log
  - weixin
---

## 对话摘要

[首个用户消息]

## 完整记录

[HH:MM] 用户/助手：消息内容（一行一条）

## 元数据

- 平台：微信/Telegram
- 用户ID：xxx 或 未知
- 会话ID：session_id
```

---

## 搜索命令

```bash
# 关键词搜索（tsvector，稳定）
/home/lxgxdx/.bun/bin/bun run /home/lxgxdx/gbrain/src/cli.ts search <关键词>

# 语义搜索（向量，中文兼容性待优化）
/home/lxgxdx/.bun/bin/bun run /home/lxgxdx/gbrain/src/cli.ts query <自然语言问题>

# 列出所有页面
/home/lxgxdx/.bun/bin/bun run /home/lxgxdx/gbrain/src/cli.ts list

# 查看 brain 统计
/home/lxgxdx/.bun/bin/bun run /home/lxgxdx/gbrain/src/cli.ts stats
```

---

## 自动同步 cron

- **hourly-conversation-sync**：`0 * * * *`（每小时同步一次当天对话）
- **nightly-dream-cycle**：`0 2 * * *`（每天2AM维护 brain 健康）

---

## 验证步骤

```bash
# 1. 检查 brain 统计
/home/lxgxdx/.bun/bin/bun run /home/lxgxdx/gbrain/src/cli.ts stats

# 2. 检查对话页面数量
/home/lxgxdx/.bun/bin/bun run /home/lxgxdx/gbrain/src/cli.ts list | grep conversation

# 3. 测试搜索
/home/lxgxdx/.bun/bin/bun run /home/lxgxdx/gbrain/src/cli.ts search 关键词

# 4. 手动运行同步脚本（调试用）
python3 ~/scripts/sync-conversations-to-brain.py
```

---

## 异常处理索引

| 情况 | 解决方法 |
|------|---------|
| `gbrain put` 后 0 chunks | 改用 stdin 传入内容，不要直接写文件 |
| embedding 失败 | 检查 SILICONFLOW_API_KEY 是否有效 |
| 搜索返回空但内容存在 | 可能是 embedding 失败，手动运行 `gbrain embed <slug>` |
| bun binary 报 bunfs bug | 用 `bun run src/cli.ts` 而不是直接运行编译后的 binary |
| 同步脚本路径错误 | pathlib 操作符陷阱：`(slug.replace(...) + ".md")` 加括号 |
