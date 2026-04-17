---
name: pptagent-debugging
description: >
  PPTAgent (deeppresenter) 本地部署故障排查，记录2026-04-17调试发现的多个串联Bug及修复方法。
  触发条件：deeppresenter generate 命令卡住无输出、日志显示"Error connecting to server"、或"models.list() 404"错误。
tags: ["debugging", "ppt", "deeppresenter", "pptagent"]
category: productivity
---

# PPTAgent 故障排查指南

## 背景

PPTAgent (deeppresenter) 本地部署在 `/tmp/pptagent_env`，配置在 `~/.config/deeppresenter/`。

## 已知问题及修复（2026-04-17）

### 问题1：models.list() 404 导致初始化卡住

**症状**：`deeppresenter generate` 启动后无任何输出，进程挂起不退出，不创建 workspace 目录。

**根因**：`deeppresenter/utils/config.py` 第302行调用 `client.models.list()` 验证模型，但 MiniMax `/v1/models` 接口返回 404，导致验证失败卡住。

**修复**：
```python
# 文件：/tmp/pptagent_env/lib/python3.11/site-packages/deeppresenter/utils/config.py
# 位置：async def validate(self): 方法（约第300行）
# 修改为：
async def validate(self):
    # Skip models.list() check - MiniMax /v1/models returns 404
    # Validated via direct chat completions test instead
    pass
```

### 问题2：MCP 服务器全部连接失败

**症状**：日志显示大量 `Error connecting to server xxx: Connection closed`，所有 MCP 工具不可用。

**根因**：`~/.config/deeppresenter/mcp.json` 中所有工具的 `command` 设为 `python3`，但 `fastmcp` 等依赖只安装在 venv 里（`/tmp/pptagent_env`），系统 Python 找不到这些模块，导致 MCP 进程启动后立即崩溃。

**修复**：将 `mcp.json` 中所有 `python3` 替换为 `/tmp/pptagent_env/bin/python`：
```json
{
    "command": "/tmp/pptagent_env/bin/python",
    "args": ["$PACKAGE_DIR/tools/any2markdown.py"]
}
```
注意：sandbox (docker) 不需要改，docker 模式用容器内 python。

### 问题3：CLI config 命令显示的配置文件 ≠ AgentLoop 实际读取的（最关键！）

**症状**：`deeppresenter config` 显示配置正确（日志里有 api_key 和 base_url），但 `deeppresenter generate` 仍然卡住。

**根因（致命陷阱）**：有两套配置文件路径：
- `~/.config/deeppresenter/config.yaml` —— **CLI 工具命令（如 `config`、`onboard`）读写这里**，不读包内
- `PACKAGE_DIR / "config.yaml"` = `/tmp/pptagent_env/lib/python3.11/site-packages/deeppresenter/config.yaml` —— **AgentLoop 实际读取这里**

`cli/commands.py` 的 `generate()` 命令调用 `DeepPresenterConfig.load_from_file(str(CONFIG_FILE))`，而 `CONFIG_FILE` 来自 `common.py`，它解析后指向 `~/.config/deeppresenter/config.yaml`。

但 `utils/config.py` 的 `DeepPresenterConfig.load_from_file()` 当**没有传入 config_path 参数时**（即 `generate` 命令走默认路径），读取的是 `PACKAGE_DIR / "config.yaml"`（包内路径），而非 `~/.config/deeppresenter/config.yaml`！

验证方法：
```bash
# CLI config 命令显示这个路径的内容
/tmp/pptagent_env/bin/python -m deeppresenter config

# 但实际 AgentLoop 读取这个文件
cat /tmp/pptagent_env/lib/python3.11/site-packages/deeppresenter/config.yaml
```

**必须同时修改两个文件才能生效：**
```bash
# 1. CLI 配置文件（onboard 命令用这个）
~/.config/deeppresenter/config.yaml

# 2. AgentLoop 实际读取的文件（包内，必须改这个！）
/tmp/pptagent_env/lib/python3.11/site-packages/deeppresenter/config.yaml
```

### 问题4：config.yaml 的 base_url 配置错误

**症状**：validate_llms() 卡住不返回，日志停在配置加载阶段。

**根因**：配置中 `base_url` 设为 `https://api.minimaxi.com/anthropic/v1`，但这个路径在 MiniMax API 上返回 404。

**正确值**：`https://api.minimax.chat/v1`

**文件位置**：必须改 `/tmp/pptagent_env/lib/python3.11/site-packages/deeppresenter/config.yaml`（AgentLoop 读的是这个）

### 问题5：API Key 是占位符

