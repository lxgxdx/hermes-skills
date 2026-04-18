---
name: gbrain-ops
description: GBrain 个人知识库操作手册。涵盖 gbrain put 必须通过 stdin、bunfs bug、Python pathlib 优先级陷阱、同步 Hermes 对话脚本。触发词：gbrain/知识库/brain/同步对话/embedding/向量搜索
---

# GBrain Operations Guide

## 基本命令（2026-04-17）

所有命令使用：`bun run ~/gbrain/src/cli.ts <cmd>`

**推荐使用** `bun run src/cli.ts` — compiled binary `/home/lxgxdx/gbrain/bin/gbrain` 有 bunfs 路径 bug，会报 `ENOENT: no such file or directory, open '/$bunfs/root/pglite.data'`。

### 正确环境变量（cron/非交互shell专用）
```bash
HOME=/home/lxgxdx
BUN_INSTALL="$HOME/.bun"          # 非交互环境必须显式设置
PATH="$BUN_INSTALL/bin:$PATH"      # bun 不在默认 PATH 中
EMBEDDING_BASE_URL=http://192.168.88.68:8081   # 本地 Infinity（Unraid Tesla P4）
USE_LOCAL_INFINITY=1
```
**注意**：这些变量必须存在于 shell 环境中，`.env` 文件不会自动加载。

### 正确命令
```bash
/home/lxgxdx/.bun/bin/bun run src/cli.ts doctor --fast
/home/lxgxdx/.bun/bin/bun run src/cli.ts put <slug> --content '...'
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
    ['/home/lxgxdx/.bun/bin/bun', 'run', '/home/lxgxdx/gbrain/src/cli.ts', 'put', slug],
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

- `gbrain search <keyword>` — tsvector 关键词搜索（快、可靠，不依赖 embedding 服务）
- `gbrain query <自然语言>` — 向量语义搜索（依赖 `EMBEDDING_BASE_URL` 环境变量正确设置）

**`query` 返回空或极低分（score < 0.001）的排查顺序：**
1. 环境变量是否设置了 `EMBEDDING_BASE_URL` 和 `USE_LOCAL_INFINITY`？
2. Infinity 服务是否在线（`curl http://192.168.88.68:8081/embeddings`）？
3. `embed coverage` 是否 100%（`gbrain health`）？

### put 也做 embedding！

`gbrain put <slug>` 会自动对内容做 embedding（写入向量数据库）。如果 embedding 失败（401 或维度不匹配），内容仍会写入数据库，但向量为空。

维度不匹配症状：`expected 1536 dimensions, not 1024` — 旧版配置使用 SiliconFlow text-embedding-3-large (1536维)，但当前使用 BAAI/bge-m3 (1024维)。

**当前环境**：使用本地 Infinity（Unraid Tesla P4），BAAI/bge-m3 模型，1024维，无维度不匹配问题。

解决方案：确认 `~/gbrain/src/core/embedding.ts` 中 `DIMENSIONS = 1024` 与 `~/gbrain/src/core/pglite-schema.ts` 中 `vector(1024)` 一致。

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
### 当前环境 bunfs bug 状态（2026-04-18）

所有使用 PGLite 数据库的 gbrain 命令均通过 `~/.bun/bin/bun run ~/gbrain/src/cli.ts` 成功执行，不再使用 compiled binary：

- ✅ `gbrain query` / `ask` — 向量语义搜索
- ✅ `gbrain init --pglite` — 可初始化
- ✅ `gbrain config show/get/set` — 配置操作
- ✅ `gbrain list/get/delete/stats` — 数据库读写
- ✅ `gbrain embed --stale` — embedding 补全
- ✅ `gbrain doctor` — 完整检查
- ✅ `gbrain health` — 健康检查

```bash
bun run ~/gbrain/src/cli.ts doctor --fast   # 快速检查（推荐日常用）
bun run ~/gbrain/src/cli.ts doctor --json   # JSON格式，可解析
bun run ~/gbrain/src/cli.ts doctor          # 完整检查
```

快速检查输出示例：Health score: 9/10，Embed coverage: 100%。

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

---

## gbrain put 超时问题

`gbrain put` 在 embedding 失败（连接超时）时会 hang 直到超时（30s+），即使内容已成功写入数据库。

