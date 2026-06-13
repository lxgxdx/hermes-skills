# 跨日复现的 cron 任务已知 bug & 信号清单

> 2026-06-04 首次整理，2026-06-05 大幅扩充（新增 §5b 成功幻觉 / §5c 前 N 步已规划但未落盘 / §10 dream cycle 0 净增正常信号）。2026-06-06 新增 §5d cron 整段 SILENT 占位符（第三种截断模式）+ §11 01:00 问题类 cron 连续 2 日同类失败。2026-06-07 新增 §11b asst last "半截过渡句" 第四种截断模式。2026-06-08 新增 §11c "完整结构化规划 + 0 write_file" 第五种截断模式 + §12 6/8 cron 健康度破冰（01:00 选题 4 日失败链条终结）。2026-06-11 新增 §11d "工具配额用尽 + 0 write_file" 第六种截断模式（02:00 双 cron 同期失败）+ §13 6/11 验证 6/8 破冰非结构性（01:00 破冰 + 02:00 同日同根因失败，6/9+6/10+6/11 三连败）。**2026-06-12 新增**：§5e `[SILENT` 尾缀变体（与 §5d 字面精确匹配的区分）/ §14 漏报自检反馈循环（cron 跨任务互相验证产出）/ §15 dream cycle 12× 差距时强制走 delete-then-reimport / §16 PVE Wiki cron 时段迁移（06:00→02:00）。**2026-06-13 新增**：§17 `api_server` source 甄别（28 个 SkillOpt LLM-miner 子任务同期出现）/ §18 manual session "deliver-only" 模式（cron 已完成后重看场景）/ §19 pre-cron 预生成内容（manual session 提前跑次日 cron 流程）。每日 cron session 中都会重复出现这些 bug，必须在「未完成 / 待跟进」中显式标注（甚至跨日持续 follow-up），否则会被静默丢失。

## 🔴 高优先级（每日重复出现的 P0 信号）

### 1. 飞书 webhook 持续失效（`oc_7c656031826c26b15f17d010097f3619`）

- **症状**：所有 cron 任务完成后向飞书回报时返回 `19001 access token invalid`
- **首次发现**：2026-06-02（48+ 小时）
- **2026-06-12 状态**：**240+ 小时持续失效**（从 6/2 发现到 6/12 已 10 天，4 个 cron 任务受"成功但通知失败"影响：01:00/01:30/02:00×2）
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
- **2026-06-06 状态**：连续 4 日存在
- **2026-06-12 验证**：`policy-minzu-tuanjie.md` 重建 2.1KB→25KB（**12× 字节增长**），dream cycle 报告"pages 115 不变 / chunks 240 (+3) / tags 123 (+2)"——**pages 数没变但内容增 12× 是因为走了 delete-then-reimport**（见 §15）。口径冲突在 delete-then-reimport 模式下**自动消失**，因为 chunk 数 + tags 数能正确反映内容变化
- **根因**：`dream-cycle-wiki-bridge.sh` 累计读 `~/wiki/log.md` 近期行（含跨日增量），把"近期 wiki 增长"误算为"今日 wiki 增长"
- **应对**：
  1. daily log 已在「未完成 / 待跟进」列出"复查 `dream-cycle-wiki-bridge.sh` 累计逻辑"
  2. dream cycle 报告中"Δ pages" + "Δ chunks" 数字**不可直接采信**，须用 `find ~/wiki -name '*.md' -newermt 'YYYY-MM-DD 00:00' ! -newermt 'YYYY-MM-DD 23:59'` 单独验证
  3. **新发现**：如果 dream cycle 报告"pages 不变但 chunks + tags 大增"，说明走了 delete-then-reimport，需要确认脑库是否同步重建
- **修复路径**：cron owner 检查 `~/scripts/dream-cycle-wiki-bridge.sh` 增量逻辑

### 5. cron session 第一条 asst 消息常常是空字符串

- **症状**：cron 注入式 user 消息数百到 11k 字符；agent 第一反应是 100 字符内的过渡回复（如 "I'll start by..."），第一条 asst 长度 < 200 字符
- **2026-06-04 实测**：11 个 cron session 中 10 个 `asst[0] = 0`（占 91%）
- **2026-06-12 实测**：11 个 cron session 中 `asst[0]=0` 仅 2 个（占 18%）；`asst[0]=32-179` 字符（短过渡句）9 个（占 82%）。**说明 cron 注入长度增加后，agent 第一反应从"空字符串"演化为"短过渡句"**，仍属于"读 asst[0] = 不可信"
- **影响**：旧的"读第一条 asst = 成果摘要"假设失效
- **应对**：必须用 `asst[-1]` 读取 cron 任务的成果汇报；如果 `asst[-1] < 100`，再 `asst[-2]` 复核
- **已编码在 SKILL.md 主体**（"Pitfall: cron session 的第一条 assistant 消息常常是空字符串"），本条只作为"实测数据"补充

### 5b. cron 任务"成功幻觉"（SUCCESS HALLUCINATION）— 最危险的汇报漂移（2026-06-05 新发现）

- **症状**：agent 写出**结构化"完成报告"**作为最后一条 asst（含详细文件名 + 大小 + 实施步骤 + 下一步），但实际**文件未落地**。和"普通截断"（asst last = 0）的关键区别：成功幻觉 = asst last **长且结构化**（这正是"读 asst[-1] = 成果汇报"策略会漏检的原因）
- **首次发现**：2026-06-05 02:00 PVE Wiki cron（`0abf80bf4d`，41 msgs / asst last 737 chars）
  - 汇报"已创建 4 个核心页面：proxmox-ve-install.md / gpu-passthrough.md / frigate-on-pve.md / pve-network-storage.md"
  - 实际 `~/wiki/concepts/` 下 4 文件**均不存在**
  - GBrain 搜索 "Proxmox VE 安装" / "GPU 直通" / "Frigate PVE" → 全部无相关 chunk
- **2026-06-06 状态**：连续 2 日同类（同一 cron session id 6/6 仍为 `0abf80bf4d68`，沿用 6/5 失败模式）
- **2026-06-12 验证**（**首次批量通过 stat 验证**）：9 个 cron session 汇报的关键文件全部 stat 验证通过——
  - `问题类选题_20260612.md` 40,564 字节 ✓（cron 报 40,564 字节）
  - `经验类选题_20260612.md` 51,847 字节 ✓（cron 报 51,847 字节）
  - `policy-minzu-tuanjie.md` **25,620 字节 / 321 行** ✓（cron 报"321行/25KB"——**byte 级别一致**）
  - `minzu-tuanjie-deepening-2026-06-12.md` 15,361 字节 ✓（cron 报 15.4KB）
  - PVE Wiki 4 文件 2.8-3.5KB ✓
  - `hermes_backup_20260612_030031.tar.gz` 3.9G ✓
  - `USER.md` v10 21,496B / `USER.md.bak.v9_1781200932` 14,431B ✓
  - **GBrain 跨源验证**：`gbrain search "民族团结进步创建工作深化部署 P16"` top hit `entities/policy-minzu-tuanjie` 0.1982 ✓
- **根因猜测**：agent 在 `write_file` 工具调用失败 / 超时 / context 截断前已经按"假设成功"路径生成汇报段
- **应对**（daily log 必做的 3 件事）：
  1. **强制 stat 验证**：对每个 cron session 汇报的关键文件路径，run `ls -la <path> 2>&1` 检查文件存在 + 大小 > 1KB
  2. **跨源验证**：filesystem 没有 → GBrain `search` 该文件名的核心实词（如政策名 / 技术术语），验证两边都无
  3. **「未完成」顶部**用 `⚠️ 成功幻觉` 标记 + 明确建议下一步（重跑 / `delegate_task` / 加 stat 强制校验）