**症状**：日志显示 `api_key: "your_key"` 或类似占位符。

**修复**：替换为真实 API Key。

## 关键路径速查

| 用途 | 路径 |
|------|------|
| 主配置 | `~/.config/deeppresenter/config.yaml` |
| MCP配置 | `~/.config/deeppresenter/mcp.json` |
| Workspace缓存 | `~/.cache/deeppresenter/<workspace_id>/` |
| 运行日志 | `~/.cache/deeppresenter/<workspace_id>/.history/deeppresenter-loop.log` |
| venv Python | `/tmp/pptagent_env/bin/python` |
| 源码 | `/tmp/pptagent_env/lib/python3.11/site-packages/deeppresenter/` |

## 调试命令

```bash
# 启动生成（后台运行）
/tmp/pptagent_env/bin/python -m deeppresenter generate "任务" \
  -o output.pptx -f file.md --lang zh --pages 25-30 &

# 查看最新 workspace 日志
LOG_DIR=$(ls -td ~/.cache/deeppresenter/*/ | head -1)
tail -f $LOG_DIR/.history/deeppresenter-loop.log

# 查看 MCP 连接状态（应有 "Connected to server" 而非 "Error connecting"）
grep -E "Connected|Error" $LOG_DIR/.history/deeppresenter-loop.log
```

## 判断进展

- 有 `Connected to server research` 等日志 → MCP 已通
- 有 `Initialized AgentLoop` → 进入主循环
- 有 `planning` / `research` / `writing` 关键字 → 真正开始生成
- 进程持续运行但无新日志 → `validate_llms()` 在等 API 响应（MiniMax 通常 2-30 秒）
- 进程退出码 0 但无输出 → 需检查日志定位错误

## 附：Hermes 记忆管理原则（2200 字符硬上限）

### 写入原则
- ✅ 写入：用户偏好、环境配置、技能知识、长期项目状态、TZB 规范
- ❌ 不写入：已完成工作日志（用 session_search 查）、调试过程、OpenClaw 内容

### 清理方法
当记忆快满（>80%）时：
1. 删重复条目：`memory (action='remove', old_text='完整原文')` — old_text 必须精确匹配
2. 删过期调试记录（关键词：工作记录、Run 0、Run 1）
3. 合并同类项（3 条变 1 条）
4. 添加新内容后确认用量在 80% 以下

### 关键区别
- 记忆（memory）：存"技能+偏好"，2200 字符上限，永久保留
- session_search：查"已完成工作详情"，无限制，自动积累

## 新发现（2026-04-17 下午）

### 问题6：MCP 工具服务器依赖模块缺失

**症状**：日志出现大量 `ModuleNotFoundError: No module named 'fastmcp'/'arxiv'/'binaryornot'/'fake_useragent'`，所有 MCP 工具（any2markdown、research、search、task 等）连接全部失败。

**根因**：deeppresenter 的工具服务器依赖这些模块，但 `pptagent_env` 虚拟环境未安装它们。

**修复**：
```bash
# 用 venv 内的 pip 安装缺失模块
/tmp/pptagent_env/bin/python -m pip install fastmcp arxiv binaryornot fake_useragent
```

### 问题7：validate_llms() API 调用挂起

即使修复了上述所有问题后，MiniMax `/v1/chat/completions` 在 curl 测试中 2 秒内返回，但 pptagent 程序内 `validate_llms()` 调用仍然无限挂起。

**可能原因**：SDK 客户端的 HTTP 库与 MiniMax 服务器的连接复用/超时行为不同，或 MiniMax-M2.7 模型在 `/v1/chat/completions` 上的行为与 curl 不同。

**下一步**：尝试换成 `MiniMax-M2` 模型，或在 config.yaml 中尝试不同的 base_url。

**最终结论（2026-04-17 晚）**：未解决。用户决定弃用 PPTAgent，改用 ppt-master。

**备选方案：ppt-master（已验证可用）**
- 仓库：`~/.hermes/skills/ppt-master/`（已克隆）
- venv：`~/.hermes/hermes-agent/.venv`
- 项目初始化：`python3 ${SKILL_DIR}/scripts/project_manager.py init <name> --format ppt169`
- 源文件导入：`python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <proj_path> <files...> --move`
- 项目路径：`/home/lxgxdx/projects/<name_ppt169_YYYYMMDD>/`
- 完整流程：Step 1（源文件）→ Step 2（初始化+导入）→ Step 3（模板）→ Step 4（八项确认）→ Step 6（生成SVG）→ Step 7（导出PPTX）
