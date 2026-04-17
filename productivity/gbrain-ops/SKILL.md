---
name: gbrain-ops
description: GBrain 个人知识库操作手册。涵盖 gbrain put 必须通过 stdin、bunfs bug、Python pathlib 优先级陷阱、同步 Hermes 对话脚本。触发词：gbrain/知识库/brain/同步对话/embedding/向量搜索
---

# GBrain Operations Guide

## 基本命令（2026-04-17）

所有命令使用：`bun run ~/gbrain/src/cli.ts <cmd>`

**推荐使用** compiled binary `/home/lxgxdx/gbrain/bin/gbrain` — 在 cron/root 环境下正常运行。`bun run src/cli.ts` 在 cron 环境中可能有路径问题。

### 正确环境变量
```bash
HOME=/home/lxgxdx
SILICONFLOW_API_KEY=sk-kum...jmew  # SiliconFlow embedding key
PATH="/home/lxgxdx/.bun/bin:$PATH"
```

### 正确命令
```bash
/home/lxgxdx/gbrain/bin/gbrain doctor --fast
/home/lxgxdx/gbrain/bin/gbrain put <slug> --content '...'   # 推荐 --content flag
```
## gbrain put — 关键：必须通过 stdin

`gbrain put` 要求内容通过 stdin 传入。直接写文件到 brain 目录不会创建 embeddings（0 chunks）。

### 错误做法
```python
# 直接写文件到 brain 目录 —— 错误！0 chunks embedded
page_path = BRAIN_DIR / (slug.replace('/', os.sep) + '.md')
page_path.write_text(content)
```

### 正确做法
```python
r = subprocess.run(
    ['bun', 'run', '/home/lxgxdx/gbrain/src/cli.ts', 'put', slug],
    input=content,  # str，不是 bytes
    capture_output=True, text=True, timeout=30,
    cwd='/home/lxgxdx/gbrain', env=env
)
```

Shell 管道方式：
```bash
cat /tmp/content.md | bun run ~/gbrain/src/cli.ts put slug
```

---

## Python pathlib 操作符优先级陷阱

`BRAIN_DIR / slug.replace('/', os.sep) + ".md"` 报错。

**必须加括号：**
```python
BRAIN_DIR / (slug.replace('/', os.sep) + '.md')
```

---

## search vs query

- `gbrain search <keyword>` — tsvector 关键词搜索（快、可靠）
- `gbrain query <自然语言>` — 向量语义搜索（依赖 embedding，有兼容性问题）

### put 也做 embedding！

`gbrain put <slug>` 会自动对内容做 embedding（写入向量数据库）。如果 embedding 失败（401 或维度不匹配），内容仍会写入数据库，但向量为空。

维度不匹配症状：`expected 1536 dimensions, not 1024` — SiliconFlow 使用了 text-embedding-3-small (1024维) 而非 GBrain 期望的 text-embedding-3-large (1536维)。

**当前环境**: `SILICONFLOW_API_KEY` 配置了 SiliconFlow，可用于 embedding，但模型可能不匹配。

解决方案：
1. 检查 SiliconFlow API 端点的模型配置，确保使用 `text-embedding-3-large`
2. 或用 `embed <slug>` 命令事后手动触发 embedding

---

## 同步 Hermes 对话脚本

脚本位置：`~/scripts/sync-conversations-to-brain.py`

幂等设计，重复运行安全。

**关键实现注意点：**
- stdin 传 `input=content`（str），不是 `input=content.encode()`（bytes 会报错）
- 先删旧 slug（gbrain delete）再重新 put，确保 embeddings 正确
- slug 格式：`conversations/YYYY-MM-DD-source-sessionid`

---

## 架构：文件系统 ≠ 向量数据库

**这是最重要的理解：GBrain 有两套存储系统，且完全不同步。**

- **向量数据库** `~/.gbrain/brain.pglite` — `list/get/search/query` 操作的对象，embedding 存在这里
- **文件系统** `~/brain/` — git 仓库备份，仅用于版本控制和手动备份；直接写文件到这里**不会创建任何 embedding**