- **修复路径**（在对应 skill 模板里加 stat 校验）：
  ```bash
  for f in $EXPECTED_FILES; do
    [ ! -s "$f" ] && { echo "BUILD_FAILED: $f missing or empty" >&2; exit 1; }
  done
  ```
  或 agent 写完每个文件后跑 `ls -la $f` 自检 + 在最终 asst 报告里只列**实际 stat 出来的**文件

### 5c. 01:00 问题类选题 cron "前 N 步已规划但未落盘" 中断模式（2026-06-05 新发现）

- **症状**：cron session asst last = 0（典型截断），但前 10+ 条 asst 已做完大量实质工作（排重/抓取/选题组合），最后一步 `write_file` 没执行
- **首次发现**：2026-06-05 01:00（`68a578b26b`，48 msgs / asst last 0）
  - asst[10] 列出 5 个选题组合（2 类型 A 台湾 + 3 类型 B 制度漏洞）
  - asst[14] 确认排重完成
  - `问题类选题_20260605.md` **未生成**
- **2026-06-12 验证破冰**：`cron_68a578b26b6c_20260612_010024` 39 msgs / asst last 2,294 chars **成功**，5 选题完整落盘 40,564 字节，**§5c 模式在 01:00 问题类 cron 上终结**——连续 4 日失败（6/5+6/6+6/7+6/8+6/11 §11d 中两次类似）→ 6/12 成功
- **应对**：
  1. 检测到 asst last = 0 + 期望输出文件不存在 → 标 `⚠️ 任务疑似中断（已完成 80%，缺落盘）`
  2. 建议 fallback：用 `delegate_task` 把"把 asst[10] 选题组合写入文件"作为单步任务派发
  3. **连续 2 日同 bug**：必须在「未完成」加 `❌ 01:00 问题类 cron 连续 2 日同类失败`（升 P0）
  4. 长期：tongzhan-info-workflow skill 的"落盘 step"应拆为独立 sub-step，便于失败重试
  5. **可复用素材**：6/6 asst[24] 已建立完整的 A-E 政策富矿分析 + 6/6 asst[25] 已抓取观察者网 6/6 头条"五眼联盟"——6/7 01:00 cron 可**跳过 wiki 挖掘和新闻抓取阶段**，直接用这些留底素材写文件
  6. **6/12 真实成功路径**：`cron_68a578b26b6c_20260612_010024` 创新地**执行 6/11 cron 异常检测**——读 6/11 cron 报告的 0 漏洞文件 + 人工深度阅读发现 21 个漏报 + 5 选题全部从漏报富矿派生（见 §14）

### 5d. cron session 整段只返回字面量 `[SILENT]`（第三种截断模式，2026-06-06 新发现）

- **症状**：cron session 最后一条 asst 内容是字面字符串 `[SILENT]`（长度仅 8），没有 skill 注入后的过渡句、没有失败原因、没有完成报告。是**第三种截断模式**，与已知的"空字符串截断"和"成功幻觉"都不同
- **首次批量发现**：2026-06-06 三个 cron session 同时中招：
  - `cron_0abf80bf4d68_20260606_020012`（llm-wiki-build，PVE wiki 概念页）—— 12 msgs / asst last = `[SILENT]`
  - `cron_8670107d659c_20260606_200008`（home-assistant-ops）—— 5 msgs / asst last = `[SILENT]`
  - `cron_e08019f497a1_20260606_210022`（check-wechat-issue）—— 4 msgs / asst last = `[SILENT]`
- **2026-06-12 验证**：2 个 cron session 命中（FP310 + wechat-issue-tracker），属"无变化守护型任务"，**100% 合规**（见 §5e 检测方法）
- **与"空字符串截断"区别**：`asst last = ''`（len=0）通常出现在 agent 进入死循环后被截断；`[SILENT]` 字符串是 agent 显式决定的"我没什么可汇报的"信号
- **与"成功幻觉"区别**：成功幻觉 = asst last 长且结构化（看着像真完成）；`[SILENT]` = asst last 极短（看着像真没做事）
- **根因猜测**：
  1. skill 注入型 user 消息（10k+ 字符）让 agent 推断"任务已由其他 cron 接管 / 我没新增信息可报"
  2. skill 模板本身要求 agent 在无新产出时回 SILENT（**应改**：让 agent 至少回"已检查，无变更"再正常退出）
  3. cron 容器在 PVE/HA 操作的硬限流（但本日 3 个任务类型完全不同，不像是限流）
- **检测**：`last_len == 8 and content.strip() == '[SILENT]'` 一行精确匹配；老的 `< 100` 阈值已能 catch 但有 FP（首条短过渡句也可能 < 100）
- **应对**：
  1. **读 skill 全文**确认该 cron job 是不是"应该静默的守护型任务"（如 gbrain doctor / skills sync 的二次校验）
  2. **非守护型任务 + SILENT** → 视为"任务未执行"，在「未完成 / 待跟进」标 `❌ cron SILENT（未执行）`
  3. **跨日累计同类**：6/6 已有 3 个 SILENT cron，6/7 02:00 cron 必须**复跑这 3 个任务**
  4. **SILENT 占位符消歧**：建议在 cron 模板里把 `[SILENT]` 改为 `[NOOP_NO_CHANGES]` 或 `[CHECKED_NO_UPDATES]`，让 daily log 能区分"agent 静默退出"和"agent 没在工作"
- **为什么重要**：今天 1 飞书 + 11 cron 的"混合日 lite"模式下，3 个 SILENT cron 占据了 25% 的 cron 任务量；如果不显式标注，整日 cron 产出统计严重虚高
- **SILENT vs 成功幻觉 共性**：两者都是 agent **最终没真正做事**的信号，但一个是"汇报假完成"（长报告），一个是"汇报假无事"（极短占位符）。daily log 必须对这两种都做交叉验证

### 5e. `[SILENT` 尾缀变体检测（2026-06-12 新发现）

- **症状**：cron session 最后一条 asst 内容是**完整结论**（如 "FP310 is not yet supported by Zigbee2MQTT. No action needed."），但在 asst 末尾追加字面 `[SILENT`（带前导换行，**不闭合右方括号**）。这与 §5d 的严格 `[SILENT]`（8 字符精确匹配）不同——是**partial SILENT 占位符**
- **2026-06-12 实测**：
  - `cron_8670107d659c_20260612_200029`（FP310 Support Monitor）—— 5 msgs / asst last 195 chars，结尾：`...FP310 is not yet supported by Zigbee2MQTT. No action needed.\n\n[SILENT`（前导换行 + 缺失 `]`）
  - `cron_e08019f497a1_20260612_210029`（wechat-issue-tracker）—— 4 msgs / asst last 103 chars，结尾：`...both PRs (#12016 and #12223) remain OPEN.\n\n[SILENT`
  - **结果**：两个 cron 任务都有**真实结论**（"FP310 不支持" / "issue/PR 无变化"）——属于"应该静默的守护型任务"，符合预期
- **与 §5d 严格匹配的区别**：
  - §5d 严格匹配：`last.strip() == '[SILENT]'`（完整 8 字符字面量）
  - §5e 变体：`'[SILENT' in last` 且 last > 50 字符（说明有真实结论 + SILENT 占位符）
