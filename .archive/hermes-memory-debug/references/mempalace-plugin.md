# MemPalace — 第三方 Memory Plugin（参考）

## 概述

MemPalace（NehuenD/hermes_mempalace）是一个本地优先的长期记忆插件，基于 **ChromaDB**（向量数据库）+ **SQLite**（知识图谱）。

**仓库**: https://github.com/NehuenD/hermes_mempalace  
**Stars**: 12  
**依赖**: `chromadb>=0.4.0`, `pyyaml`, `mempalace`

## 安装流程

```bash
# 1. 安装插件代码
hermes plugins install NehuenD/hermes_mempalace

# 2. 启用插件
hermes plugins enable mempalace

# 3. 安装 Python 依赖（用 uv，pip 不直接指向 venv）
uv pip install chromadb pyyaml --python ~/.hermes/hermes-agent/venv/bin/python

# 4. 安装 mempalace Python 包
uv pip install mempalace --python ~/.hermes/hermes-agent/venv/bin/python

# 5. 重启 Gateway
# 直接 systemctl restart 有时会超时，Gateway 会在新消息来时自动重载
hermes gateway restart
```

## 核心工具

| 工具 | 作用 |
|------|------|
| `mempalace_learn` | 存入新知识（recall-before-filing 查重） |
| `mempalace_recall` | 语义搜索记忆 |
| `mempalace_update` | 修改记忆（correct/extend/replace） |
| `mempalace_remember` | 自然语言存入 |
| `mempalace_recall_all` | 批量加载记忆 |
| `mempalace_session_write/read` | 跨 session 项目追踪 |

## 层级结构

Wing → Room → Closet → Drawer

- **Wing**: 领域/agent（如 `wing_myos`）
- **Room**: 主题（learnings/sessions/preferences）
- **Closet**: 分类（personal/projects/world）
- **Drawer**: 单条记忆（UUID + 内容 + 向量 + 版本链）

## 与内置 memory 的区别

| | 内置 memory | MemPalace |
|---|---|---|
| 存储 | `~/.hermes/memories/*.md` | ChromaDB + SQLite |
| 搜索 | 全文搜索 | 向量语义搜索 |
| 结构 | 平铺 | 宫殿层级 |
| 依赖 | 无 | chromadb, pyyaml |

## 当前状态

- **已安装**: ✅ v3.3.5
- **插件状态**: enabled
- **Gateway**: 运行中
