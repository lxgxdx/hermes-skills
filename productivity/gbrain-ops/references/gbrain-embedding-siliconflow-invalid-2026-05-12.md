# GBrain Embedding 故障：SiliconFlow Token 失效（2026-05-12）

## 故障现象

`gbrain put` 和 `gbrain embed --stale` 均成功执行，但输出：
```
[gbrain] embedding failed for <slug> (1 chunks): Embedding request failed: 404 Not Found
```

页面内容写入数据库成功，但向量 embedding 全部失败（0 chunks embedded）。

## 根因

SiliconFlow API Token 完全失效：
```bash
curl -X POST "https://api.siliconflow.cn/v1/embeddings" \
  -H "Authorization: Bearer ${SILICONFLOW_API_KEY}"
# 返回: "Invalid token"
```

GBrain 默认 embedding 服务是 SiliconFlow（`https://api.siliconflow.cn/v1`），token 失效后所有 embedding 请求均返回 404。

## 修复过程

### 1. 验证本地 Infinity 可用
```bash
curl -X POST "http://192.168.88.68:8081/embeddings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local" \
  -d '{"model":"BAAI/bge-m3","input":["test"]}'
# 返回正常 1024 维向量 ✅
```

### 2. 永久修复：改 embedding.ts 源码的 fallback URL

**`config set` 和 `.env` 都是 workaround**，正确做法是改源码，确保即使没有任何环境变量也默认走本地 Infinity：

```bash
vim ~/gbrain/src/core/embedding.ts
# 第16行改之前: return process.env.EMBEDDING_BASE_URL || 'https://api.siliconflow.cn/v1';
# 第16行改之后: return process.env.EMBEDDING_BASE_URL || 'http://192.168.88.68:8081';
```

同时清掉 gbrain/.env 里的失效 key：
```bash
echo "EMBEDDING_BASE_URL=http://192.168.88.68:8081" > ~/gbrain/.env
```

### 3. 临时 workaround（如果不方便改源码）

写入 `~/.hermes/.env`：
```bash
echo "EMBEDDING_BASE_URL=http://192.168.88.68:8081" >> ~/.hermes/.env
```

注意：`gbrain config set` **不会**影响 embedding 请求目标（bug），必须用 `.env`。

### 验证
```bash
~/.bun/bin/bun run ~/gbrain/src/cli.ts embed --slugs hermes-config
# hermes-config: all 1 chunks already embedded ✅

~/.bun/bin/bun run ~/gbrain/src/cli.ts search "PPT 配色 活力橙"
# 返回 hermes-config 结果 ✅
```

## 关键教训

1. **`config set` 不会影响 embedding URL** — GBrain CLI 的 `config set` 命令将配置写入文件，但 embedding 服务初始化时读的是环境变量
2. **源码 fallback URL 是最可靠的修复** — 改 `embedding.ts` 第16行，确保即使没有任何环境变量也默认走本地 Infinity
3. **`.env` 是临时 workaround** — 适合不想改源码的情况，但 `config set` 完全不生效
4. **embedding 失败不影响页面存储** — 内容写入数据库成功，向量为空而已；修复后 `embed --stale` 可以补上