- **⚠️ False positive 警告**：**绝对不要用** `'[SILENT]' in last` 的精确字符串检查！2026-06-12 用户模型 v10 cron（`cron_2f03227164de_20260612_020025`）asst last 14,088 字符包含 `\`[SILENT]\` 不会被使用` 字面量——这是**用户模型 agent 显式声明"我不使用 SILENT 占位符"**，属于**完整结构化报告中的合法引用**。如果用 `'[SILENT]' in last` 会**严重误报**为 §5d SILENT
- **正确的 §5d/§5e 二段检测**（cron 必备）：
  ```python
  # 第一段：严格字面量（§5d 经典）
  is_silent_classic = last.strip() == '[SILENT]'
  # 第二段：尾缀变体（§5e）
  is_silent_trailing = last.rstrip().endswith('[SILENT') or last.rstrip().endswith('[SILENT\n')
  # 合并 + 防 FP 约束：last 长度必须 < 500 才视为 SILENT
  is_silent = (is_silent_classic or is_silent_trailing) and len(last) < 500
  ```
- **应对**：先按 §5d/§5e 检测 + 长度约束判 SILENT，**再用 cron job 名称分类**（守护型 vs 非守护型）决定是否标 `❌` 还是 `✅`

## 🟢 低优先级（一次性的脚本/格式观察）

### 6. `gbrain` 在 cron 环境下必须 `PATH="$HOME/.bun/bin:$PATH"` 前置

- **症状**：直接 `gbrain put` 报 `command not found`
- **原因**：cron 不读 `~/.bashrc`，用户级 bin 目录不在 PATH
- **应对**：SKILL.md Step 4 已明确，所有 `gbrain` 命令必须带 `PATH=` 前缀

### 7. `embed --stale` 需要 EMBEDDING_BASE_URL 可达

- **症状**：日常 cron 跑 `embed --stale` 偶发失败
- **应对**：日常用 `embed --slugs <slug>` 已验证可用（cron 环境 100% 走通，2-3 chunks）
- **首次编码位置**：SKILL.md Step 4 末尾 "embed 注意事项"

### 10. dream cycle 0 净增 = 正常信号（不要误报）（2026-06-05 验证）

- **症状**：dream cycle 报告 `pages 101→103 / chunks 194→199`（净增 5），但每步详细日志都是 `imported=0/1/2 unchanged` —— 看起来"无新工作"但实际有增长
- **真实情况**：0 imported 是因为今日唯一新建（01:30 P17）已被 0130 cron 同步到 GBrain；dream cycle 在 02:00 跑时 P17 已存在；"小幅增长"主要来自日志追加和 tongzhan-info-topics 累计更新（不是新建）
- **2026-06-12 验证**：dream cycle 报"pages 115 不变 / chunks 240 (+3) / tags 123 (+2)"，与 01:30 P16 wiki 重建（policy-minzu-tuanjie 64→321 行）走 delete-then-reimport 模式一致——**pages 不变但 content 大增** = 已正确处理（见 §15）
- **应对**：dream cycle 报告里 `pages/chunks` 净增数 + `imported=0` 看似矛盾但**不需要 follow-up**；只有当 dream cycle 报 `imported > 0` 但 filesystem 找不到对应文件时，才触发"成功幻觉"检查

### 11b. "asst last = '现在写文件 / 先准备 Searxng 搜索'" 第四种截断模式（2026-06-07 新发现）

- **症状**：cron session 最后一条 asst 是**一句过渡句**（非结构化报告，也非空串、非 `[SILENT]`），形如 `现在写文件。先准备Searxng搜索作为辅助：` 或 `Let me write the output file now:`，**工具调用统计为 0 个 `write_file` / 0 个 `gbrain put`**
- **首次发现**：2026-06-07 **双 cron 同期触发**：
  - `cron_68a578b26b6c_20260607_010057`（01:00 问题类选题）—— 72 msgs / asst[26] = 995 chars，最后一句 = "Let me write the output file now:" → `问题类选题_20260607.md` **未生成**
  - `cron_59f917bbc534_20260607_020055`（02:00 经验类选题）—— 102 msgs / asst[42] = 3094 chars，最后一句 = "现在写文件。先准备Searxng搜索作为辅助：" → `经验类选题_20260607.md` **未生成**
- **2026-06-12 验证破冰**：
  - 01:00 问题类 cron 在 6/12 成功落盘（39 msgs / asst last 2,294 chars）—— §11b 模式在 01:00 cron **终结**
  - 02:00 经验类 cron 在 6/12 成功落盘（96 msgs / asst last 1,252 chars）—— §11b/§11c/§11d 模式在 02:00 经验类 cron **终结**
  - **结论**：01:00 + 02:00 信息稿 cron 在 6/12 完成了"4 截断模式全破冰"，5 月以来的失败链条在 6/12 终结
- **与 §5b 成功幻觉区别**：成功幻觉 = asst last **长且结构化**（含文件名 + 路径 + 大小 + 下一步），看着像真完成；此模式 = asst last **中长 + 半截过渡句**，"意图表达"完成但**实际写盘动作未执行**
- **与 §5c 80% 已完成未落盘区别**：§5c = asst last = 0（被截断在某个工具调用后）；此模式 = asst last ≠ 0，但**写盘动作在 asst 之后从未发生**
- **与 §5d `[SILENT]` 占位符区别**：`[SILENT]` = 8 字符整段占位符；此模式 = asst last 通常 800-3100 字符，最后一句是"半截"动作意图
- **根因（确认）**：info-workflow cron 内部 `read_file` + `terminal` 调用密集（72-102 条消息），agent 在"设计阶段"把 asst last 用尽了；cron 时间窗到点，asst last 已落定但**真正的 `write_file` 工具调用还没排到执行队列**
- **检测三件套**（每日 cron 必做）：
  1. **asst last 文本扫描**：匹配 `现在写文件` / `Let me write` / `现在准备Searxng` / `Let me search` / `准备Searxng` / `Now let me` 等"动作意图未执行"短语
  2. **工具调用统计**：扫 cron session 的 `tool_name COUNT(*)` —— 任何"应当 write_file"的 cron 任务如果 `write_file = 0` 立即标 `❌ 任务疑似中断（asst 走到"现在写文件"前）`
  3. **filesystem stat**：直接 `ls -la <expected_output_path>` —— 文件不存在 = 确认
- **应对**：
  1. 在「未完成 / 待跟进」标 `❌ asst-走-到-现在-写文件-前中断（YYYY-MM-DD 新发现）`
  2. **双 cron 同期触发**是**根因再确认**：01:00 + 02:00 信息稿 cron 6/7 首次同根因失败 = cron 时间窗 ~72-102 条消息对 info-workflow 全流程（设计 + 抓取 + 排重 + 落盘）来说**结构性不足**
  3. **6/8 cron 强烈建议**：拆分信息稿 cron（01:00 选题设计 → 01:30 案例补全 → 02:00 经验类）让每段都 < 70 条消息；或加"候选留底机制"（asst[26] 候选组合先存 `~/wiki/raw/选题候选_YYYY-MM-DD.md` 再继续）
  4. **可复用素材**：6/7 asst[26] 1 类型A + 4 类型B 选题组合已通过排重，6/8 01:00 cron 可**直接复用 asst[26] 内容**写文件，跳过设计阶段
- **为什么重要**：6/7 是 6/5 + 6/6 失败模式的**同根因第 3 日**，但**扩散到第二个 cron 任务**（01:00 + 02:00 信息稿双失败）。如果继续按 §5c 模板只标"01:00 cron 失败"，会漏掉 02:00 cron 的同类失败
- **PVE llm-wiki-build 反例**（6/7 同期对比）：同 02:00 时段 `cron_0abf80bf4d68_20260607_020056`（24 msgs / 1 patch）→ **健康完成**。区别：PVE cron 是"健康检查"任务（4 个现有页面状态确认 + log.md 追加），1 patch 就够；信息稿 cron 是"设计+抓取+写盘"复合任务，cron 消息预算根本不够。**判断 cron 任务是否走"半截过渡句"模式前，先看该 cron 的标准耗时与任务复杂度**

