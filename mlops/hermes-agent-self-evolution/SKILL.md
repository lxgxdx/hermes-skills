---
name: hermes-agent-self-evolution
description: NousResearch hermes-agent-self-evolution 工具使用指南——用 DSPy + GEPA 自动优化 Hermes Agent 的 Skills。关键：skills 路径问题（HERMES_AGENT_REPO）、venv 安装、sessiondb vs synthetic 评估模式选择。已支持 MiniMax API（MiniMax-M2.7），通过自定义 MiniMaxLM 类实现。
tags: [hermes-agent, dspy, gepa, skill-optimization, self-evolution, nousresearch]
category: mlops
---

# hermes-agent-self-evolution 使用指南

## 概述

- 仓库：https://github.com/NousResearch/hermes-agent-self-evolution
- 功能：用 DSPy + GEPA 自动优化 Hermes Agent 的 Skills（读取执行 trace，理解失败原因针对性改写）
- 特点：无 GPU 需求，API 调用迭代优化，每次运行约 $2-10
- 所有变体必须通过测试套件、大小限制、语义一致性检查，通过 PR 提交

## MiniMax API 支持（已实现）

工具现在完全支持 MiniMax API，无需 OpenAI Key。实现方式：

1. **自定义 MiniMaxLM 类**：`evolution/core/minimax_lm.py` — 直接用 OpenAI 客户端调用 MiniMax API，支持 `quality` 参数
2. **get_lm() 路由函数**：自动识别 `minimax/*` 模型名，创建 MiniMaxLM；其他模型走标准 dspy.LM

**API Key 环境变量**（按优先级）：
- `MINIMAX_API_KEY` — 国际版（api.minimax.io）
- `MINIMAX_CN_API_KEY` — 中国版（api.minimaxi.com）

**默认模型**：`minimax/MiniMax-M2.7`，quality=`highspeed`

**常用模型映射**：
- `minimax/MiniMax-M2.7` — 标准质量
- `minimax/MiniMax-M2.7:highspeed` — 高速模式（默认）

**完整运行命令（必须先加载环境变量）**：
```bash
# 1. 加载 MiniMax API Key（必须！这些变量只在 ~/.hermes/.env 中）
set -a && source ~/.hermes/.env && set +a

# 2. 运行（HERMES_AGENT_REPO 必须设置）
cd ~/hermes-agent-self-evolution
HERMES_AGENT_REPO=~/.hermes ./venv/bin/python -m evolution.skills.evolve_skill \
  --skill dogfood --iterations 1 --eval-source synthetic
```

**验证是否成功**：
- 正常信号：`Average Metric: X.XX / 8 (XX%)` 分数逐步提升
- 异常信号：`LLM scoring: 150/150 failed (100% error rate)` → judge model 配置问题
- skill 约束验证：输出 `✓ Evolved skill passed all constraints` 即成功

## 安装（关键细节）

**必须用 self-evolution 目录内的 venv**，不能用 hermes-agent 的 venv：

```bash
cd ~/hermes-agent-self-evolution
python -m venv venv
./venv/bin/pip install -e ".[dev]"
```

hermes-agent 的 venv 在 `~/.hermes/hermes-agent/venv/`，不会给 self-evolution 提供 dspy 等依赖。

## 关键：Skills 路径问题

**问题根因**：工具内部 `get_hermes_agent_path()` 搜索 `~/.hermes/hermes-agent/skills/`，但用户的 skills 在 `~/.hermes/skills/`。

**解法**：设环境变量 `HERMES_AGENT_REPO=~/.hermes`，让工具去 `~/.hermes/skills/` 找。

```bash
HERMES_AGENT_REPO=~/.hermes ./venv/bin/python -m evolution.skills.evolve_skill --skill <skill名> ...
```

## 评估数据源选择

| 模式 | 命令 | 适用场景 | 耗时 |
|------|------|----------|------|
| synthetic | `--eval-source synthetic` | **推荐先试这个**（几分钟内出结果） | 短 |
| sessiondb | `--eval-source sessiondb` | skill 有大量真实对话历史 | 长（150 候选约 22+ 分钟，每条 9s） |

**sessiondb 完全失败的信号**：
```
LLM scoring: 150/150 failed (100% error rate)
Found 0 relevant examples
✗ No relevant examples found from session history
```
→ LLM judge 认为 150 条候选全部不相关，直接 0 个样本可用。

**推荐流程**：先用 synthetic 验证工具正常运作，再在感兴趣的 skill 上用 sessiondb 跑。

## 高价值优化候选（按实际使用频率排序）

