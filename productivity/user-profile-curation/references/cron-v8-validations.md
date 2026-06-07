# Cron v8 验证模式 — 2026-06-08 实测成功的 4 个模式

> **来源**：v8 (2026-06-08) user-profile-curation cron 任务执行 + 同期 6/8 01:00
> tongzhan-info-workflow cron 4 日失败破冰 + 6/8 01:30 tongzhan-wiki-policy-builder
> P05 深化。
>
> **目的**：记录从 v7 假设 → v8 实测验证的模式，让未来的 cron skill 设计不必
> 重新推导。

---

## 模式 1：cron 时间窗拆分（v7 提议 → v8 验证有效）

**问题背景**：tongzhan-info-workflow 的 01:00 cron 任务在 6/5、6/6、6/7 连续 3 日
失败（asst last 0 chars / 成功幻觉），根因是单次 cron 想完成
"读 Wiki 政策库（5+ read_file）→ 抓新闻（browser_navigate）→ 设计 5 选题 →
写 5 选题 → 排重 → write_file"全流程，超出 ~72 条消息预算。

**v7 提议**：把任务拆成 01:00 选题 + 01:30 案例补全两个相邻 slot。

**v8 验证（2026-06-08 01:00）**：
- 单次 cron 用 70 条消息
- 完成 5 选题 / 26.6KB / 134 行 / 完整排重核对
- 完整 stat 验证 `问题类选题_20260608.md` (26650B)
- **零成功幻觉，零 0-char asst**

**对所有 cron skill 的设计规则**：

> 当一个 cron 任务反复出现 "asst last = 0 chars" 或 "成功幻觉" 但内容其实已设计好，
> 修复方法**不是**加更多工具或简化内容，而是**拆分为相邻 cron slot**，让每个
> slot 有完整预算走完 write_file。

**反模式**：

- ❌ 把"选题 + 写作 + 校对 + 落盘"全塞进一个 cron 只因"工作流图上看似连接"
- ❌ 给 cron 加 `delegate_task` subagent 期望"分摊预算"（subagent 有自己的
  context 限制，最终还是会撞墙）
- ❌ 缩短内容期望"少写点就能写完"（用户画像的核心价值就是完整，不是精简）

**成功条件**：每个 slot 走完"读 → 设计 → 写 → stat 验证"四步，且 write_file 是
slot 的**最后一步**（不是中间步骤，避免后续工具调用打断落地）。

---

## 模式 2："Wiki 政策库 → cron 选题"反向循环（v8 6/8 实测）

**核心观察**：6/8 01:00 tongzhan-info-workflow cron 主动读
`~/wiki/entities/policy-*.md` 文件，从"执行层面问题标注"章节挖出 3 个全新
制度漏洞选题：

| 选题 | 来源 Wiki 页 | 制度漏洞 |
|------|------------|----------|
| 民族团结进步促进法 7/1 生效倒计时 | `policy-minzu-tuanjie-promotion-law.md` | 配套实施细则缺位 |
| 台湾同胞投资保护法 30 年未体系修订 | `policy-taiwan-investment.md` | 母法 19 条 vs 政策文件 89 条 |
| 光彩事业品牌保护 3 年置顶零追责 | `policy-guangcai.md`（P15，6/7 二次深化） | 监管协调机制失效 |

**这是用户设计的工作流**——不是 agent 自作主张：

```
[Wiki 政策页]  ←  用户/agent 建设
   │
   ↓ cron 01:00 读 Wiki
[5 候选选题]
   │
   ↓ 用户电脑选定 + 起草
[信息稿 .docx]
   │
   ↓ 新案例/新制度问题
[Wiki 政策页] + [comparisons/ 案例库子页]   ← 闭环
```

**对 user-profile-curation 的影响**：

- v(n) 报告 Wiki 进展时，**必须同时报告 cron 选题用了哪些 Wiki 页**——这是
  "Wiki 价值" 的唯一度量（光建 Wiki 没用，cron 反向挖到才有用）
- v(n) 报告 cron 选题时，**必须标注选题反向挖自哪些 Wiki 页**——这是"选题质量
  提升"的证据
- 两个数字应一起增长：Wiki 深化页数 → 制度漏洞富矿数 → 类型B 选题数

**对 tongzhan-info-workflow 的影响**：

- 选题 cron 任务的"读 Wiki 政策库"步骤应从可选升级为**必做第一步**（当前是
  "第二步（新增）"，应升格为"必做"）
- Wiki 政策库每新建/深化一页，**未来 30 天内**应能产出至少 1 个新类型B 选题
- 监控指标：选题 cron 的"完全无重复"率（v8 6/8 是 100%）

---

## 模式 3：连续 cron 日的"自主运行天花板" ≈ 7 天（v8 6/8 实测）

**观察**：6/2 → 6/8 连续 7 日所有平台（feishu/weixin/tg/cli）零人类对话，
但 cron 任务自驱推进所有 5 大工作线。历史峰值是 4-5 日（v6 之前），v8
刷新到 7 日。

