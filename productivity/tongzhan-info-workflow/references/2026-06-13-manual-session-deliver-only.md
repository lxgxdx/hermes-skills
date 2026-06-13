# 06/13 manual session 触发 "deliver-only" 模式（08:59 实测）

> **本参考文件专门记录一类新现象**：manual session 在 cron 已自动完成后打开，应进入 deliver-only 模式而不是 full-run 模式。

## 1. 现象描述

**6/13 时间线**：
- 06/13 01:07:37 — 问题类 cron 自动运行成功（`last_status=ok`，deliver=origin）
- 06/13 02:13:52 — 经验类 cron 自动运行成功（`last_status=ok`，deliver=origin）
- 06/13 08:59:45 — manual session 打开（用户主动查询 / 飞书推送补救 / 用户看完文件后追问）

**6/13 08:59 session 实际行为**（已纠正）：
1. ❌ 第一次操作直接 `ls -lt ~/wiki/entities/policy-*.md`（开始扫描）
2. ❌ 然后写 `/tmp/double_regex_scan.py` + 跑（浪费 token）
3. ❌ 然后 `browser_navigate` 观察者网台湾版（浪费 token）
4. ❌ 然后 `browser_click` 水饺联盟详情（浪费 token）
5. ✅ 最后 `ls -la /mnt/nfs/.../选题库/` 发现文件已存在
6. ✅ 读 6/13 选题文件确认已完整（43.4KB / 240 行 / 5 选题）
7. ✅ 改用 deliver-only 模式汇报给用户

**应做行为**（按 SKILL.md "必须先做的第一件事"）：
1. ✅ 第一步 `ls /mnt/nfs/.../选题库/问题类选题_$(date +%Y%m%d).md`
2. ✅ 文件存在 + size > 30KB → deliver-only 模式
3. ✅ 读取已有文件 + 浓缩汇报
4. ✅ 不重新扫描 Wiki、不重新抓新闻、不重新生成选题

## 2. 文件"完整"判定的最低标准（实测）

| 类型 | 最低 size | 选题数 | 必含章节 |
|------|-----------|--------|---------|
| 问题类 | > 30KB | ≥ 5 个 "### 选题" | "排重"、"剩余🟢优先富矿" |
| 经验类 | > 50KB | ≥ 8 个 "### " 标题 | "排重分析"、"本地素材" |

**6/13 实测对照**：
- 问题类 43.4KB / 240 行 / 5 选题 → ✅ A 状态（deliver-only）
- 经验类 84.8KB / 152 行 / 8 选题 → ✅ A 状态（deliver-only）

## 3. deliver-only 模式的汇报结构（用户偏好）

按用户偏好（bullet 列表 + 加粗重要内容 + 有限长度）：

```
[日期] 每日选题 cron 已完成（[问题类时间戳] + [经验类时间戳] 连续 N 日成功）

**问题类 N 个选题（[size] / [行数]）**

- **[类型/维度] 选题标题** — 简述切入角度（1-2 句含真实数据/案例）
- **[类型/维度] 选题标题** — 简述
- ...（共 N 条）

**经验类 N 个选题（[size] / ~[行数]）**

- **[本地/外地] 选题标题** — 简述
- ...（共 N 条）

**剩余🟢优先富矿**：6/13 用 N 个后，剩余 ~[count]+ 漏洞（按文件列出）—— 未来 [N] 周选题富矿稳定产出

**[次日] cron 建议方向**：
- [文件].md 剩余 X 个富矿中挖 Y 个
- 抓取观察者网台湾版 [次日] 凌晨首页，**如有新增热点事件补充 1-2 个台湾方向热点事件类选题**

**[日期] cron 关键洞察**：...（2-3 条本次新发现）

**[日期] cron 排重结果**：✅ N 个选题全部通过排重检查，与 [日期范围] 所有问题类/经验类选题均无主题重复

---

**两份文件均已落库**：
- 问题类：`[路径]`（[size] / [行数]）
- 经验类：`[路径]`（[size]）

**飞书推送状态**：⚠️ 飞书 webhook 已 N+ 小时失效（持续性记录），按 v11 决策停止推送避免日志噪声。本汇报通过 [deliver=origin 或当前对话] 自动交付到用户视野。
```

## 4. 何时会出现这种场景

未来 manual session 触发 deliver-only 模式的场景：

1. **用户 7:30 起床后主动查询**（最常见）：飞书推送 webhook 失效 → 用户直接来 CLI/微信/TG 问"今天有什么选题"
2. **cron 自动 deliver 失败补救**：cron 报告 `last_status=ok` 但 deliver 通道（飞书 webhook）失败 → 用户通过其他渠道追问
3. **cron 重新触发**：某些情况下 cron 任务会被重复触发（同一天 01:00 + 09:00 两次）
4. **跨平台查询**：用户在 CLI 看完后到微信/TG 复述同一问题
5. **7:30 飞书推送通道全面失效时的备用推送**：飞书 264+ 小时失效时，需通过其他平台推送给用户

## 5. 与已有模式的区别

| 模式 | 触发场景 | 工具调用 | 输出 |
|------|---------|---------|------|
| **full-run**（SKILL.md 标准流程） | 文件不存在 + cron 未运行 | 30+ 次（扫描 Wiki + 抓新闻 + 生成选题）| 完整新选题文件 |
| **incremental**（B 状态） | 文件存在但 size 不达标 | 10-15 次（grep 已用关键词 + 补充缺口）| 增量更新文件 |
| **deliver-only**（A 状态，本参考新增） | 文件存在 + size 达标 | 3-5 次（ls + read_file + 汇报）| 浓缩汇报给用户 |
| **quick-reply**（用户偏好模式）| 用户在微信/TG 问"今天选题怎么样" | 1-2 次（read_file 摘要） | 1 段话简述 |

## 6. 跨 session 一致性

**deliver-only 模式的"一致性"要求**：
- manual session 汇报的选题列表 = cron 自动生成的选题列表（不擅自增删）
- 选题顺序、关键词、维度标签保持一致
- 如发现 cron 输出有质量问题，**另起一个 incremental 任务**，不要在 deliver-only 中修改

## 7. 6/13 08:59 session 的工具调用节省

| 实际行为 | 应做行为 | 节省次数 |
|---------|---------|---------|
| ls -lt wiki/entities | ls 选题库 | -4 次（不必要的 wiki 扫描） |
| write_file double_regex_scan.py | — | -1 次 |
| terminal python3 double_regex_scan.py | — | -1 次 |
| browser_navigate 观察者网 | — | -1 次 |
| browser_click 水饺联盟详情 | — | -1 次 |
| browser_console 提取正文 | — | -1 次 |
| terminal grep policy-shandong-tongzhan | — | -1 次 |
| read_file P14 第六章 | — | -1 次 |
| 后续搜索文件等 | — | -10+ 次 |
| **总计** | **节省 ~21 次工具调用 + ~5K token 输出** | |

按 SKILL.md "必须先做的第一件事" 检测 → 6/13 应直接 read_file 选题文件 + deliver-only 汇报 → 节省约 21 次工具调用。

## 8. 相关 cron job ID

- 问题类 cron：`68a578b26b6c`（name: "问题类选题搜索"），`schedule: 0 1 * * *`，`deliver: origin`
- 经验类 cron：`59f917bbc534`（name: "经验类选题搜索"），`schedule: 0 2 * * *`，`deliver: origin`

**两个 cron 都 `last_run_at=2026-06-13`** 是判断"今日文件已生成"的最可靠信号之一。