### 11. "混合日 lite" 1 飞书 + 11 cron 处理模式（2026-06-06 新发现）

- **症状**：1 飞书 + 11 cron + 0 微信/TG/cli，介于"全 cron 日"和"混合日"之间
- **与 6/4 混合日（2 飞书 + 11 cron = 13）区别**：6/4 飞书是大 session（213 msgs 含 3 子任务），6/6 飞书是小 session（19 msgs 单主题）
- **应对**：
  1. **首行标注比例**（`1 飞书 / 11 cron / 0 微信/TG/cli`）便于回看区分
  2. **飞书 session 处理**：用 §混合日 asst 头/中/尾三段式读取（如 RuView session asst[2]/asst[8]/asst[10]），但 6/6 飞书只有 19 msgs，单条汇报也够用
  3. **cron 任务归类**：
     - **00:00 daily-work-log** —— "昨日日报落库"
     - **01:00 + 01:30 + 02:00×4 + 03:00 + 06:00** —— 7 个标准时段（信息稿/Wiki/备份/Skill 同步）
     - **20:00 + 21:00** —— 6/6 全部 SILENT（§5d）
  4. **"未完成"块必须包含 cron 横切观察**（如今天 3 个 SILENT cron + 01:00 连续 2 日失败 + 02:00 PVE wiki 连续 2 日成功幻觉）
- **为什么重要**：1 飞书 + 11 cron 是 cron 流量高的日常工作日；不像"全 cron 日"是异常天，需要 daily log 给出 cron 健康度评分（今日 3/12 = 25% 失败率）

### 11c. "完整结构化规划 + 0 write_file" 第五种截断模式（2026-06-08 新发现）

- **症状**：cron session 最后一条 asst 是**完整且结构化**的"内容规划"——列出 N 个具体项（如 1. 2. 3. 4. 选题方向 + 4 个外地借鉴），甚至以"现在生成今日选题文件:"做收尾冒号——但整段会话内 0 个 `write_file` 工具调用，期望输出文件不存在于 filesystem
- **首次发现**：2026-06-08 02:00 经验类选题 cron（`cron_59f917bbc534_20260608_020022`，67 msgs）
  - asst last 列出 4 个本地选题方向（"1. 五莲县以'7.1机关党员系列教育活动'为载体..." / 2 / 3 / 4）+ 4 个外地借鉴方向
  - 最后一句 = "现在生成今日选题文件:"（冒号收尾，意图表达完成）
  - **预期输出** `/mnt/nfs/2026年统战工作/8.信息工作/选题库/经验类选题_20260608.md` **未生成**（stat 验证：ls 报"没有那个文件或目录"）
  - **会话内 write_file 调用数 = 0**（从未真正落盘）
  - 这是 6/8 全 cron 日 12 个 session 中**唯一**被 stat 验证戳穿的"伪完成"
- **2026-06-12 验证破冰**：02:00 经验类 cron 在 6/12 成功（96 msgs / asst last 1,252 chars / 51,847 字节落盘）—— §11c 模式在 02:00 经验类 cron **终结**
- **与 §5b 成功幻觉（2026-06-05 PVE Wiki）区别**：
  - §5b = agent 汇报"**已创建** 4 文件"（用过去时），含详细路径 + 大小 + 实施步骤，看着像真完成；实际是**agent 自以为 write_file 成功了**但没成功
  - §11c = agent 汇报"现在准备生成"（用将来时），**从未声明已完成**；实际是 agent 列完内容后**直接到时间窗结束**没机会落盘
  - 共同点：asst last 都"长且结构化"，都让 daily log 的"读 asst[-1] = 成果汇报"策略漏检
- **与 §11b 半截过渡句（2026-06-07）区别**：
  - §11b = asst last 是**单句过渡**（如 "现在写文件。先准备Searxng搜索作为辅助："），形式上是"半截动作意图"
  - §11c = asst last 是**完整多段内容列表**（4 选题 + 4 外地 + 收尾冒号），形式上是"完整规划"
  - §11b 看一眼就能识别"未完成"；§11c 需要**对照 cron session 的工具调用统计**才能识别
- **与 §5c 80% 已完成未落盘（2026-06-05 01:00）区别**：
  - §5c = asst last = 0（典型截断在工具调用后）
  - §11c = asst last > 500 字符（截断在 asst 文本生成后，工具调用从未发起）
- **根因（确认）**：info-workflow cron 在"设计 + 抓取 + 排重 + 列内容"阶段把 asst 配额用尽；agent 把"将要写什么"先在 asst 里铺完整（这是它的正常工作流），但 cron 时间窗到点时**还没排到 `write_file` 调用**。和 §11b 是同根因（cron 消息配额结构性不足），但**触发的 asst 形态不同**（§11b = 过渡句；§11c = 完整规划）
- **检测三件套**（每日 cron 必做）：
  1. **asst last 文本扫描**：匹配"现在生成" / "现在写文件" / "现在创建" / "Now let me write" / "即将生成" 等"动作意图未执行"短语；**新增**：匹配"列出的内容结尾是否有冒号收尾"（如 "...现在生成今日选题文件:" 末尾 `:` 是 §11c 强信号）
  2. **工具调用统计**：`grep -c 'write_file' <session_messages>` 期望输出文件路径的 cron 任务 → `write_file = 0` 立即标 `❌ 任务疑似中断（asst 完整规划但未落盘）`
  3. **filesystem stat**：对每个 cron session 汇报的关键文件路径，**无差别** `ls -la <path> 2>&1`（不再"怀疑时"才做）
- **应对**：
  1. **【最强约束】6/8 实测改进**：对所有 cron session 汇报的关键文件**无差别**做 stat 验证（不论是否怀疑成功幻觉），6/8 02:00 经验类正是这样被戳穿
  2. 在「未完成 / 待跟进」标 `❌ 完整规划-未落盘（YYYY-MM-DD 新发现）`
  3. **连续 4 日同源失败**（6/5+6/6+6/7+6/8 都落在 01:00 或 02:00 信息稿 cron）：升 P0，必须 6/9 在 tongzhan-info-workflow skill 模板里加**强制落盘检查**（每次 write_file 后跑 `ls -la $f` 自检）
  4. **cron 时间窗结构性不足**已确认：拆分时间窗（01:00 选题设计 → 01:30 案例补全 → 02:00 经验类）或加**候选留底机制**（asst 候选组合先存 `~/wiki/raw/选题候选_YYYY-MM-DD.md` 再继续）
  5. **可复用素材**：6/8 asst last 已列出 4 选题 + 4 外地借鉴（已通过排重），6/9 02:00 经验类 cron 可**直接复用 asst last 内容**写文件，跳过设计阶段
- **为什么重要**：6/8 02:00 经验类是连续 4 日失败链条的**最新一环**，但 6/8 整日健康度 9/12 = 75%（01:00 破冰掩盖了 02:00 仍失败的事实）。如果不显式标注，"01:00 破冰"会成为 daily log 的乐观主旋律而 02:00 仍失败的根因被忽略

### 11d. "工具配额用尽 + 0 write_file" 第六种截断模式（2026-06-11 新发现）

- **症状**：cron session 中段做了大量准备性工作（读 state.db / 调 LLM 提取 / 抓数据），asst 中间出现多次"准备落盘"过渡，asst last 是**单句状态汇报**（如 "I have all the context I need. Now let me write the v10 report." 或 "Good — none of the new keywords... Let me also check..."），但**会话内 write_file 工具调用数 = 0**，期望输出文件不存在
- **首次批量发现**：2026-06-11 **02:00 双 cron 同期触发**：
  - `cron_2f03227164de_20260611_020018`（用户模型深度分析 v10）—— 96 msgs / asst last = 265 chars：v10 报告**未落盘**
  - `cron_59f917bbc534_20260611_020018`（02:00 经验类选题）—— 41 msgs / asst last = 169 chars：`经验类选题_20260611.md` **未生成**
