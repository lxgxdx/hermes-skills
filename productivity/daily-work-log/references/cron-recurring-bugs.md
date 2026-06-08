# 跨日复现的 cron 任务已知 bug & 信号清单

> 2026-06-04 首次整理，2026-06-05 大幅扩充（新增 §5b 成功幻觉 / §5c 前 N 步已规划但未落盘 / §10 dream cycle 0 净增正常信号）。2026-06-06 新增 §5d cron 整段 SILENT 占位符（第三种截断模式）+ §11 01:00 问题类 cron 连续 2 日同类失败。2026-06-07 新增 §11b asst last "半截过渡句" 第四种截断模式。2026-06-08 新增 §11c "完整结构化规划 + 0 write_file" 第五种截断模式 + §12 6/8 cron 健康度破冰（01:00 选题 4 日失败链条终结）。每日 cron session 中都会重复出现这些 bug，必须在「未完成 / 待跟进」中显式标注（甚至跨日持续 follow-up），否则会被静默丢失。

## 🔴 高优先级（每日重复出现的 P0 信号）

### 1. 飞书 webhook 持续失效（`oc_7c656031826c26b15f17d010097f3619`）

- **症状**：所有 cron 任务完成后向飞书回报时返回 `19001 access token invalid`
- **首次发现**：2026-06-02（48+ 小时）
- **2026-06-06 状态**：100+ 小时持续失效
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

### 5b. cron 任务"成功幻觉"（SUCCESS HALLUCINATION）— 最危险的汇报漂移（2026-06-05 新发现）

- **症状**：agent 写出**结构化"完成报告"**作为最后一条 asst（含详细文件名 + 大小 + 实施步骤 + 下一步），但实际**文件未落地**。和"普通截断"（asst last = 0）的关键区别：成功幻觉 = asst last **长且结构化**（这正是"读 asst[-1] = 成果汇报"策略会漏检的原因）
- **首次发现**：2026-06-05 02:00 PVE Wiki cron（`0abf80bf4d`，41 msgs / asst last 737 chars）
  - 汇报"已创建 4 个核心页面：proxmox-ve-install.md / gpu-passthrough.md / frigate-on-pve.md / pve-network-storage.md"
  - 实际 `~/wiki/concepts/` 下 4 文件**均不存在**
  - GBrain 搜索 "Proxmox VE 安装" / "GPU 直通" / "Frigate PVE" → 全部无相关 chunk
- **2026-06-06 状态**：连续 2 日同类（同一 cron session id 6/6 仍为 `0abf80bf4d68`，沿用 6/5 失败模式）
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
- **2026-06-06 状态**：**连续 2 日同类失败**（同一 cron 任务 `68a578b26b`，6/5 与 6/6 均为 asst last < 200 chars）
  - 6/6 asst[4]：读完 6/03-6/04 + 6/05 经验类（共 24 个本地选题）建立排重库
  - 6/6 asst[24]：建立 Wiki 政策富矿 A-E 五组（台湾投资保护法/互联网宗教/宗教活动场所/宗教教职人员/民族团结促进法）
  - 6/6 asst[25]：抓到观察者网 6/6 头条"五眼联盟"新角度
  - 6/6 asst last = 116 chars（在"打开文章详情"阶段截断，**未生成 `问题类选题_20260606.md`**）
- **与"未开始"区别**：未开始 = asst 全短过渡句；此模式 = asst 中段已经做了 80% 工作
- **应对**：
  1. 检测到 asst last = 0 + 期望输出文件不存在 → 标 `⚠️ 任务疑似中断（已完成 80%，缺落盘）`
  2. 建议 fallback：用 `delegate_task` 把"把 asst[10] 选题组合写入文件"作为单步任务派发
  3. **连续 2 日同 bug**：必须在「未完成」加 `❌ 01:00 问题类 cron 连续 2 日同类失败`（升 P0）
  4. 长期：tongzhan-info-workflow skill 的"落盘 step"应拆为独立 sub-step，便于失败重试
  5. **可复用素材**：6/6 asst[24] 已建立完整的 A-E 政策富矿分析 + 6/6 asst[25] 已抓取观察者网 6/6 头条"五眼联盟"——6/7 01:00 cron 可**跳过 wiki 挖掘和新闻抓取阶段**，直接用这些留底素材写文件

### 5d. cron session 整段只返回字面量 `[SILENT]`（第三种截断模式，2026-06-06 新发现）

