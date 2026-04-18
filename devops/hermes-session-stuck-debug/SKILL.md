---
name: hermes-session-stuck-debug
description: Hermes Gateway session卡住故障排查 - 微信返回旧响应
---
# Hermes Gateway Session 卡住故障排查

## 症状
- 微信发消息返回旧的/重复的响应
- 日志出现 `invalid params, invalid function arguments json string`
- 日志写明 `Skipping transcript persistence for failed request in session <ID> to prevent session growth loop`
- 同一 session 反复失败，返回旧响应

## 排查步骤

### 1. 查看错误日志
```bash
tail -200 ~/.hermes/logs/errors.log
```
找 `Non-retryable client error` 或 `invalid function arguments`

### 2. 查看 agent.log 确认具体 session
```bash
tail -100 ~/.hermes/logs/agent.log
```
找到出错的 session ID（如 `20260418_160551_874df0`）

### 3. 确认 gateway 运行状态
```bash
ps aux | grep hermes | grep -v grep
```

### 4. 找到卡住的 session 文件
```bash
ls ~/.hermes/sessions/ | grep <session_id>
# 例如
ls ~/.hermes/sessions/ | grep 20260418_160551
```

## 修复方案

### 方案A：删除卡住的 session 文件（推荐）
```bash
rm ~/.hermes/sessions/<session_id>.jsonl
rm ~/.hermes/sessions/session_<session_id>.json
# 然后重启 gateway
```

### 方案B：重启 gateway
```bash
# 重启 hermes gateway
```

## 根因
某个工具/插件调用时参数格式错误，导致 session 卡在失败状态，不断返回最近一次成功生成的响应。

## 预防
- 关注日志中的 `Skipping transcript persistence for failed request` 警告
- 及时删除卡住的 session 避免用户收到过时响应