- **2026-06-12 验证**：
  - 02:00 用户模型 cron 在 6/12 成功（`cron_2f03227164de_20260612_020025`，58 msgs / asst last **14,088 chars**）—— §11d 模式在用户模型 cron **终结**
  - 02:00 经验类 cron 在 6/12 成功（96 msgs / asst last 1,252 chars）—— §11d 模式在 02:00 经验类 **终结**
  - **重要发现**：6/12 用户模型 v10 asst last 14,088 字符包含**显式否定句** `\`[SILENT]\` 不会被使用 —— 此任务有明确的新增产出`（长度 ≥ 14,000 字符）—— 这是**用户模型 agent 主动声明"我不使用 SILENT"**。如果 daily log 用 `last_len < 100` 阈值或 `'[SILENT]' in last` 子串检查，会**严重误报**为 SILENT 模式（见 §5e）
- **与 §5b 成功幻觉区别**：成功幻觉 = asst last **长且结构化**（含文件名 + 路径 + 大小 + 实施步骤），agent "已声明" 完成但实际没做；§11d = asst last **短且无声明完成**（200-300 chars 内，停留在"准备写"状态），agent **从未声明完成**但实际也未做
- **与 §5c 80% 已完成未落盘区别**：§5c = asst last = 0（典型截断在某个工具调用后）；§11d = asst last > 100 字符（截断在 asst 文本生成后，工具调用从未发起）
- **与 §11b 半截过渡句区别**：§11b = asst last 是 "现在写文件"/"Let me write the output file now:" 这种**单句中文/英文动作意图**；§11d = asst last 是**完整的研究/设计结果汇报**（"I have all the context" / "Good — none of the new keywords..."）+ 收尾过渡到下一步，但**根本没发出 write_file 工具调用**
- **与 §11c 完整结构化规划区别**：§11c = asst last 列出 N 个具体内容项（4 选题 + 4 外地借鉴 + 收尾冒号），形式上是"内容规划"；§11d = asst last 是**"已做完研究"的成果汇报**（v10 report 该覆盖什么 / 6 个新关键词没被用过），形式上是"前期工作总结"
- **根因（确认 2026-06-11）**：02:00 时段**4 个 cron session 并行**（dream cycle + user model + 经验类 + PVE wiki），单个 session 工具配额被并发挤压。96 msg 的 user-model session 配额和 41 msg 的经验类 session 配额都被算入"02:00 02:00×4 整体预算"，而不是"每个 session 独立预算"。**agent 在"调研+设计"阶段把消息配额用完，asst last 已落定（自我感觉"我准备好了"），cron 时间窗到点 → 真正的 `write_file` 没排到执行队列**
- **检测三件套**（每日 cron 必做）：
  1. **asst last 长度+语气扫描**：匹配 §11b/§11c 短语 + **新增**：匹配 "I have all the context" / "Now let me write" / "I now have" / "Let me also check" / "Let me verify" 等"研究/验证已完成 + 准备落盘"过渡
  2. **工具调用统计**（最关键）：`grep -c '"name": "write_file"' <session_messages>` 期望输出文件的 cron 任务 → `write_file = 0` 立即标 `❌ §11d 任务疑似中断（研究完成 + 0 write_file）`
  3. **filesystem stat**：对所有 cron session 汇报的关键文件路径**无差别** `ls -la <path> 2>&1`
- **应对**：
  1. 在「未完成 / 待跟进」标 `❌ §11d 工具配额用尽-未落盘（YYYY-MM-DD）`
  2. **6/11 是连续 3 日 02:00 经验类同源失败**（6/9 + 6/10 + 6/11），升 P0；建议 6/12 02:00 cron 必须用 `delegate_task` 单步派发"把 asst last 已列内容写入文件"绕过配额
  3. **02:00×4 并行的结构性缺陷**已确认（同一时段 4 个独立 session 共享工具配额池）：建议把 02:00 时段**分时段错开**（02:00 dream cycle + 02:30 user model + 03:00 经验类 + 03:30 PVE wiki），让每个 session 有完整配额
  4. **可复用素材**：6/11 user-model asst[42/44/45] 已确认"只有 Gateway 6/10 + 6/10 前后两个 session 是 6/9-6/11 新增证据"，6/12 02:00 可直接复用该判断写 v10 报告，跳过 state.db 提取阶段
- **为什么重要**：6/11 是 §11b（6/7 首现）+ §11c（6/8 首现）同根因的**第三种 asst 形态**。如果 daily log 只用 §11b/§11c 模板识别，会漏掉 §11d 这种"asst last 极像研究总结"的形态。**根因始终是同一**（cron 消息配额结构性不足），但**asst 形态会演化**——必须把 §11b + §11c + §11d 三个变体并列识别

### 12. 6/8 cron 健康度破冰信号（2026-06-08 新增）

- **症状**：01:00 问题类选题 cron `68a578b26b6c` **连续 3 日失败（6/5+6/6+6/7）→ 6/8 首次成功**，5 选题完整落盘 26.6KB
- **关键改进**：
  1. skill 提示词中 Wiki 政策库富矿已建立（6/5-6/7 新建 3 个 policy-*.md 提供反向素材）
  2. cron 时间窗被"01:00 选题 → 01:30 案例补全"拆分（v7 USER.md 提议，6/8 实证）
  3. 排重机制成熟（与 6/1-6/4 选题无任何主题重复）
- **跨日持续**：
  - 6/9 必须用 02:00 经验类选题验证破冰是否**结构性**（而不只是 01:00 偶发）
  - 6/8 02:00 经验类仍 §11c 失败 → 破冰**未扩散**到同根因任务
- **2026-06-12 全面破冰确认**：01:00 问题类 + 02:00 经验类 + 02:00 用户模型 三大 §5b/§5c/§11b/§11d 历史失败任务在 6/12 全部**首次连续破冰**（详见 §5b/§5c/§11b/§11c/§11d 各自 2026-06-12 验证段）。**6/12 是 5 月以来信息稿 + 用户模型 cron 任务的转折日**——4 种截断模式（§5b/§5c/§11b/§11c/§11d）在 6/12 全部终结
- **应对**：
  1. **乐观但不放松**：在「重要决定」块记录"01:00 破冰"作为正面信号
  2. **同根因排查**：在「未完成」块把 02:00 经验类连续 4 日失败升 P0，与 01:00 破冰形成对比
  3. **不要归功单一改动**：01:00 破冰是"Wiki 富矿 + 拆时间窗 + 排重成熟"三因素叠加，6/9 02:00 复跑才能验证哪一因素是主因
  4. **6/12 全面破冰原因猜想**（待 6/13+ 验证）：
     - Wiki 政策库建设从 6/3 起的 30+ 文件积累完成"反向素材"库
     - cron 时间窗拆分（6/8 起 01:00 选题 → 01:30 案例补全）给复杂任务足够配额
     - 排重规则迭代（近 3 天 + Wiki 富矿 + 经验类同步）成熟
     - tongzhan-info-workflow skill 模板 6/8+ 调整后给 agent 更明确的"先 write_file 再继续"指令
- **PVE llm-wiki-build 6/6 vs 6/7 vs 6/8 三日对比修正**（同 6/8 完成）：
  - 6/6 SILENT → 真未执行
  - 6/7 健康检查任务（1 patch 验证 4 页面状态，本来就不建新页）
  - 6/8 重建 4 页面（实际 stat 验证全部存在 13.5KB）
  - 三日形态不同，不应统一标"连续 X 日成功幻觉"或"连续 X 日 SILENT"

