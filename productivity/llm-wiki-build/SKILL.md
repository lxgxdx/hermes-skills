---
name: llm-wiki-build
description: 从官方文档构建 LLM Wiki 知识库的完整流程。包含中文文档镜像技巧、Wiki 结构初始化、批量创建 entity/concept 页面的规范。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wiki, knowledge-base, documentation]
    category: productivity
---

# LLM Wiki 构建流程

## 触发条件

用户要求"构建某某主题的个人知识库"时激活。

## 完整流程

### 1. 初始化 Wiki 结构

```bash
mkdir -p ~/wiki/{raw/{articles,papers,transcripts,assets},entities,concepts,comparisons,queries}
```

三个必需文件：
- `SCHEMA.md` — 领域定义、conventions、frontmatter 规范、tag taxonomy
- `index.md` — 内容目录，所有页面的一句话摘要
- `log.md` — 操作日志，只增不减

### 2. 抓取文档

**关键经验**：英文文档站经常超时，优先使用中文镜像站（如 docs.frigate-cn.video），内容一致且加载更快。

使用浏览器或 curl 抓取页面内容，保存到 `raw/articles/`。

### 3. 原始来源存储

每个文档摄取后，先保存到 `raw/articles/` 作为不可变来源：
```markdown
# 页面标题

> 来源：<URL>
> 最后更新：YYYY-MM-DD

<内容>
```

**多文档拆分技巧**：汇编类文档（如政策文件汇编）可能含多个独立文件。
1. 用 `python-docx` 读取所有段落，标记各文档标题所在段落索引
2. 根据索引范围切分，保存为独立文件
3. 切分后再并行派发 subagent 创建各 entity 页面

```python
# 示例：定位多文档起止位置
from docx import Document
doc = Document('doc.docx')
paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
# 找各文档标题段落索引
for i, para in enumerate(paragraphs):
    if '条例名称' in para:
        print(f'[{i}] {para[:60]}')
```

### 4. Wiki 页面类型规范

**Entity 页面**（实体，如硬件产品、服务）：
```markdown
---
title: <实体名>
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity
tags: [<taxonomy tags>]
sources: [raw/articles/source.md]
---

## 概述
## 关键事实
## 相关链接（[[wikilinks]]）
```

**Concept 页面**（概念、原理）：
```markdown
---
title: <概念名>
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: concept
tags: [<taxonomy tags>]
sources: []
---

## 概述
## 工作原理/核心特性
## 配置要点
## 相关概念（[[wikilinks]]）
```

**每个页面必须**：
- 包含 YAML frontmatter（title, created, updated, type, tags, sources）
- 至少 2 个指向其他 wiki 页面的 [[wikilinks]]
- 来源标注到 `sources` 字段

### 5. 维护 index.md 和 log.md

- **index.md**：每创建一个页面就添加一行（实体或概念章节下），包含页面名和一句话摘要
- **log.md**：每个操作追加一条日志，包含创建的文件列表

## 已知问题

- 英文文档站超时：改用中文镜像站（适用于 Frigate 等主流项目）
- Wiki 页面内容需要实际使用中持续补充，初始构建只建框架

## 知识库分工（用户2026-04-19确立）

- **LLM Wiki**（`~/wiki` 或 `~/klipper-wiki`）：技术文档（Frigate/Klipper等）
- **GBrain**：对话记忆、碎片想法、模糊检索

## 并行批量建页技巧（2026-04-19）

创建多个 concept 页面时，用 `delegate_task` 并行处理效率最高：

```bash
# 单次并行创建5个页面（一个 delegate_task 带5个 tasks）
delegate_task(tasks=[
  {"goal": "创建 bed-mesh concept", "context": "Wiki目录: ~/klipper-wiki/", ...},
  {"goal": "创建 pressure-advance concept", ...},
  ...
])
```

**经验**：
- 每个 subagent 独立读取源文档、写入目标文件，无需主 agent 中转数据
- 5个页面并行约60-90秒完成，单 agent 串行需要5倍以上时间
- 适合20+页面规模的大批量创建；少量页面（1-3个）直接串行更简单
- 批量大时让 subagent 一次处理多个页面（`tasks` 数组），减少任务启动 overhead
- Klipper 45页实测：分9批（每批5个），全部完成约2小时（含并发延迟）

## Wiki 路径

**按领域分目录，每项目独立，不混用。**

- Frigate Wiki: `~/wiki/`
- Klipper Wiki: `~/klipper-wiki/`
- Home Assistant Wiki: `~/ha-wiki/`（2026-04-20 新建，与 Frigate 完全独立）
- GBrain：对话记忆/碎片想法，与 LLM Wiki 分工明确

## 多项目 Wiki 并行构建（2026-04-20 经验）

**教训**：规划新 Wiki 前先确认用户期望的目录结构，技能文档类内容不应混在已有项目的 Wiki 里。

**正确流程**：
1. 询问 Wiki 放在哪个目录（是否有现有项目 Wiki）
2. 如有多个领域，明确每个领域的 Wiki 路径
3. 每个领域创建独立的 `SCHEMA.md / index.md / log.md`
4. 不同领域 Wiki 内容互不干扰

## Klipper Wiki 实测数据（2026-04-19）
- 原始文档：50篇（官方 klipper3d.org），共 ~1.5MB
- 提炼结果：45个 concept 页面，覆盖核心配置、调平技术、运动控制、硬件驱动、通信协议、调试工具
- 经验：Klipper 文档质量高、结构清晰，50篇可压缩为45个页面（features.md 合并到 klipper.md）
- 优先级排序：probe-calibrate > delta-calibrate > debugging > api-server > command-templates > endstop-phase > hall-filament-sensor > load-cell

## 页面命名规范

- 英文标题 → kebab-case（如 `pressure-advance.md`、`bed-leveling.md`）
- 中文标题 → 拼音（如 `kong-zhi-qi.md`）

## 自动更新脚本（Frigate 示例）

```bash
#!/bin/bash
# 位置: ~/wiki/scripts/update.sh
# cron: 0 9 * * 1 bash ~/wiki/scripts/update.sh
WIKI_DIR=~/wiki
FEISHU_WEBHOOK="飞书webhook地址"
cd $WIKI_DIR || exit 1
UPDATES=$(find raw/articles -name "*.md" -mtime -7 2>/dev/null | wc -l)
if [ "$UPDATES" -gt 0 ]; then
  MSG="Frigate Wiki 更新：发现 $UPDATES 个文档有变化，请检查。"
  curl -s -X POST "$FEISHU_WEBHOOK" -H "Content-Type: application/json" \
    -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$MSG\"}}" 2>/dev/null
fi
```
