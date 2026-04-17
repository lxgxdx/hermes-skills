---
name: gbrain-ops
description: GBrain 个人知识库操作手册。涵盖 gbrain put 必须通过 stdin、bunfs bug、Python pathlib 优先级陷阱、同步 Hermes 对话脚本。触发词：gbrain/知识库/brain/同步对话/embedding/向量搜索
---

# GBrain Operations Guide

## 基本命令（2026-04-17）

所有命令使用：`bun run ~/gbrain/src/cli.ts <cmd>`

**禁止使用** compiled binary `~/gbrain/bin/gbrain` — 有 bunfs bug，会报 ENOENT。

---

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

`gbrain put <slug>` 会自动对内容做 embedding（写入向量数据库）。如果环境里没有配置 `OPENAI_API_KEY`（或硅基流动的 key 未被识别），embedding 会静默失败（exit 0 但 chunks=1 且无向量）。

当前配置：硅基流动的 `SILICONFLOW_API_KEY` 可以用于 `query`，但 `put` 的 embedding 仍然尝试用 OpenAI，导致 embedding failed 警告。解决方案：用 `embed <slug>` 命令事后手动触发 embedding，或确保 `OPENAI_API_KEY` 被正确传递。

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

## doctor 健康检查

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
| compiled binary ENOENT | bunfs bug | 用 `bun run src/cli.ts` |
| 0 chunks embedded | 直接写文件没走 stdin | 用 `gbrain put slug --content '...'` |
| query 返回空 | 向量兼容性问题 | 用 `search` 代替 |
| subprocess input=bytes 报错 | 要求 str | `input=content` 而非 `.encode()` |
| `list` 显示的页面文件系统里没有 | 数据库和文件系统独立 | 用 `get <slug>` 从数据库读，不从文件读 |
| `gbrain put` 后文件系统没变化 | 正常现象 | 内容在数据库，不在文件系统 |
| put/embed/doctor 超时 | embedding 401 后hang | 后台运行+8秒kill |
