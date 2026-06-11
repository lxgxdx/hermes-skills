# Feishu Webhook HTTP 200 False-Positive (v10 6/12 实证)

> 摘要：飞书 webhook 在 token 失效时**仍然返回 HTTP 200**，但 body 含
> `{"code":19001,"msg":"param invalid: incoming webhook access token
> invalid"}`。只看 HTTP status code 会被骗。

## 1. 陷阱的本质

Feishu 自定义机器人 webhook (`/open-apis/bot/v2/hook/<TOKEN>`) 的
**应用层错误码**在 HTTP 协议层**没有体现**：

| HTTP status | Body code | 真实含义 | Agent 容易误判 |
|------------|-----------|---------|---------------|
| 200 | `0` | 消息成功投递 | ✅ 真成功 |
| 200 | `19001` | webhook URL token 失效 | ❌ **假成功**（最危险）|
| 200 | `19002` | 签名错误 | ❌ 假成功 |
| 200 | `230xxx` | 消息体格式 / 字段错误 | ❌ 假成功 |
| 非 200 | — | 网络层错误 | ✅ 真失败 |

**根因猜测**（未公开文档）：Feishu 的 webhook endpoint 把所有
"请求到达 + 解析成功"的响应都收编到 200，只有 body 里的 `code`
字段区分业务成功 / 失败。**curl 的 `-w "%{http_code}"` 永远看到 200**。

## 2. v10 6/12 实测复现

```bash
$ HOOK="https://open.feishu.cn/open-apis/bot/v2/hook/oc_7c656031826c26b15f17d010097f3619"

# 第一次：只看 HTTP code（被骗）
$ curl -sS -o /dev/null -w "HTTP %{http_code} | time %{time_total}s\n" \
    -X POST "$HOOK" \
    -H "Content-Type: application/json" \
    -d '{"msg_type":"text","content":{"text":"[user-model v10 cron] webhook status test"}}'
HTTP 200 | time 0.085100s
# → Agent 推理："webhook 可用！可以发 v10 报告了"

# 第二次：加 -i 看完整 body（暴露真相）
$ curl -sS -X POST "$HOOK" \
    -H "Content-Type: application/json" \
    -d '{"msg_type":"text","content":{"text":"test"}}'
{"code":19001,"data":{},"msg":"param invalid: incoming webhook access token invalid"}
# → 真相：webhook 一直失效（v6/v7/v8/v9 报告的 192+ 小时不是误报）

# 第三次：发完整 post 类型（富文本）
$ curl -sS -X POST "$HOOK" \
    -H "Content-Type: application/json" \
    -d '{"msg_type":"post","content":{...big payload...}}'
{"code":19001,"data":{},"msg":"param invalid: incoming webhook access token invalid"}
# → 同样 19001
```

## 3. 历史时间线（v6 → v10 累积）

| 版本 | 报告 | 飞书推送声明 | 实际状态 |
|------|------|------------|---------|
| v6 (2026-06-06) | 192+ 小时失效 | 未发 | 真实失效 |
| v7 (2026-06-07) | 192+ 小时失效 | 未发 | 真实失效 |
| v8 (2026-06-08) | 168+ 小时失效 | 未发 | 真实失效 |
| v9 (2026-06-09) | 192+ 小时失效 | 未发 | 真实失效 |
| v10 (2026-06-12) | **240+ 小时失效** | **HTTP 200 误判 → 实际 19001** | 真实失效（与历次一致）|

**结论**：v6/v7/v8/v9 的"失效 192+ 小时"都是**对的**。v10 的 200 看似
"恢复"实际是 Feishu 的协议陷阱。

## 4. 防御协议（every Feishu call）

```bash
# 防骗最小可行检查
feishu_send() {
  local payload="$1"
  local resp=$(curl -sS -X POST "$FEISHU_HOOK" \
    -H "Content-Type: application/json" \
    -d "$payload")
  local code=$(echo "$resp" | python3 -c "import json,sys; print(json.load(sys.stdin).get('code',-1))" 2>/dev/null)

  if [ "$code" = "0" ]; then
    echo "✅ Feishu delivery confirmed (code=0)"
    return 0
  else
    echo "❌ Feishu rejected: code=$code, body=$resp"
    return 1
  fi
}

# 调用
if feishu_send '{"msg_type":"text","content":{"text":"hello"}}'; then
  echo "User notified via Feishu"
else
  echo "Webhook broken — fall back to canonical file + cron auto-deliver"
fi
```

## 5. 替代方案（webhook 失效时）

按优先级：

1. **Canonical 文件**（`~/.hermes/memories/USER.md`）—— 始终是 source of
   truth，下一个 session 必读
2. **Cron auto-deliver 渠道** —— system prompt 保证最终回复自动送达
3. **Telegram `5927500943`** —— 技术监控备用，但 user 已说明"飞书优先"
4. **微信** —— 日常渠道，但 cron 不通过 weixin 平台（cron 走 gateway）

**当且仅当** 4 个渠道**全部确认失败**，才在最终回复里写
"SILENT: webhook 失效" + 文件路径。

## 6. 相关 v10 发现

- **Feishu `clarify` 工具在 cron 模式也中招** —— 当 cron job 通过
  gateway 触发 `clarify` 时，Feishu 同样返回 HTTP 200 + code=19001，
  提示"`open_id cross app`"。**不是 clarify 工具的问题，是
  Feishu 平台对 cron-from-gateway 的鉴权**
  - 详细参考：`hermes-agent` skill 的 `references/feishu-platform-issues.md`
- **`hermes-agent` skill 已有 Feishu 19001 排错章节** —— 本 skill 的
  防御协议与 `hermes-agent` 的 22+ 天 troubleshooting 文档**一致**，
  但本 skill 增加了"body check" 实操步骤

## 7. 给未来 agent 的提醒

```
❌ NEVER:  看到 HTTP 200 就声明 "飞书推送成功"
✅ ALWAYS: parse body code 字段；code=0 才算成功
✅ ALWAYS: 落库状态明确写"webhook 19001 持续失效 N 小时"
✅ ALWAYS: fallback 写明 "cron auto-deliver 渠道"
❌ NEVER: 在 webhook 失效时偷偷跳过推送 + 假装"已通知"
```

## 8. 验证方法（如果你怀疑 webhook 可能恢复了）

```bash
# 真验证：发一个最小 text 消息，看 body 是否 code=0
curl -sS -X POST "$FEISHU_HOOK" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"ping"}}' | head -c 200
```

**不要被 HTTP 200 骗了**。看 body 里的 `code` 字段。

---

*来源：v10 cron 6/12 02:00 实测。后续 v11+ 仍按此协议推送。*
