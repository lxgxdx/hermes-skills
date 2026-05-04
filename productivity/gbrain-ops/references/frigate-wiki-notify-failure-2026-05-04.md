# Frigate Wiki 同步脚本通知故障记录（2026-05-04）

## 事件摘要

cron job `frigate-wiki-weekly-update` 运行 `python3 ~/.hermes/scripts/frigate-wiki-updater.py`，文档同步成功（39个文档已更新），但通知发送失败导致脚本以 exit code 39 退出。

**现象**：`Script Error` / exit 39，但文档实际已全部更新到 `~/wiki/raw/articles/`。

## 失败排查

### Telegram
- Token 从 `~/.hermes/.env` 的 `TELEGRAM_BOT_TOKEN` 读取
- Chat ID: `5927500943`（Home channel）
- 结果：`{"ok":false,"error_code":404,"description":"Not Found"}` — bot token 无效或 bot 未绑定到任何 chat

### Feishu
- 配置：`FEISHU_APP_ID`, `FEISHU_APP_SECRET` 在 `~/.hermes/.env`
- 结果：`{"code":10014,"msg":"app secret invalid"}` — secret 已失效

### WeChat
- 使用 Hermes 内置 weixin platform（`WEIXIN_TOKEN`, `WEIXIN_ACCOUNT_ID`）
- 结果：无响应，不确定是否成功

## 根因

cron prompt 里写了"发送消息到 Telegram（Home channel）"，但：
1. Telegram bot token 可能是截断的（`.env` 里显示 `876452...9Hxc` — 中间被遮蔽）
2. Feishu app secret 已失效
3. 通知失败导致 Python 脚本 `sys.exit(1)` 或类似非零退出

## 关键教训

**cron job 的通知步骤是独立的风险点**。当文档同步本身成功但通知失败时：
- 脚本退出码 != 0 → Hermes 报告 "Script Error"
- 但数据实际已更新 → 不需要重跑脚本
- 用户看不到通知 → 以为什么都没发生

**修复方向**：cron job 应将通知结果与主流程分离，或者通知失败不应导致非零退出码。

## 当前配置位置

```
~/.hermes/.env:
  TELEGRAM_BOT_TOKEN=876452...9Hxc      # 被截断，无法确认完整 token
  TELEGRAM_HOME_CHANNEL=5927500943
  FEISHU_APP_ID=cli_a969394fa639dcc0
  FEISHU_APP_SECRET=PQ2F7x...7vzQ        # 被截断且已失效
  WEIXIN_TOKEN=c2049b...68c6             # 被截断
  WEIXIN_HOME_CHANNEL=o9cq808UFBCpJzQF430OM41xXIZE@im.wechat
```

## 参考

- cron job 定义：`~/.hermes/cron/jobs.json` → `frigate-wiki-weekly-update`
- 同步脚本：`~/.hermes/scripts/frigate-wiki-updater.py`
