---
name: hermes-memory-debug
title: Hermes Memory Tool 存储位置与调试
description: 调试Hermes内置memory tool的存储位置问题。记忆存在本地文件而非云端。用于memory tool报错、想直接编辑、或不确定存储位置时。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Hermes, Memory, Debug, Config, Storage]
    category: devops
---

# Hermes Memory Tool — 存储位置与调试

## 存储位置（本地文件）

记忆存在 `~/.hermes/memories/` 目录：
- `MEMORY.md` — Agent个人笔记（环境事实、工具经验、已解决的坑）
- `USER.md` — 用户Profile（偏好、角色、沟通习惯等）

**不是云端！** Honcho/mem0/hindsight 是可选的外部memory provider插件，需要额外配置才会启用。

## 调试方法

当不确定memory工具是否正常工作时：
```bash
cat ~/.hermes/memories/MEMORY.md
cat ~/.hermes/memories/USER.md
```

## 常见问题

### memory tool报错 "Replacement would put memory at X/Y chars"
MEMORY.md 或 USER.md 超过了字符限制（约2200和1375字符）。
**解法**：直接编辑 `~/.hermes/memories/MEMORY.md` 或 `USER.md` 精简内容

### 想清理记忆但不想用memory tool
直接用文本编辑器修改 `~/.hermes/memories/*.md`，删除不需要的条目（条目分隔符是 `§`）

## 内部实现（参考资料）

- memory tool源码：`~/.hermes/hermes-agent/tools/memory_tool.py`
- memory manager：`~/.hermes/hermes-agent/agent/memory_manager.py`
- memory provider抽象：`~/.hermes/hermes-agent/agent/memory_provider.py`