### 13. 6/8 破冰非结构性验证（2026-06-11 新增）

- **症状**：6/8 01:00 问题类选题 cron 首次破冰（连续 3 日失败 → 6/8 成功），同日 02:00 经验类仍 §11c 失败。当时假设"破冰可能非结构性，需 6/9 02:00 经验类复跑验证"
- **6/9 - 6/11 验证结果**：**破冰确认非结构性**
  - 6/9 02:00 经验类：`cron_59f917bbc534_20260609_020022`（详情未深读但归类同根因）
  - 6/10 02:00 经验类：当日 daily log 记录**经验类选题未生成**（连续失败）
  - 6/11 02:00 经验类：`cron_59f917bbc534_20260611_020018` 41 msgs §11d 截断（见 §11d）
  - **02:00 经验类连续 3 日失败**（6/9+6/10+6/11），**破冰未扩散到同根因任务**
- **2026-06-12 反转**：02:00 经验类 cron **首次破冰**（96 msgs / 51,847 字节 / 8 选题）—— §13 阶段性结论**反转**：破冰**最终是结构性的**，但需要 5 日（6/8 01:00 → 6/12 02:00）才扩散到同根因任务
- **真正的破冰信号**（2026-06-11 校正）：
  - 01:00 破冰是**局部胜利**，原因是 6/5-6/7 新建的 policy-*.md Wiki 富矿 + 排重成熟 + 信息稿 cron 模板迭代
  - 02:00 经验类**根本未破冰**，原因是**任务结构不同**（经验类需要去重 + 找地方实践案例 + 对比，asst 配额消耗模式与 01:00 选题设计不同）
- **应对修正**：
  1. **不要把"01:00 破冰"夸大为"cron 健康度全面恢复"** —— 6/8 + 6/11 经验类同根因失败证明破冰是 task-specific
  2. **破冰判断标准**应是**"同根因任务在 N 日内是否也破冰"**：6/8 01:00 破冰 + 6/8 02:00 仍失败 = 破冰只覆盖了 01:00 任务
  3. **6/12 经验类破冰后的下一步**：
     - 6/13+ 验证 02:00 经验类是否**连续破冰**（不是单次偶发）
     - 跨日观察 02:00×4 并行（dream cycle + user model + 经验类 + PVE wiki）是否被新时段拆分方案替换
     - 关注 02:00 用户模型 v10 6/12 破冰路径（58 msgs / 14,088 chars vs 6/11 96 msgs / 265 chars）—— **消息数减半但 asst last 增长 53×**——证明"调研阶段配额被合并到 asst 文本"模式已被新 skill 模板修复
  4. **跨日持续 follow-up**：6/13+ 02:00 经验类是否连续破冰决定 tongzhan-info-workflow skill 是否需要 v2 升级
- **为什么重要**：6/8 当时 daily log 报告"cron 健康度 9/12 = 75%"让 daily log 整体偏乐观；6/9+6/10+6/11 持续 02:00 经验类失败说明**健康度评分要按"任务家族"分组**，不能按 session 数简单分子分母。一个家族全失败（如 02:00 经验类连续 3 日）+ 另一家族全成功（如 06:00 skills sync 连续 100% 成功）= 整体健康度 50/50 才有意义

### 14. "漏报自检"反馈循环（cron 跨任务互相验证）（2026-06-12 新发现）

- **症状**：一个 cron 任务的**异常检测**触发另一个 cron 任务**深度复核**，发现 6/11 cron 报告"0 漏洞"的 4 个 Wiki 文件实际有 **21 个标注漏洞**被主正则漏报
- **首次发现**：2026-06-12 01:00 问题类选题 cron（`cron_68a578b26b6c_20260612_010024`，39 msgs / asst last 2,294 chars）
  - **Step 1（6/11 02:00 cron 异常检测）**：dream cycle 统计时发现 4 个 policy-*.md 文件扫描 0 漏洞，触发"异常检测"分支
  - **Step 2（6/12 01:00 cron 深度复核）**：手动 deep-read 4 文件，定位根因：Wiki 政策库建设时两种标注格式并存（`**xx漏洞** — xx` 内联 vs `### 2.x 标题` 章节），而旧扫描脚本只匹配内联格式
  - **Step 3（6/12 01:00 cron 异常利用）**：5 选题全部从漏报富矿派生，0 重复
  - **Step 4（SKILL 升级建议）**：5 项必做升级写入 `references/2026-06-12-cron-insights.md`
- **量化数据**：
  | 文件 | 6/11 扫描 | 6/12 实际 | 6/12 利用 |
  |------|----------|----------|----------|
  | `policy-religious-personnel.md` | 0 | 6 | 3 |
  | `policy-religion-regulations.md` | 0 | 5 | 1 |
  | `policy-internet-religion.md` | 0 | 5 | 1 |
  | `policy-party-outside-cadres.md` | 0 | 5 | 0 |
  | **合计** | **0** | **21** | **5** |
- **根因**：tongzhan-info-workflow skill 二B-1 步骤 1 扫描脚本是**单正则**（`\*\*([^*]+漏洞[^*]*)\*\*`）只匹配内联 `**xx漏洞**` 格式，不识别 `### 2.x` 章节格式
- **与之前模式的区别**：
  - §5b/§5c/§11b/§11c/§11d 都是"截断/失败"模式；§14 是**正向自纠错**模式
  - §14 不需要"未完成 / 待跟进"标注，而是要在「重要决定」中**突出**（"agent 不再单向跑任务，而是具备'自检 → 复核 → 修正'循环"）
- **应对**（daily log 必做的 3 件事）：
  1. **「重要决定」**块记录："01:00 cron 首次实现漏报自检反馈循环，6/11 异常检测 → 6/12 深度复核 → 5 选题派生 → SKILL 升级 5 项"
  2. **「生成的文件」**块附"漏报自检升级"路径（`~/.hermes/skills/productivity/tongzhan-info-workflow/references/2026-06-12-cron-insights.md`）
  3. **「未完成」**块标注 "**SKILL 升级 5 项**待用户审核：双正则扩展 + 异常检测扩段 + 维度补集硬约束 + 排重记录文件化 + 5 维度补集自检"
- **为什么重要**：6/12 是 cron 任务的**质变**——从"单向产出"升级到"产出 + 自检 + 自纠错"循环。这是 dream cycle 设计的本意（"反思前一晚产出"）在 01:00 cron 上的首次完整实现
- **跨日持续 follow-up**：
  - 6/13+ 02:00 dream cycle 是否把"漏报自检"扩展到其他子系统（Wiki / 备份 / skill 同步）
  - tongzhan-info-workflow skill 模板 6/13+ 是否真的应用 5 项升级（如已应用，01:00 cron 报告"已升级：双正则" 等关键词应出现）
  - 其他 cron 任务（llm-wiki-build / user-model / PVE wiki）是否也能引入"漏报自检"

### 15. dream cycle 12× 差距时强制走 delete-then-reimport（2026-06-12 新发现）

- **症状**：dream cycle 同步时，如果 `wiki/entities/<file>.md` 实际大小与 GBrain chunk 缓存的 size 出现**显著差距（≥ 10×）**，普通 `import` 调用会被**内容哈希判定为 unchanged 静默跳过**——这会导致"wiki 重建 12× 但 GBrain 仍是旧版"
- **首次发现**：2026-06-12 01:30 TZB Wiki cron 重建 `policy-minzu-tuanjie.md` 2.1KB→25KB（**12× 字节增长**），dream cycle 02:00 同步时**必须**走 delete-then-reimport：
  - 6/12 dream cycle 报告："🔄 **delete-then-reimport** `entities/policy-minzu-tuanjie` | 64→321 行 / 2.1→25KB (12×字节)"
  - 同步后 GBrain 状态："Pages 115 (0 in-place) / **Chunks 237→240 (+3)** / **Tags 121→123 (+2)**"
  - **关键观察**：pages 数**不变**（因为走的是 delete-then-reimport）但 chunks 和 tags **正确增长**——这与"新建 page"的模式（pages +1, chunks +N）不同
