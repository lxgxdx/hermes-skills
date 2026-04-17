---
name: openclaw-memory-sync
description: 从openclaw的SQLite记忆库读取并融合跨Agent记忆
triggers:
  - 同步记忆
  - 融合记忆
  - 之前的工作
  - openclaw记忆
---

# OpenClaw Memory Sync Skill

从 openclaw 的 SQLite 记忆库中读取长期记忆，用于融合跨智能体的记忆。

## 触发条件
用户提到要"同步记忆"、"查看之前的工作记录"、"融合两个Agent的记忆"时使用。

## 方法

openclaw 的记忆存在 SQLite 数据库中：
```
~/.openclaw/memory/main.sqlite
```

### 查询表结构
```python
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/lxgxdx/.openclaw/memory/main.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
print(cursor.fetchall())
# 输出: ['meta', 'files', 'chunks', 'embedding_cache', 'chunks_fts', ...]
"
```

### 主要表
- **chunks**: 记忆内容主体（191条），包含 text、path、source、updated_at
- **meta**: 键值对元数据
- **files**: 文件索引

### 搜索记忆内容
```python
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/lxgxdx/.openclaw/memory/main.sqlite')
cursor = conn.cursor()
# 关键词搜索
cursor.execute(\"SELECT id, path, substr(text, 1, 200) FROM chunks WHERE text LIKE '%关键词%'\")
for r in cursor.fetchall():
    print('---')
    print('ID:', r[0])
    print('Path:', r[1])
    print('Text:', r[2])
"
```

### 注意事项
- sqlite3 CLI 未安装，需要用 Python 的 sqlite3 模块查询
- chunks 表有 191 条记忆，text 字段存储实际内容
- path 字段标识来源（如 `MEMORY.md`、`memory/2026-04-08.md` 等）

## 记忆格式
openclaw 的记忆已经是摘要/总结形式，直接可读。
搜索关键词时注意：记忆可能包含"整理"、"文件夹"、"TZB"等不同表述。

## 融合流程
1. 查询 openclaw 记忆库
2. 找到相关记忆后，更新自己的 MEMORY.md
3. 告诉用户记忆已同步融合
