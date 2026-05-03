---
name: github-pat-retrieval
description: 从配置文件中检索GitHub PAT的正确位置，以及处理部分遮蔽(redaction)token的方法。
triggers:
  - "GitHub PAT 找不到"
  - "gh auth login 失败"
  - "token 认证失败"
  - "github token 401"
---

# GitHub PAT 检索与认证

## 存储位置（按优先级）

1. **git-credentials**: `~/.git-credentials`
2. **gh CLI config**: `~/.config/gh/hosts.yml`
3. **环境变量**: `GITHUB_TOKEN` / `GH_TOKEN`

## 常见问题：Token 被 Redaction（遮蔽）

### 问题现象
通过微信/Telegram发送的GitHub PAT，经过Hermes系统处理后会被部分遮蔽：
```
# 原始token
ghp_完整字符序列

# 经过redaction后（存储在session文件/.git-credentials中）
ghp_Fc...ZhBU
```

中间的 `...` **不是token的实际字符**，而是Hermes的敏感信息脱敏标记。真实token = `ghp_Fc` + [被遮蔽部分] + `ZhBU`。

### 影响
用这个被遮蔽的token认证会返回 `401 Unauthorized`。

### 解决步骤

1. 让用户重新提供完整的、未经过聊天工具传输的PAT
2. 直接设置到shell环境变量（不经过聊天工具）
3. 或直接写入git-credentials

### 为什么微信/TG会导致token redaction
Hermes的 `agent/redact.py` 会对GitHub PAT格式的字符串进行脱敏，被存储到session文件或日志中的token都会被部分遮蔽。

## 快速验证 PAT 是否有效
使用 `gh auth status` 或 `gh api user` — 如果未认证会提示登录。

## GitHub 代码搜索的限制（重要）

### 未认证搜索必定失败
GitHub 搜索 API（`/search/code`）需要认证：
- **无 PAT**：返回 `Requires authentication`
- **PAT 作用域不足**：返回 `401` 或空结果
- `gh search code` CLI 命令需要 `repo` 作用域的 PAT

### 有效方案

**方案 A — gh CLI（推荐）：**
```bash
# 需要先登录，并确认 PAT 有 repo 作用域
gh auth login --hostname github.com
# 搜索
gh search code "刹车片钢背" --limit 10
```

**方案 B — curl + PAT：**
```bash
curl -s -H "Authorization: token ghp_xxx" \
  "https://api.github.com/search/code?q=%E5%88%86%E8%BD%A6%E7%89%87%E9%92%A2%E8%83%8C" \
  | jq '.items[].html_url'
```

### 当前 PAT 状态
- `ghp_Fc...ZhBU`（redacted）= 被遮蔽的 PAT，中间 `...` 是脱敏标记
- 有效但被截断，无法直接使用
**注意：** Token 不能是被 redacted 的（包含 `...` 的无效）。需要用户提供原始、未经过聊天工具传输的完整 token。

### 搜索替代方案

当 PAT 不可用或搜索失败时，见 `references/github-search-alternatives.md`：SourceGraph（无需登录）、Google站内搜索、GitHub中文搜索等。

## 直接用 curl 提交 GitHub Issue（gh CLI 未登录时）

当 `gh auth status` 显示未登录时，可以用 curl 直接调用 GitHub API：

```bash
# 基本格式
curl -s -u "USERNAME:TOKEN" \
  -X POST "https://api.github.com/repos/OWNER/REPO/issues" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -d '{"title": "Issue标题", "body": "Issue内容"}'
```

**实际例子（ NousResearch/hermes-agent）：**
```bash
curl -s -u "lxgxdx:ghp_xxx" \
  -X POST "https://api.github.com/repos/NousResearch/hermes-agent/issues" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -d '{"title": "[Bug] 标题", "body": "## Bug Description\n\n..."}'
```

**注意：** Token 不能是被 redacted 的（包含 `...` 的无效）。需要用户提供原始、未经过聊天工具传输的完整 token。