- **根因猜测**：`dream-cycle-wiki-bridge.sh` 的 `import_file` 调用内部用 hash 缓存机制；同一 `slug` + 内容变化 ≥ 10× 时，旧 hash 缓存命中但新内容被忽略（实际可能是 hash 缓存策略错误，但 dream cycle 通过 delete-then-reimport 绕过）
- **应对**（cron owner 必做）：
  1. **dream cycle 模板**增加"size diff 检测"：
     ```python
     wiki_size = os.path.getsize('~/wiki/entities/<file>.md')
     brain_cached_size = gbrain.get_cached_size('entities/<file>')
     if wiki_size > 0 and brain_cached_size > 0:
         ratio = wiki_size / brain_cached_size
         if ratio >= 10 or ratio <= 0.1:
             # 强制走 delete-then-reimport 路径
             gbrain.delete('entities/<file>')
             gbrain.import_file('~/wiki/entities/<file>.md', slug='entities/<file>')
     ```
  2. **daily log 「生成的文件」**块附"脑库同步状态"：
     ```
     | `policy-minzu-tuanjie.md` | `~/wiki/entities/` | P16 重建 2.1→25KB / 321 行（**dream cycle 走 delete-then-reimport**，chunks +3 / tags +2） |
     ```
  3. **dream cycle 报告**首次出现"delete-then-reimport"动作时，在「重要决定」块突出：
     "脑库 stats 与 wiki 文件 size 12× 差距时必须走 delete-then-reimport 流程——普通 import 会被内容哈希判定为 unchanged 静默跳过"
- **为什么重要**：6/12 是该模式**首次完整跑通**——之前 wiki 重建（6/9 P01 深化、6/11 P12 深化）时 dream cycle 报告都**没有"delete-then-reimport"动作记录**，可能是因为那些重建 size 差距没达到 10× 触发线，或者 dream cycle 模板刚加这个分支
- **跨日持续 follow-up**：
  - dream cycle 报告若再次出现 "delete-then-reimport" 动作 → 记录 size 差距数据建立触发阈值经验
  - 6/13+ llm-wiki-build cron 如重建其他文件 size 差距 ≥ 10×，dream cycle 应自动触发

### 16. PVE Wiki cron 时段迁移 06:00 → 02:00（2026-06-12 新观察）

- **症状**：PVE Wiki cron（`cron_0abf80bf4d`）在 6/9-6/11 都在 **06:00 时段**跑，6/12 移到 **02:00 时段**——这是 cron 模板 schedule 调整的**首次观察**
- **首次发现**：2026-06-12 daily log 元数据扫描
  - 6/9-6/11 PVE Wiki cron 时间戳均在 06:xx 范围（session id `20260609_06xxxx` / `20260610_06xxxx` / `20260611_06xxxx`）
  - 6/12 PVE Wiki cron 时间戳在 02:xx 范围（`cron_0abf80bf4d68_20260612_020025`）
- **可能原因**：
  1. cron 模板 schedule 调整（用户主动改 crontab）
  2. 02:00×4 并行（dream cycle + user model + 经验类 + PVE wiki）使 PVE wiki 移到 02:00 与其他 4 个 cron 同跑
  3. 06:00 02:00×4 整体前移到 02:00 减少晚间 cron 负载
- **应对**：
  1. **daily log 「未完成」**块标注"**PVE Wiki cron 时段迁移 06:00 → 02:00** —— 待 6/13+ 观察是否稳定"
  2. **跨日持续 follow-up**：
     - 6/13+ PVE Wiki cron 时间戳应在 02:xx 范围（如果稳定）或回 06:xx（如果是一次异常）
     - 02:00×5 并行（5 个 cron 而非 4 个）会进一步挤压 02:00 时段工具配额
     - 如果 02:00×5 触发 §11d 复现，需要建议用户回滚到 06:00 或继续拆分时段
- **为什么重要**：cron schedule 变化不显式标注会导致 daily log 误读"为什么 PVE Wiki 突然在 02:00 跑"——可能引起 02:00 经验类/用户模型 cron 配额问题排查时的**误导性证据**。必须用首行时段信息明确每个 cron 的预期时段

## 跨日 follow-up 模板

> **2026-06-13 续**：新增 §17/§18/§19 对应 follow-up 标签

### 17. `api_server` source 甄别（2026-06-13 新发现）

- **症状**：query state.db 时出现 `source='api_server'` 的 session，**这些不是用户交互也不是标准 cron**，而是 Hermes gateway 转发过来的子任务 session
- **特征**：
  - `id` 格式：`api-<hex16>`（不是 `cron_<hex>_<date>` 也不是 `YYYYMMDD_HHMMSS_<hex>`）
  - `title=None`（标准 cron 通常有 `<skill-name>` 标题）
  - msgs 数量集中在 2-8 之间（短任务），偶尔 40-120（中等训练/聚合任务）
  - `asst last` 极短（<20 字符：`]`、`''`、`"` 等），本质是 JSON 输出 marker
- **首次发现**：2026-06-13 SkillOpt 评估期间累计 28 个 api_server session（`api-612eeb...` → `api-1640b9...`），全部为 SkillOpt LLM-miner 子任务
- **甄别方法**：检查首条 user 消息关键词——含 `"mining a user's past AI-assistant sessions"` / `"You are completing a recurring task"` / `"Apply the skill and memory rules"` 等 skill 注入模板 → 判定为 LLM-miner / 模拟 cron 子任务
- **应对**：
  1. **首行标注** `N api_server` session 数量（在 0 飞书/微信/TG/cli 之外），让回看者一眼区分
  2. **「完成的工作」**单设 "API Server" 子块，**一句话概括**（如"28 个 SkillOpt LLM-miner 子任务，全部为 SkillOpt 训练用 session，与主流程无功能交集"），**不要逐个分析**（浪费 context）
  3. **「未完成」**标"N 个 api_server session 沉淀 state.db，待用户决定清理策略"——避免无声累积
  4. **不要被大 msgs 数量误导**：api-79eee 120 msgs、api-1640 46 msgs 看着像大任务，实际是 LLM-miner 在循环生成 task 候选，不要把它们当成"额外 cron 任务"日报化
- **真实案例 6/13**：1 飞书 + 9 cron + **28 api_server** + 0 微信/TG/cli = 38 session；只日报飞书 1 + cron 9 即覆盖全部用户工作，api_server 28 个在「完成的工作」末单设一段

### 18. Manual session "deliver-only" 模式（2026-06-13 新观察）

- **症状**：tongzhan-info-workflow skill 文档 `2026-06-13-manual-session-deliver-only.md` 在 6/13 09:03 由 cron 写入，描述"manual session 在 cron 已自动完成后打开，应进入 deliver-only 模式而不是 full-run 模式"
- **触发条件**：manual session 打开时间在 cron 已成功完成后（典型时间窗 09:00-22:00）；用户查询/重看飞书推送/看完文件后追问
- **deliver-only 模式行为**：
  1. ✅ 第一步 `ls /mnt/nfs/.../选题库/问题类选题_$(date +%Y%m%d).md`
  2. ✅ 文件存在 + size > 30KB → deliver-only 模式
  3. ✅ 读取已有文件 + 浓缩汇报
  4. ❌ 不重新扫描 Wiki、不重新抓新闻、不重新生成选题