**正确做法：** 后台运行，8秒后kill取输出：
```bash
cd /home/lxgxdx/gbrain && /home/lxgxdx/.bun/bin/bun run src/cli.ts put <slug> --content '<yaml>' &
PID=$!
sleep 8
kill $PID 2>/dev/null
wait $PID 2>/dev/null
echo "Done"
```

输出中的 `[gbrain] embedding failed for <slug>` 表示内容已写入、仅embedding失败。

**`--content` flag vs stdin：** `--content` 参数方式等价于 stdin，且更简洁。两者都会在 embedding 失败时超时。

## 本地 Infinity 向量服务配置（2026-04-18）

**Infinity 部署**：Unraid (192.168.88.68:8081)，Tesla P4，镜像 michaelf34/infinity:latest，模型 BAAI/bge-m3，1024维。

**环境变量**（必须写入 `~/.bashrc` 以便 cron 和 shell 持久化）：
```bash
export EMBEDDING_BASE_URL=http://192.168.88.68:8081
export USE_LOCAL_INFINITY=1
[ -f ~/.gbrain/.env ] && set -a && source ~/.gbrain/.env && set +a
```

**验证**：
```bash
curl -X POST http://192.168.88.68:8081/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"model":"BAAI/bge-m3","input":"hello"}'
# 应返回 1024 维向量
```

**归档脚本**（`archive-and-cleanup-sessions.py`）已更新为使用本地 Infinity 环境变量，不再依赖 SiliconFlow。

| `gbrain query` 返回空但 `call query` 有结果 | CLI 和 MCP 工具走不同代码路径 | CLI 需要 shell 环境变量，`call query` 走 gbrain 内部配置 |

## `call query` vs `gbrain query` 的区别

GBrain 有两套 query 实现，行为不同：

- **`gbrain query`**（CLI）：依赖 shell 环境变量 `EMBEDDING_BASE_URL` + `USE_LOCAL_INFINITY`，没有则 fallback 到 SiliconFlow（token 失效）返回空
- **`call query`**（MCP/工具）：走 gbrain 内部配置，不依赖 shell 环境变量

**排查流程**：如果 `gbrain query <句子>` 返回空，先用 `source ~/.bashrc` 加载环境变量，或显式设置：
```bash
export EMBEDDING_BASE_URL=http://192.168.88.68:8081
export USE_LOCAL_INFINITY=1
~/.bun/bin/bun run ~/gbrain/src/cli.ts query "<句子>"
```

## Hermes Agent 自更新机制

**当前版本**：v0.10.0 (2026.4.16)，状态 "Up to date"

- `hermes update` 是手动命令，**没有内置自动检查**
- 建议添加每周 cron 任务定期检查：`0 8 * * 0 hermes update --gateway`

## GitHub WeChat Bug Issue

- **Issue**：[WeChat] asyncio.timeout bug and session expiration not handled gracefully #12154
- **仓库**：https://github.com/NousResearch/hermes-agent/issues/12154
- **状态**：Open（2026-04-18 提交，暂无修复/评论）
- **内容**：asyncio.timeout() 在 task 外调用导致消息发送失败；iLink session 过期后暂停10分钟不重连

## 已知问题速查
|------|------|------|
| compiled binary 报 ENOENT | bunfs bug 或 HOME 环境变量问题 | 使用 `~/.bun/bin/bun run ~/gbrain/src/cli.ts` 而非 compiled binary |
| 0 chunks embedded | 直接写文件没走 stdin | 用 `gbrain put slug --content '...'` |
| query 返回空或极低分 | 环境变量未设置或 Infinity 离线 | 检查 `EMBEDDING_BASE_URL` / `USE_LOCAL_INFINITY`，验证 Infinity 在线 |
| subprocess input=bytes 报错 | 要求 str | `input=content` 而非 `.encode()` |
| `list` 显示的页面文件系统里没有 | 数据库和文件系统独立 | 用 `get <slug>` 从数据库读，不从文件读 |
| `gbrain put` 后文件系统没变化 | 正常现象 | 内容在数据库，不在文件系统 |
| `doctor --fast` 报 "Could not find skills directory" 但 skills 目录存在 | doctor 的 skills 路径解析有bug | 可忽略此warn，skills实际存在且可用 |
| Embed coverage 低于 100% | 部分页面 embedding 失败 | `gbrain embed --stale` 补全缺失的 embedding |


