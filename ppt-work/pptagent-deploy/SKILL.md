---
name: pptagent-deploy
description: PPTAgent（ICIP/EMNLP 2025）本地部署指南，含 uv 安装、依赖解决、API key 配置
triggers:
  - 部署 PPTAgent
  - install PPTAgent
  - icip-cas PPTAgent
---

# PPTAgent 本地部署指南

## 概述
PPTAgent（中科院 ICIP 出品，EMNLP 2025 论文）是一个 Agent 驱动的 PPT 生成框架，支持从文档/提示词自动生成专业演示文稿。

GitHub: https://github.com/icip-cas/PPTAgent

## 部署环境
- Python 3.11+
- uv 包管理器
- API key（OpenRouter 或智谱 bigmodel.cn）
- 可选：Docker（用于 sandbox 模式）

## 安装步骤

### 1. 创建虚拟环境
```bash
uv venv /tmp/pptagent_env
source /tmp/pptagent_env/bin/activate
```

### 2. 安装依赖（耐心等待）
由于网络慢，大型包（gradio 60MB、playwright 44MB、opencv 57MB、speechrecognition 31MB）下载耗时长。
```bash
# 设置超时，避免下载超时
export UV_HTTP_TIMEOUT=600

# 逐个安装大包（--no-deps 避免重复解析）
uv pip install gradio==5.50.0 --no-deps
uv pip install playwright --no-deps
uv pip install opencv-python-headless --no-deps
uv pip install speechrecognition --no-deps

# 安装 pptagent（包含全部216个依赖包）
uv pip install pptagent
```

### 3. 安装 Playwright 浏览器
```bash
playwright install chromium
```

### 4. 安装 npm 依赖
```bash
npm install --prefix /home/lxgxdx/.cache/deeppresenter/html2pptx html2pptx
```

### 5. 配置文件路径
- 配置目录：`~/.cache/deeppresenter/`
- 示例配置在包内：`/tmp/pptagent_env/lib/python3.11/site-packages/deeppresenter/config.yaml.example`
- 复制配置：`cp .../config.yaml.example ~/.cache/deeppresenter/config.yaml`

### 6. API Key 配置
修改 `~/.cache/deeppresenter/config.yaml`：

**方案A：OpenRouter（推荐，可访问 Claude/Gemini）**
```yaml
research_agent:
  base_url: "https://openrouter.ai/api/v1"
  model: "anthropic/claude-sonnet-4.5"
  api_key: "你的OPENROUTER_API_KEY"

design_agent:
  base_url: "https://openrouter.ai/api/v1"
  model: "google/gemini-3-pro-preview"
  api_key: "你的OPENROUTER_API_KEY"
```

**方案B：智谱 GLM**
```yaml
long_context_model:
  base_url: "https://open.bigmodel.cn/api/paas/v4/"
  model: "glm-4.5"
  api_key: "你的智谱API_KEY"
```

### 7. 运行
```bash
source /tmp/pptagent_env/bin/activate
pptagent onboard  # 首次配置向导
pptagent generate "你的PPT主题" -o output.pptx
```

## 常用命令
```bash
pptagent onboard          # 交互式配置向导
pptagent generate "..." -o out.pptx   # 生成PPT
pptagent generate "..." -f data.xlsx -p "8-12"  # 带附件，指定页数
pptagent config           # 查看当前配置
```

## 已知的坑
1. **gradio 下载超时**：设置 `UV_HTTP_TIMEOUT=600`，60MB 包需要耐心等待
2. **playwright 下载超时**：同样需要 `UV_HTTP_TIMEOUT=600`
3. **pptagent 需要 API key**：不配置 key 无法运行
4. **config.yaml 位置**：是 `~/.cache/deeppresenter/config.yaml`，不是包里的
5. **Docker 可选**：有 Docker 则使用 sandbox 模式更稳定，没有也能跑
6. **Windows 不支持**：需要 WSL
7. **offline_mode 必须为 false**：默认值可能是 true，务必显式设为 false，否则完全禁用网络调用
8. **api_key 不能是占位符**：config.yaml 示例里可能有 `"your_key"` 字样的占位符，必须替换成真实 key
9. **openclaw 的 key 和 pptagent 不通用**：openclaw 的 key 存在 `~/.openclaw/agents/main/agent/auth-profiles.json`，是 `sk-cp-` 格式，但该 key 调用 MiniMax API 会返回 401（openclaw 内部有代理转换）。pptagent 需要单独的、未经代理的 API key
10. **base_url 格式**：MiniMax 实际可用 base_url 为 `https://api.minimaxi.com/anthropic/v1`，模型用 `MiniMax-M2.7`

## 任务卡住诊断流程

**症状**：进程存在，CPU 0%，无输出文件，无网络活动

```bash
# 1. 检查进程是否存活及运行时长
ps aux | grep pptagent | grep -v grep
ps -p <PID> -o pid,etime,cmd

# 2. 检查是否有对外网络连接（无连接 = 卡在等API响应或内部死锁）
ss -tp | grep <PID>

# 3. 检查 config.yaml 是否正确（offline_mode / api_key / base_url）
cat ~/.cache/deeppresenter/config.yaml

# 4. 检查日志文件（子进程的日志通过管道输出，没写入磁盘）
#    若有日志文件：
cat ~/.cache/deeppresenter/<workspace_id>/.history/deeppresenter-loop.log

# 5. 杀掉卡住进程（需同时杀父进程和所有子进程）
#    先找到所有相关进程：
ps aux | grep "deeppresenter\|pptagent" | grep -v grep
#    然后批量杀掉：
kill -9 <pid1> <pid2> <pid3> ...

# 6. 验证 API key 有效性（单独测试）
curl -s --max-time 15 \
  -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}' \
  "https://api.minimaxi.com/anthropic/v1/chat/completions"
#   若返回 401 = key无效；404 = URL不对；200 = 正常
```

**常见根因**：
- API key 是 "your_key" 占位符 → 进程等响应超时（40分钟+）
- `offline_mode: true` → 完全禁用网络
- openclaw 的 key 格式（`sk-cp-`）不能直接用于 MiniMax API → 返回 401
- 模型不支持当前任务

## 与 ppt-master 的对比
- ppt-master：轻量，SVG 手动设计，完全可控，适合固定内容
- PPTAgent：重量，端到端 AI 生成，设计精美，适合文档转演示
- **党政培训场景：内容固定，强烈推荐用 ppt-master**；学术/产品演示可选 PPTAgent