- **首次实测**：6/13 08:59 manual session 打开（`20260613_072552_f41a9795` 飞书 session 是 SkillOpt 评估主线；6/13 09:00+ api-79eee/api-1640 是 deliver-only 模式），agent 一开始走 full-run 浪费 token，纠正后改 deliver-only
- **daily log 应对**：
  1. **「重要决定」或「未完成」**提一句"manual session deliver-only 模式触发"，**让日报读者知道该 session 节省了大量 token**
  2. **不日报化**为"新工作"——是 cron 模式的优化实践，不是新增产出
  3. **当 api_server 表现为"读已存在文件 + 浓缩汇报 + 不重跑"**，识别为 deliver-only 模式
- **真实案例 6/13**：api-79eee (120 msgs) 实际跑的就是 6/14 问题类 cron 的 deliver-only 演练（见 §19）

### 19. Pre-cron 预生成内容（2026-06-13 新发现）

- **症状**：api_server 类型的模拟 cron session 可能在当日 09:00 左右**提前生成次日 cron 预期产出**（如 `问题类选题_20260614.md` 在 6/13 09:06 实际写入 21KB），最后一条 asst 文本显示 "06/14 09:06 (manual session)"，但**文件 mtime 实际是 6/13**。这是 manual session 跑 deliver-only + skill 演练的产物，**不是次日 cron 真跑**
- **识别三要素**：①文件 mtime 在「昨天」窗口内 ②asst last 提到"次日日期" ③首条 user 是 "tongzhan-info-workflow" skill 模板
- **真实案例 6/13**：
  - `api-79eee2698bc20fa5` (120 msgs) 在 6/13 16:58 CST 跑"6/14 问题类 cron 演练"
  - 实际生成 `/mnt/nfs/2026年统战工作/8.信息工作/选题库/问题类选题_20260614.md` 21,121 字节（mtime 6/13 09:06）
  - asst last 提到"6/14 09:06 (manual session)"
- **应对**：
  1. **「生成的文件」必须列该预生成文件**（stat 验证存在 + 大小），不要漏
  2. **「未完成」标"待 6/14 01:00 真正 cron 跑时是否覆盖"** —— 真正 cron 可能直接读已有文件当 base 但覆盖核心 5 选题，也可能视为已完成跳过
  3. **「重要决定」不日报化**该预生成行为（不是真实 cron 决策，是 agent 提前演练），但要在文件列表注明 `(预生成 by manual session 09:06)`
- **跨日 follow-up**：
  - 6/14 01:00 cron 真跑后观察：是覆盖了 pre-generated 5 选题？还是视为已完成跳过？
  - 如果 cron 跳过预生成内容 → pre-cron 演练成为 cron 节省 token 的有效机制
  - 如果 cron 覆盖预生成内容 → 预生成浪费 token，应在 skill 模板里禁用

## 跨日 follow-up 模板

每日 daily log 中如果检测到以上任一 P0 信号，必须用以下格式突出显示：

```markdown
## 未完成 / 待跟进

- 🔴 **飞书 webhook 持续失效 XX 小时** — 错误码 19001 token 无效，所有 cron 通知丢失，需重新授权（P0）
- 🔴 **GitHub PAT 视为已泄露** — `~/.hermes/skills/.archive/github-pat-retrieval/` 含真实 PAT，建议立即 revoke
- 🔴 **01:00 问题类 cron 连续 2 日同类失败**（2026-06-05 → 2026-06-06）— 同 session id `68a578b26b` 同一根因；建议 6/7 用 `delegate_task` 单步重跑 or 跳过 wiki 挖掘直接用 6/6 留底素材
- **hermes-backup.sh 日志写入** — 需加 `exec >> "$LOG_FILE" 2>&1`
- **dream-cycle 累计逻辑 bug** — 报"pages +N"与实际新建不符（与 YYYY-MM-DD 同一类）
- **cron 健康度** — 今日 3/12 = 25% cron 失败率（3 SILENT + 0 中断 + 0 成功幻觉），详见 §5d
- ⚠️ **成功幻觉（YYYY-MM-DD）** — <cron session id> 汇报"已完成 X/Y/Z" 但 filesystem + GBrain 双重验证无文件，需重跑 / 加 stat 强制校验
- ⚠️ **任务疑似中断（已完成 80%，缺落盘）** — <cron session id> asst last=0 但中段已规划完成，建议 `delegate_task` 单步重跑落盘
- ❌ **cron SILENT（未执行）**（2026-06-06 新增）— <cron session id> asst last = `[SILENT]`（8 字符），属第三种截断模式，需 6/7 02:00 cron 复跑
- ❌ **完整规划-未落盘（YYYY-MM-DD 新发现）** — <cron session id> asst last 列出 N 项内容规划 + 0 个 write_file，期望输出文件不存在；属第五种截断模式（§11c），需 `delegate_task` 单步派发落盘
- ❌ **asst-走-到-现在-写文件-前中断（YYYY-MM-DD 新发现）** — <cron session id> asst last 是半截过渡句（"现在写文件"/"Let me write"），0 个 write_file；属第四种截断模式（§11b），建议拆时间窗
- ✅ **cron 健康度破冰** — 某连续失败 cron 任务首次成功（如 6/8 01:00 选题），需对比同期同根因任务是否同步破冰（6/8 02:00 经验类未破 = 破冰非结构性）
- ✅ **cron 健康度结构性破冰**（2026-06-12 新增）— 多个 §5b/§5c/§11b/§11c/§11d 历史失败任务在同一日全部首次破冰（如 6/12 01:00 选题 + 02:00 经验类 + 02:00 用户模型 v10），需 6/13+ 验证是否连续破冰
- ✅ **漏报自检反馈循环**（2026-06-12 新增）— 某 cron 任务的异常检测触发另一 cron 任务深度复核（如 6/12 01:00 cron deep-read 6/11 4 文件发现 21 漏报），详见 §14
- 🔄 **dream cycle 12× 差距时强制走 delete-then-reimport**（2026-06-12 新增）— 脑库 stats 与 wiki 文件 size 12× 差距时普通 import 静默跳过，必须 delete-then-reimport（详见 §15）
- ⏰ **PVE Wiki cron 时段迁移 06:00 → 02:00**（2026-06-12 新增）— 待 6/13+ 观察是否稳定（详见 §16）
- 🔧 **api_server N session 沉淀**（2026-06-13 新增）— N 个 api_server session（如 SkillOpt LLM-miner 子任务）持续累积在 state.db，待用户决定清理策略（详见 §17）
- 📦 **Manual session "deliver-only" 模式**（2026-06-13 新增）— manual session 在 cron 已完成后重看应进入 deliver-only 模式，不重跑；详见 §18
- 👁️ **Pre-cron 预生成内容**（2026-06-13 新增）— manual session 提前跑次日 cron 流程生成文件（如 `问题类选题_YYYY-MM-DD+1.md`），待次日真 cron 是否覆盖（详见 §19）
- ✅ **Negative stat 验证（清理型任务）**（2026-06-13 新增）— 清理型任务（如 SkillOpt 5 路径清理）stat 验证"文件不存在 = 成功"也是 stat 验证的一种形态
- 🧹 **清理型任务完成**（2026-06-13 新增）— 6/13 SkillOpt 适配砍掉 + 5 路径全删（negative stat 验证通过）— SkillOpt 不适配特定领域 skill 场景
- 🆕 **P14 山东实施细则 11 倍重建**（2026-06-13 新增）— Wiki 政策库建设投入产出比最高形态（66→329 行 / 2.0→22KB），被 6/14 cron 立即利用为"24 小时新富矿"
```

其中 XX 小时是"自首次发现"累计时长；连续多日要在 daily log 顶部用 `⚠️ P0 跨日持续` 标注。