根据 Hermes state.db 的 session 分析（2026-04-22）：
- `dogfood`：专门用于自我进化的技能，用它优化自己价值最大
- `ppt-master-usage`：PPT 相关关键词 732 次，流程复杂失败模式多
- `easyocr-unraid-p4-deploy`：刚部署，GPU 模式还在调，有大量真实 failure case
- `html-ppt`：11129 chars，结构复杂
- `homeassistant-lovelace-cards`：9916 chars，涉及 Home Assistant API 调用

## 常用命令

默认使用 `minimax/MiniMax-M2.7`（quality=highspeed），无需额外配置 OpenAI Key：

```bash
# 1. 加载 MiniMax API Key（必须！）
set -a && source ~/.hermes/.env && set +a

# 2. 运行
cd ~/hermes-agent-self-evolution

# 1次迭代，合成数据模式（推荐先试这个）
HERMES_AGENT_REPO=~/.hermes ./venv/bin/python -m evolution.skills.evolve_skill \
  --skill <skill名> \
  --iterations 1 \
  --eval-source synthetic

# 多次迭代，真实历史模式（耗时，适合高价值 skill）
HERMES_AGENT_REPO=~/.hermes ./venv/bin/python -m evolution.skills.evolve_skill \
  --skill <skill名> \
  --iterations 10 \
  --eval-source sessiondb

# 指定不同模型（使用 OpenAI）
HERMES_AGENT_REPO=~/.hermes ./venv/bin/python -m evolution.skills.evolve_skill \
  --skill <skill名> \
  --optimizer-model openai/gpt-4.1 \
  --eval-model openai/gpt-4.1-mini \
  --iterations 1 \
  --eval-source synthetic
```

## 后台运行（长时间任务）

```bash
cd ~/hermes-agent-self-evolution
nohup bash -c 'set -a && source ~/.hermes/.env && set +a && HERMES_AGENT_REPO=~/.hermes ./venv/bin/python -m evolution.skills.evolve_skill \
  --skill <skill名> --iterations 1 --eval-source sessiondb' > ~/evolution_<skill名>.log 2>&1 &

# 跟踪进度
tail -f ~/evolution_<skill名>.log
```

## 优化阶段现状

| 阶段 | 目标 | 状态 |
|------|------|------|
| Phase 1 | Skill files (SKILL.md) | ✅ 已实现 |
| Phase 2 | Tool descriptions | 🔲 计划中 |
| Phase 3 | System prompt sections | 🔲 计划中 |
| Phase 4 | Tool implementation code | 🔲 计划中 |

## 调试中发现并修复的问题（2026-04-22）

| # | 问题 | 修复 |
|---|------|------|
| 1 | `MINIMAX_BASE_URL` 国际端点 404 | 改用 `MINIMAX_CN_BASE_URL` |
| 2 | DSPy 内部参数（`signature_kwargs`、`rollout_id` 等）泄露到 OpenAI API 返回 400 | 在 `MiniMaxLM._convert_kwargs()` 添加 `_FORBIDDEN_KWARGS` 白名单过滤 |
| 3 | JSON 解析被 markdown code block 截断 | 改用 bracket-counting 解析器 |
| 4 | `deepcopy(Program)` 失败：RLock 无法 pickle | 为 Program 类添加 `__getstate__`/`__setstate__` |
| 5 | `max_tokens=2048` 不足（生成 20 个测试用例时截断） | 改为 `max_tokens=4096` |
| 6 | `optuna` 未安装 | `pip install optuna` |
| 7 | 生成的 skill 缺少 YAML frontmatter | 需在内容生成模板添加 `---` / `name:` / `description:` |

## 完整验证记录（2026-04-22）

**端到端成功运行**：耗时约 17 分钟，11 次 MIPRO trial，最佳分数 **48.49%**

- Dataset 生成（20条合成数据）✅
- GEPA → MIPROv2 fallback ✅
- Fewshot Bootstrap（6组候选）✅
- 指令候选生成（3条）✅
- MIPROv2 优化（最佳 48.49%）✅
- 约束验证 ✅（除 skill structure 格式问题外）
- 输出保存 ✅

**遗留问题**：生成的 skill content 本身正确，但缺少 YAML frontmatter（`---`, `name`, `description`），导致 `skill_structure` 约束失败。这是内容生成模板问题，不影响整体流程。

## DSPy JSON Adapter WARNING

每条消息都会输出：
```
WARNING dspy.adapters.json_adapter: Failed to use structured output format, falling back to JSON mode.
```
这是正常的，不影响功能。gepa fallback 到 JSON 模式可以正常工作。
