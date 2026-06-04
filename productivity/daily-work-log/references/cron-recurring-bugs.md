# 跨日复现的 cron 任务已知 bug & 信号清单

> 2026-06-04 首次整理。这些 bug 每天会在 cron session 中重复出现，必须在「未完成 / 待跟进」中显式标注（甚至跨日持续 follow-up），否则会被静默丢失。

## 🔴 高优先级（每日重复出现的 P0 信号）

### 1. 飞书 webhook 持续失效（`oc_7c656031826c26b15f17d010097f3619`）

- **症状**：所有 cron 任务完成后向飞书回报时返回 `19001 access token invalid`
- **首次发现**：2026-06-02（48+ 小时）
- **2026-06-04 状态**：72+ 小时持续失效
- **影响**：所有 cron 任务的用户通知全部丢失；用户只能通过每日 00:00 的 daily-work-log cron session 间接看到结果
- **应对**：daily log 必须在「未完成 / 待跟进」顶部列出此条；连续多日需要在「未完成」开头用 `🔴 **飞书 webhook 持续失效 XX 小时**` 突出显示
- **修复路径**（需用户操作，不在 cron 范围内）：重新走飞书开放平台授权流程，更新 webhook token 到 `~/.hermes/config.yaml` 或 `.env`

### 2. `hermes-backup.sh` 不会写 backup.log

- **症状**：脚本只 `echo` 到 stdout，cron 环境下的输出通常被吞掉；用户 `tail -f /home/lxgxdx/scripts/backup.log` 看不到任何记录
- **首次发现**：2026-06-04 03:00 cron session；agent 当时手动 `>> "$LOG_FILE"` 追加了
- **影响**：备份失败时无任何日志留痕，故障发现延迟
- **应对**：
  1. daily log 「未完成 / 待跟进」列出"修复建议"块，附完整 patch 代码：
     ```bash
     # 在 hermes-backup.sh 头部加
     LOG_FILE="/home/lxgxdx/scripts/backup.log"
     exec >> "$LOG_FILE" 2>&1
     ```
  2. 同时记录在"连续多日"清单直到脚本被改
- **修复路径**：用户改 `~/scripts/hermes-backup.sh` 即可（一行 `exec` 解决）

### 3. GitHub Skills 同步 pre-push PAT 拦截

- **症状**：每日 06:00 cron 跑 `bash /tmp/hermes-skills-sync.sh`，pre-push 正则 `ghp_[A-Za-z0-9]{20,}` 匹配到 `.archive/` 下的真实 GitHub PAT，sync 整个被 block
- **首次发现**：2026-06-04 06:00 cron session（agent 当时 `git rm --cached` + `git checkout` 修复，但 PAT 本身未 revoke）
- **PAT 实际位置**：
  - `~/.hermes/skills/.archive/github-pat-retrieval/SKILL.md`（line ~75，diff 示例 URL 内）
  - `~/.hermes/skills/.archive/github-pat-retrieval/references/git-config-token-extract.md`（40 字符变体）
- **安全风险**：PAT 自 2026-05-12 起以明文存盘
- **应对**：
  1. daily log 「未完成 / 待跟进」必须用 `🔴 GitHub PAT 视为已泄露，建议立即 revoke + 生成新 token` 提示
  2. 提示位置应突出（紧随飞书 webhook 之后），避免被淹没在 13 条普通 follow-up 中
- **修复路径**：用户去 GitHub Settings → Developer settings → Personal access tokens 撤销旧 token + 生成新 token

## 🟡 中优先级（每日 cron 行为差异）

### 4. Dream cycle 累计计数 vs llm-wiki-build 实际计数的口径冲突

- **症状**：dream cycle 报"今日 Wiki +N pages"，但实际 cron session 只新建 M 个页面（M < N）
- **首次发现**：2026-06-03（14 vs 1）
- **2026-06-04 状态**：99→99 pages（与 06-03 报"96→94"累计增长混淆）；实际 06-04 新建 1 policy + 4 PVE concept = 5 wiki 页
- **根因**：`dream-cycle-wiki-bridge.sh` 累计读 `~/wiki/log.md` 近期行（含跨日增量），把"近期 wiki 增长"误算为"今日 wiki 增长"
- **应对**：
  1. daily log 已在「未完成 / 待跟进」列出"复查 `dream-cycle-wiki-bridge.sh` 累计逻辑"
  2. dream cycle 报告中"Δ pages" + "Δ chunks" 数字**不可直接采信**，须用 `find ~/wiki -name '*.md' -newermt 'YYYY-MM-DD 00:00' ! -newermt 'YYYY-MM-DD 23:59'` 单独验证
- **修复路径**：cron owner 检查 `~/scripts/dream-cycle-wiki-bridge.sh` 增量逻辑

### 5. cron session 第一条 asst 消息常常是空字符串

- **症状**：cron 注入式 user 消息数百到 11k 字符；agent 第一反应是 100 字符内的过渡回复（如 "I'll start by..."），第一条 asst 长度 < 200 字符
- **2026-06-04 实测**：11 个 cron session 中 10 个 `asst[0] = 0`（占 91%）
- **影响**：旧的"读第一条 asst = 成果摘要"假设失效
- **应对**：必须用 `asst[-1]` 读取 cron 任务的成果汇报；如果 `asst[-1] < 100`，再 `asst[-2]` 复核
- **已编码在 SKILL.md 主体**（"Pitfall: cron session 的第一条 assistant 消息常常是空字符串"），本条只作为"实测数据"补充

## 🟢 低优先级（一次性的脚本/格式观察）

### 6. `gbrain` 在 cron 环境下必须 `PATH="$HOME/.bun/bin:$PATH"` 前置

- **症状**：直接 `gbrain put` 报 `command not found`
- **原因**：cron 不读 `~/.bashrc`，用户级 bin 目录不在 PATH
- **应对**：SKILL.md Step 4 已明确，所有 `gbrain` 命令必须带 `PATH=` 前缀

### 7. `embed --stale` 需要 EMBEDDING_BASE_URL 可达

- **症状**：日常 cron 跑 `embed --stale` 偶发失败
- **应对**：日常用 `embed --slugs <slug>` 已验证可用（cron 环境 100% 走通，2-3 chunks）
- **首次编码位置**：SKILL.md Step 4 末尾 "embed 注意事项"

## 跨日 follow-up 模板

每日 daily log 中如果检测到以上任一 P0 信号，必须用以下格式突出显示：

```markdown
## 未完成 / 待跟进

- 🔴 **飞书 webhook 持续失效 XX 小时** — 错误码 19001 token 无效，所有 cron 通知丢失，需重新授权（P0）
- 🔴 **GitHub PAT 视为已泄露** — `~/.hermes/skills/.archive/github-pat-retrieval/` 含真实 PAT，建议立即 revoke
- **hermes-backup.sh 日志写入** — 需加 `exec >> "$LOG_FILE" 2>&1`
- **dream-cycle 累计逻辑 bug** — 报"pages +N"与实际新建不符（与 YYYY-MM-DD 同一类）
```

其中 XX 小时是"自首次发现"累计时长；连续多日要在 daily log 顶部用 `⚠️ P0 跨日持续` 标注。
