---
name: openclaw-skill-cleanup
description: OpenClaw 迁移到 Hermes 的 Skills 清理流程——识别不可用/冗余 Skills，修复路径引用，保留有用技能。
---

# OpenClaw 迁移 Skills 清理流程

## 适用场景

从 OpenClaw 迁移到 Hermes 后，skills 目录下留下大量 `openclaw-imports/` 子目录，需要清理。

## 判断标准（4 类）

### ❌ 直接删除
- **OpenClaw 环境变量依赖**：技能依赖 `OPENCLAW_TMUX_SOCKET_DIR`、`BAIDU_API_KEY` 等 OpenClaw 特有变量
- **外部 API Key 明文暴露**：Key 直接写在 SKILL.md 里（如百度 OCR）
- **冗余**：Hermes 已有原生版（`github`、`obsidian`）
- **脚本路径损坏且无替代**：调用不存在的 `~/.openclaw/skills/xxx` 路径
- **外部付费 API 无 Key**：如 `convert-to-pdf` 依赖的 Cross-Service-Solutions

### ⚠️ 路径需修复
- 脚本实际存在于 skills 目录内
- 仅是 SKILL.md 里的引用路径过时（`~/.openclaw/` → 实际路径）
- 修复方法：`sed` 替换或 patch

### ⚠️ 有替代但质量高
- Hermes 有 native skill，但 OpenClaw 版质量也很高
- 可考虑保留（增加覆盖），或对比后删除

### ✅ 可用
- 无脚本依赖（纯知识型 SKILL.md）
- 脚本路径已修复或无需修复

## 执行流程

### 1. 定位迁移目录
```bash
ls ~/.hermes/migration/openclaw/*/archive/extensions/
# 列出所有迁移来的插件/skill 目录
```

### 2. 列出所有待清理 skills
```bash
find ~/.hermes/skills/openclaw-imports -name "SKILL.md" | xargs wc -l | sort -n
```

### 3. 逐个检查
对每个 SKILL.md 检查：
```
grep -n "openclaw\|~/.openclaw\|{baseDir}\|BAIDU_\|API_KEY" SKILL.md
```
- 有 `~/.openclaw/skills/xxx` 引用 → 脚本存在则修复路径，不存在则删除
- 有 `{baseDir}` 引用 → 替换为实际路径
- 有 `BAIDU_API_KEY` 等外部 Key → 检查 Key 是否有效、API 是否仍可用

### 4. 删除确认
```bash
rm -rf ~/.hermes/skills/openclaw-imports/<skill-name>
```

### 5. 修复路径（如果有脚本）
```python
# 替换 SKILL.md 中的路径引用
old = "~/.openclaw/skills/xxx/"
new = "/home/lxgxdx/.hermes/skills/openclaw-imports/xxx/"
content = content.replace(old, new)
```

## 实际清理记录（2026-04-20）

### 已删除（9个）
| Skill | 原因 |
|-------|------|
| `tmux` | OpenClaw socket 多 Agent 范式，Hermes 不兼容 |
| `baidu-search` | 无 API Key，路径损坏 |
| `convert-to-pdf` | 无 API Key，外部服务不可用 |
| `pdf-smart-tool-cn` | 最大（422行），完全不可用 |
| `pdf-to-word-with-format` | 路径损坏 |
| `github` | 冗余，Hermes 有 native github skill |
| `obsidian` | 冗余，Hermes 有 native obsidian skill |
| `bing-search` | 路径损坏，有 web toolset 替代 |
| `academic-research` | 路径损坏，有 native arxiv skill |

### 已修复路径（4个）
| Skill | 修复内容 |
|-------|---------|
| `document-editor` | `~/.openclaw/...` → 实际路径 |
| `document-organizer` | `~/.openclaw/...` → 实际路径 |
| `pdf-ocr` | `{baseDir}/scripts/` → 实际路径 |
| `pdf-to-image-preview` | `scripts/` → 实际路径 |

### 保留（6个）
- `document-editor`（机关公文格式，专业）
- `document-organizer`（自动分类整理文档）
- `pdf-ocr`（百度 OCR，有免费额度）
- `pdf-to-image-preview`（PDF 转图片）
- `word-docx`（纯知识型，无路径问题）
- `ws-excel`（纯知识型，无路径问题）
