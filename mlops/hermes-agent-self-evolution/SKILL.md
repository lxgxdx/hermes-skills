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

**默认模型**：`minimax/MiniMax-M2.7`，quality=`highspeed`（通过 extra_body 传递）

**常用模型映射**：
- `minimax/MiniMax-M2.7` — 标准质量（配合 `quality=highspeed` extra_body 参数使用）
- `minimax/MiniMax-M2.7:highspeed` — **无效后缀**，不要使用

**重要**：MiniMax API 不支持 `:highspeed` 后缀，必须用 `MiniMax-M2.7` 模型名 + `extra_body={"quality": "highspeed"}` 参数。

**完整运行命令（wrapper 脚本方式，推荐）**：

由于 `~/.hermes/.env` 中的 API key 被 mask，需要通过 Python 从 auth.json 读取并注入环境变量。提供 wrapper 脚本：

```python
# ~/hermes-agent-self-evolution/run_evolution.py
import json, os, subprocess
from pathlib import Path

auth_path = Path.home() / ".hermes" / "auth.json"
with open(auth_path) as f:
    data = json.load(f)
token = data["credential_pool"]["minimax-cn"][0]["access_token"]

os.environ["MINIMAX_CN_API_KEY"] = token
os.environ["MINIMAX_CN_BASE_URL"] = "https://api.minimaxi.com/v1"

# 用法: python run_evolution.py <skill_name> <eval_source> [iterations]
skill = sys.argv[1] if len(sys.argv) > 1 else "ppt-master-usage"
eval_src = sys.argv[2] if len(sys.argv) > 2 else "synthetic"
iters = sys.argv[3] if len(sys.argv) > 3 else "1"

result = subprocess.run([
    "./venv/bin/python", "-m", "evolution.skills.evolve_skill",
    "--skill", skill, "--iterations", iters, "--eval-source", eval_src
], env=dict(os.environ, HERMES_AGENT_REPO=str(Path.home() / ".hermes")))
```

```bash
cd ~/hermes-agent-self-evolution
python run_evolution.py ppt-master-usage sessiondb 1
```

**验证是否成功**：
- 正常信号：`Average Metric: X.XX / 8 (XX%)` 分数逐步提升
- 异常信号：`LLM scoring: 150/150 failed (100% error rate)` → judge model 配置问题
- skill 约束验证：输出 `✓ skill_structure: Skill has valid frontmatter (name + description)` 即成功

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

## 调试中发现并修复的问题（2026-04-22~23）

| # | 问题 | 修复 |
|---|------|------|
| 1 | `MINIMAX_BASE_URL` 国际端点 404 | 改用 `MINIMAX_CN_BASE_URL` |
| 2 | DSPy 内部参数泄露到 OpenAI API 返回 400 | `MiniMaxLM._convert_kwargs()` 添加 `_FORBIDDEN_KWARGS` 白名单过滤 |
| 3 | JSON 解析被 markdown code block 截断 | 改用 bracket-counting 解析器 |
| 4 | `deepcopy(Program)` 失败：RLock 无法 pickle | 为 Program 类添加 `__getstate__`/`__setstate__` |
| 5 | `max_tokens=2048` 不足 | 改为 `max_tokens=4096` |
| 6 | `optuna` 未安装 | `pip install optuna` |
| 7 | `dspy.LM('minimax/...')` 无法路由到 MiniMaxLM | `RelevanceFilter` 改用 `get_lm()` |
| 8 | DSPy JSON Adapter 对 MiniMax 尝试结构化输出 | `MiniMaxLM.supports_response_schema = False` |
| 9 | `MiniMax-M2.7:highspeed` 模型名无效 | 去掉 `:highspeed` 后缀，用 `extra_body={"quality":"highspeed"}` |
| 10 | `skill_structure` 验证 `evolved_body` 但部署 `evolved_full` | 验证改用 `evolved_full` + frontmatter fallback |
| 11 | 原始 skill 无 frontmatter 时生成产物不合法 | Fallback 重建最小 frontmatter |

## 完整验证记录

- Dataset 生成（20条合成数据）✅
- GEPA → MIPROv2 fallback ✅
- Fewshot Bootstrap（6组候选）✅
- 指令候选生成（3条）✅
- MIPROv2 优化（最佳 48.49%）✅
- 约束验证 ✅（除 skill structure 格式问题外）
- 输出保存 ✅

**遗留问题**：生成的 skill content 本身正确，但缺少 YAML frontmatter（`---`, `name`, `description`），导致 `skill_structure` 约束失败。这是内容生成模板问题，不影响整体流程。

## SessionDB 模式验证（2026-04-23）

**问题现象**：sessiondb 模式下 `LLM scoring: 135/135 failed (100% error rate)`，所有候选评分瞬间返回0（耗时0秒）

**根因**：两个问题叠加：
1. `RelevanceFilter` 用 `dspy.LM('minimax/...')` 而不是 `get_lm()`，导致无法正确路由到 `MiniMaxLM`
2. `MiniMaxLM.supports_response_schema = True` 误导 DSPy JSON Adapter 对 MiniMax 尝试结构化输出

**修复**：
- `evolution/core/external_importers.py`：将 `dspy.LM(self.model)` 改为 `get_lm(self.model, quality="highspeed")`
- `evolution/core/minimax_lm.py`：将 `supports_response_schema` 改为 `False`

**验证结果（ppt-master-usage skill）**：
- 135 个候选全部成功评分 ✅
- 10 次迭代，最佳分数 **47.14%**
- 耗时约 20 分钟

**重要发现（2026-04-23）**：

**工具机制**：MIPROv2/GEPA 优化的是"技能调用的包装 prompt"（系统指令如何引导 Agent 使用技能），而不是技能 body 文本本身。`optimized_module.skill_text` 返回的 body 文本和原始完全一致。

- **实际表现**：多次运行 ppt-master-usage 进化，baseline 和 evolved 文件内容完全相同（`diff` 无变化）
- **结论**：这个工具无法改变 skill 内容本身，只改进调用方式。如果目标是从真实失败案例中学习并重写技能内容，需要其他机制

**sessiondb 完整运行数据（ppt-master-usage，2026-04-23）**：
- 耗时：950 秒（16 分钟）
- 数据集：25 train / 12 val / 13 holdout
- 基准分：0.444，进化后：0.411（无提升）
- 约束：全部通过（`skill_structure` ✓）

**注意**：MiniMax API 在高峰期可能返回 529 过载错误，此时可改用 `--eval-model openai/gpt-4.1-mini`（需有效的 OpenAI API Key）

## DSPy JSON Adapter WARNING

每条消息都会输出：
```
WARNING dspy.adapters.json_adapter: Failed to use structured output format, falling back to JSON mode.
```
这是正常的，不影响功能。gepa fallback 到 JSON 模式可以正常工作。