**对 v(n) 报告的硬要求**：

- 报告头部必须包含"**连续 cron 日数**"字段（v8 是 7，v9 可能是 8）
- 当连续 cron 日数 ≥ 7，v(n) 增量章节必须明确说"自上次人类对话以来 N 天
  自主运行，建议下次人类对话时先回顾累计产出"
- "**待用户决策**"章节应优先列出"用户可能想看哪些累计产出"（v8 已隐含
  第 18 条："6/9 后用户大概率会回到 cron → 人对话切换"）

**对 cron 自身健康度的影响**：

- 7 日全 cron 是"健康"还是"用户失联"？取决于**飞书 webhook 状态**：
  - 飞书 webhook 健康 → 每日自动报告正常推送 → 用户知情 → 7 日 cron = 自主
  - 飞书 webhook 失效（v8 168+ 小时）→ 每日自动报告全丢失 → 用户**可能**
    不知情 → 7 日 cron = 失联
- **当前 v8 状态：飞书 webhook 失效 168+ 小时 + 7 日全 cron = 用户大概率
  失联 1 周**。这是紧急待修复项。

**阈值建议**：

- 1-5 日：正常范围
- 6-7 日：v(n) 报告应明确"累计 X 天无人类对话"提示
- ≥ 8 日：v(n) 报告应在"洞察"章节加 "USER ALERT：建议下次人对话时
  主动 checkpoint 累计产出" 警示

---

## 模式 4：落库状态表必须带精确字节数（v8 6/8 实测）

**v8 报告落库状态表（v6 起就要求但 v7 之前常省略精确字节）**：

```markdown
| 文件 | 路径 | 用途 | 大小 |
|------|------|------|------|
| **用户模型主文件** | `~/.hermes/memories/USER.md` | v8 主报告（覆盖 v7） | **18,460B** ✅ |
| **v7 备份** | `~/.hermes/memories/USER.md.bak.v7_1780855293` | v7 完整备份 | 17,239B ✅ |
| **周期化归档** | `~/.hermes/memories/user_model_report_20260608.md` | 54 天数据快照 | **18,460B** ✅ |
| **每日精简版** | `~/.hermes/memories/daily/2026-06-08-user-model-snapshot.md` | GBrain 同步版 | **1,898B** ✅ |
```

**为什么这一行很关键**：

1. **精确字节**（不是 "已完成" 或 "已落盘"）让未来 v(n+1) 立刻能 spot：
   - 文件是否被外部误删（size = 0B）
   - 文件是否被错误覆盖（size 异常小）
   - 增长是否合理（v7 17.2K → v8 18.5K = +1.2K / +7% 合理）

2. **v(n) 版本号绑定**（"v8 主报告" / "v7 完整备份"）让未来翻历史时
   一眼看到这是哪个版本，**不必打开文件读第一行**

3. **✅ 标记**（不是 ✗）让 cron 成功状态在视觉上立即可读，**避免成功的
   幻觉**：如果 size 是 0B 但你写了 ✅，就是自欺欺人

**实现细节**：

```bash
# 写完 3 个文件后必须立即 wc -c
wc -c ~/.hermes/memories/USER.md \
      ~/.hermes/memories/user_model_report_YYYYMMDD.md \
      ~/.hermes/memories/daily/YYYY-MM-DD-user-model-snapshot.md
```

**反模式**：

- ❌ 只写 "3 个文件已落盘"（无 size，等于没说）
- ❌ 写 "KB 级"（太模糊，0.5K 也是 KB 级）
- ❌ 写 "完成"（已被成功幻觉 pattern 污染的词，禁用）

**推广建议**：所有 cron 写盘 skill（`tongzhan-wiki-policy-builder` /
`tongzhan-info-workflow` / `daily-work-log` / `llm-wiki-build` /
`dream-cycle`）的最终汇报都应包含等价的"实际字节"表。

---

## 附：v8 同时验证的 3 个"未变项"（不是新模式，是已沉淀的纪律）

1. **memory 工具在 cron 模式持续不可用** —— v8 第 8 次确认。直接写文件是
   持久化的 source of truth。`memory` 工具的 1 次尝试 + 立即 fallback 模式
   已成为 cron 标准动作。
2. **`write_file` → `wc -c` 验证纪律** —— v8 严格执行。`verify-cron-writes.sh`
   脚本可选项，但即使不调脚本，单条 `wc -c` 命令也够。
3. **v(n-1) 备份到 `.bak.v(n-1)_<ts>`** —— v8 备份 USER.md 到
   `USER.md.bak.v7_1780855293`（17,239B），命名版号 + Unix 时间戳，grep 友好。
   Hermes 自动备份是 13.9KB `.bak.1780392841`（无名版号），手工命名版号
   的备份更有审计价值。

---

*更新日期：2026-06-08 / 触发会话：cron_*_20260608_02* (user-profile-curation v8)*