`gbrain put slug` 只写入向量数据库，不会生成 ~/brain/slug.md 文件。
`gbrain list` 显示的是向量数据库内容，和 ~/brain/ 目录内容可能完全不同。

如需导出数据库内容到文件系统，需要手动处理（目前没有 `gbrain sync` 命令）。

---

## PGLite 数据库路径

`~/.gbrain/config.json` 配置了 `database_path: /home/lxgxdx/.gbrain/brain.pglite`

### PGLite 锁文件问题
`brain.pglite/` 目录下可能存在 `.gbrain-lock/` 子目录，表示有未释放的锁。如果 `gbrain put` 命令超时且 `doctor` 显示 "No database configured"，可能是锁未释放。

解决方法：检查并清理 `.gbrain-lock/` 目录（确保没有其他 gbrain 进程在运行）

### doctor 显示 "No database configured" 但配置文件存在
原因：compiled binary 运行时 HOME 环境变量可能不是 `/home/lxgxdx`，导致找不到 `~/.gbrain/config.json`。
解决：`HOME=/home/lxgxdx /home/lxgxdx/gbrain/bin/gbrain doctor --fast`

```bash
bun run ~/gbrain/src/cli.ts doctor --fast   # 快速检查（推荐日常用）
bun run ~/gbrain/src/cli.ts doctor --json   # JSON格式，可解析
bun run ~/gbrain/src/cli.ts doctor          # 完整检查
```

快速检查输出示例：Health score: 90/100，有警告但不影响日常使用。

```bash
bun run ~/gbrain/src/cli.ts list           # 列出向量数据库中所有页面
bun run ~/gbrain/src/cli.ts stats          # 向量数据库统计
bun run ~/gbrain/src/cli.ts get <slug>     # 从向量数据库查看页面内容
bun run ~/gbrain/src/cli.ts embed <slug>   # 强制对某页面重新 embedding
bun run ~/gbrain/src/cli.ts embed --stale  # 对所有 stale 页面重新 embedding
bun run ~/gbrain/src/cli.ts search <词>    # tsvector 关键词搜索（可靠）
bun run ~/gbrain/src/cli.ts query <句>     # 向量语义搜索
bun run ~/gbrain/src/cli.ts delete <slug>  # 从向量数据库删除页面
```

**判断数据库内容**：`list` 的输出 title 来自数据库，不来自文件系统。

---

## gbrain put 超时问题

`gbrain put` 在 embedding 失败（401）时会hang住直到超时（30s+），即使内容已成功写入数据库。

**正确做法：** 后台运行，8秒后kill取输出：
```bash
/home/lxgxdx/.bun/bin/bun run src/cli.ts put <slug> --content '<yaml>' &
PID=$!
sleep 8
kill $PID 2>/dev/null
wait $PID 2>/dev/null
echo "Done"
```

输出中的 `[gbrain] embedding failed for <slug>` 表示内容已写入、仅embedding失败。

**`--content` flag vs stdin：** `--content` 参数方式等价于 stdin，且更简洁。两者都会在 embedding 失败时超时。

## 已知问题速查

| 问题 | 原因 | 解决 |
|------|------|------|
| compiled binary 报 ENOENT | bunfs bug 或 HOME 环境变量问题 | 确认 HOME=/home/lxgxdx 在 cron 环境中正确设置 |
| 0 chunks embedded | 直接写文件没走 stdin | 用 `gbrain put slug --content '...'` |
| query 返回空 | 向量兼容性问题 | 用 `search` 代替 |
| subprocess input=bytes 报错 | 要求 str | `input=content` 而非 `.encode()` |
| `list` 显示的页面文件系统里没有 | 数据库和文件系统独立 | 用 `get <slug>` 从数据库读，不从文件读 |
| `gbrain put` 后文件系统没变化 | 正常现象 | 内容在数据库，不在文件系统 |
| put embedding 失败 (expected 1536 dimensions, not 1024) | SiliconFlow 返回 1024维，但 GBrain 期望 text-embedding-3-large 的 1536维 | 检查 SiliconFlow API embedding 模型配置，或用 `gbrain put` 忽略警告手动记录内容 |
| put/embed 超时 | embedding 401 后hang | 后台运行+8秒kill |