- **症状**：cron session 最后一条 asst 内容是字面字符串 `[SILENT]`（长度仅 8），没有 skill 注入后的过渡句、没有失败原因、没有完成报告。是**第三种截断模式**，与已知的"空字符串截断"和"成功幻觉"都不同
- **首次批量发现**：2026-06-06 三个 cron session 同时中招：
  - `cron_0abf80bf4d68_20260606_020012`（llm-wiki-build，PVE wiki 概念页）—— 12 msgs / asst last = `[SILENT]`
  - `cron_8670107d659c_20260606_200008`（home-assistant-ops）—— 5 msgs / asst last = `[SILENT]`
  - `cron_e08019f497a1_20260606_210022`（check-wechat-issue）—— 4 msgs / asst last = `[SILENT]`
- **与"空字符串截断"区别**：`asst last = ''`（len=0）通常出现在 agent 进入死循环后被截断；`[SILENT]` 字符串是 agent 显式决定的"我没什么可汇报的"信号
- **与"成功幻觉"区别**：成功幻觉 = asst last 长且结构化（看着像真完成）；`[SILENT]` = asst last 极短（看着像真没做事）
- **根因猜测**（待 6/7 02:00 验证）：
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
- **应对**：dream cycle 报告里 `pages/chunks` 净增数 + `imported=0` 看似矛盾但**不需要 follow-up**；只有当 dream cycle 报 `imported > 0` 但 filesystem 找不到对应文件时，才触发"成功幻觉"检查

### 11b. "asst last = '现在写文件 / 先准备 Searxng 搜索'" 第四种截断模式（2026-06-07 新发现）

- **症状**：cron session 最后一条 asst 是**一句过渡句**（非结构化报告，也非空串、非 `[SILENT]`），形如 `现在写文件。先准备Searxng搜索作为辅助：` 或 `Let me write the output file now:`，**工具调用统计为 0 个 `write_file` / 0 个 `gbrain put`**
- **首次发现**：2026-06-07 **双 cron 同期触发**：
  - `cron_68a578b26b6c_20260607_010057`（01:00 问题类选题）—— 72 msgs / asst[26] = 995 chars，最后一句 = "Let me write the output file now:" → `问题类选题_20260607.md` **未生成**
  - `cron_59f917bbc534_20260607_020055`（02:00 经验类选题）—— 102 msgs / asst[42] = 3094 chars，最后一句 = "现在写文件。先准备Searxng搜索作为辅助：" → `经验类选题_20260607.md` **未生成**
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
- **根因（确认）**：info-workflow cron 在"设计 + 抓取 + 排重 + 列内容"阶段把 asst 配额用尽；agent 把"将要写什么"先在 asst 里铺完整（这是它的正常工作流），但 cron 时间窗到点时**还没排到 `write_file` 调用**。和 §11b 是同根因（cron 消息预算结构性不足），但**触发的 asst 形态不同**（§11b = 过渡句；§11c = 完整规划）
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

### 12. 6/8 cron 健康度破冰信号（2026-06-08 新增）

- **症状**：01:00 问题类选题 cron `68a578b26b6c` **连续 3 日失败（6/5+6/6+6/7）→ 6/8 首次成功**，5 选题完整落盘 26.6KB
- **关键改进**：
  1. skill 提示词中 Wiki 政策库富矿已建立（6/5-6/7 新建 3 个 policy-*.md 提供反向素材）
  2. cron 时间窗被"01:00 选题 → 01:30 案例补全"拆分（v7 USER.md 提议，6/8 实证）
  3. 排重机制成熟（与 6/1-6/4 选题无任何主题重复）
- **跨日持续**：
  - 6/9 必须用 02:00 经验类选题验证破冰是否**结构性**（而不只是 01:00 偶发）
  - 6/8 02:00 经验类仍 §11c 失败 → 破冰**未扩散**到同根因任务
- **应对**：
  1. **乐观但不放松**：在「重要决定」块记录"01:00 破冰"作为正面信号
  2. **同根因排查**：在「未完成」块把 02:00 经验类连续 4 日失败升 P0，与 01:00 破冰形成对比
  3. **不要归功单一改动**：01:00 破冰是"Wiki 富矿 + 拆时间窗 + 排重成熟"三因素叠加，6/9 02:00 复跑才能验证哪一因素是主因
- **PVE llm-wiki-build 6/6 vs 6/7 vs 6/8 三日对比修正**（同 6/8 完成）：
  - 6/6 SILENT → 真未执行
  - 6/7 健康检查任务（1 patch 验证 4 页面状态，本来就不建新页）
  - 6/8 重建 4 页面（实际 stat 验证全部存在 13.5KB）
  - 三日形态不同，不应统一标"连续 X 日成功幻觉"或"连续 X 日 SILENT"

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
```

其中 XX 小时是"自首次发现"累计时长；连续多日要在 daily log 顶部用 `⚠️ P0 跨日持续` 标注。
