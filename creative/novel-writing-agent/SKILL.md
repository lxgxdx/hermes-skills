---
name: novel-writing-agent
description: DeepSeek 小说写作 Agent，支持34种类型。触发词：写小说/开始写小说/novel/写网文/写仙侠。
---

# DeepSeek 小说写作 Agent

## 项目位置
`~/novel-project/`
```
~/novel-project/
├── 01_档案/
│   ├── 剧情大纲.md      # 章节大纲（含每章核心事件、钩子）
│   ├── 人物表.md        # 角色名字候选
│   ├── 章节日志.md      # 每章记录（自动累积）
│   └── 世界观设定.md    # 背景/规则/特殊设定
├── 02_正文/
│   └── 第001章_xxx.md   # 章节正文
└── 03_工具/
    ├── write_chapter.py  # 核心脚本（34种类型）
    ├── export_for_fanqie.py  # 番茄导出脚本
    └── node_modules/     # random_chinese_fantasy_names npm包
```

## ⚠️ 关键限制：terminal 工具对 .py 脚本无输出

**问题**：`python write_chapter.py <任意命令>` 通过 hermes-agent 的 terminal 工具执行时，stdout 和 stderr 都是 0 字节（rc=0），所有 print 语句、sys.stderr.write()、os.write() 全部消失。

**原因**：hermes-agent 的 terminal 工具对直接执行 .py 脚本有输出拦截行为，即使是 debug 语句也看不见。

**现象**：在这次排查中，即使在脚本最开头加了 `os.write(1, b"DEBUG\n")`，通过 terminal 执行时仍然 0 输出。

**解法**：永远不要用 terminal 运行 write_chapter.py。所有功能都用 execute_code + exec() 调用：
```python
import sys, os
sys.path.insert(0, '/home/lxgxdx/novel-project/03_工具')
exec(open('/home/lxgxdx/novel-project/03_工具/write_chapter.py').read(), globals())

pool = xianxia_name_pool()          # 仙侠名词池
result = generate_outline("仙侠文", "故事种子", 16)  # 生成大纲
ch = write_chapter("仙侠文", 1, "章节主题")  # 写章节
```

## 支持的34种小说类型

（注意：不是35种，是34种）

仙侠文、玄幻小说、奇幻小说、斯奈德节拍、人情小说、末世囤货、女频虐文、知乎短篇、脑洞文、都市爽文、悬疑小说、科幻小说、古言小说、种田文、快穿文、系统文、升级流、诸天无限文、追妻火葬场、甜宠爽文、换元法创作、替身文、同人文、直播流、规则怪谈、娱乐文、女频耽美虐文、四合院流、巫师流、小说仿写、雪花写作法、读心术文、番茄过稿、故事灵感

## 工作流程

### Step 1 — 初始化项目

用户说"写小说/开始写/想写仙侠"时，问4个问题：

1. **题材/类型？** 从34种里选，或描述方向
2. **世界观风格？** 西幻/东方/末世/都市等
3. **主角设定？** 穿越/本土/重生/普通人/特殊能力
4. **篇幅预期？** 短篇5千-1万 / 中篇1-3万 / 长篇3万以上

### Step 2 — 生成大纲

用 `generate_outline()` 生成，**仙侠文会自动注入名词池**（门派/功法/丹药/地名等）。

```python
# 例子
result = generate_outline("仙侠文", "山村少年误入遗迹得到残卷功法", 16)
# 仙侠文会自动带名词池
```

大纲格式：每章包含章节名、核心事件（2-3句）、结尾钩子。

确认后手动保存到 `01_档案/剧情大纲.md`。

### Step 3 — 逐章撰写

```python
# 写第X章
ch = write_chapter("仙侠文", 章节号, "本章主题")
print(ch)  # 输出到控制台
# 手动保存到 02_正文/第XXX章_章节名.md
# 手动更新 01_档案/章节日志.md
# 发送飞书给用户审阅
```

**⚠️ write_chapter() 不会自动保存**，需要手动保存文件。

### Step 4 — 章节日志格式

每章写完后追加到 `01_档案/章节日志.md`：

```markdown
## 第X章 章节名 (YYYY-MM-DD)
- **人物**：角色名/状态变化
- **地点**：发生地点
- **核心事件**：本章主要剧情
- **关键道具/信息**：获得物品、听到的关键信息
- **悬念/钩子**：留给下一章的悬念
```

### Step 5 — 番茄发布（写完任意多章后）

```bash
# 导出 TXT
python ~/novel-project/03_工具/export_for_fanqie.py

# 导出并启动上传 GUI
python ~/novel-project/03_工具/export_for_fanqie.py --upload
```

番茄上传工具（fanqie-novel-auto-uploader）需要用户手动在 GUI 中登录番茄作家后台。

---

## 仙侠文专项功能

### 名词池（xianxia_name_pool）

调用 `xianxia_name_pool()` 返回 dict：
```python
{
  'characters': {'male': [...20个人名], 'female': [...20个人名]},
  'dao':        {'male': [...15个道号], 'female': [...15个]},
  'sects':      [...10个门派名],
  'skills':     [...10个功法名],
  'books':      [...8个秘籍名],
  'locations':  [...10个地名],
  'alchemy':    [...8个丹药名],
  'materials':  [...8个材料名],
  'nations':    [...5个国家]
}
```

### generate_outline 注入名词池

当 `novel_type` 为"仙侠文"、"仙侠文创作"或"玄幻小说"时，`generate_outline()` 自动在 prompt 里注入名词池，包含门派、功法、丹药、材料、地名、国家等信息。

### 仙侠文系统提示词

仙侠文模板包含反套路方法论：
- 至少2个反转设定（废物流→天才陨落；师父→布局者）
- 世界观秘密（仙界是囚笼/飞升是骗局）
- 打破脸谱角色
- 每3章一个反转
- 禁用退婚/废物流/签到系统等老梗

---

## 当前进行中的项目

**项目：** 《仙墟》
**类型：** 仙侠文（反套路设计）
**篇幅：** 中篇，16章
**主角：** 沈忘，山村少年，意外得到残卷《逆命诀》
**核心悬念：** 仙界是囚笼，飞升者皆为"养分"；沈忘的真实身份是玄霄的善念转世

**当前进度：** 第1章已完成并保存（墟中少年，3600字，修订版含合理逻辑），第2章待写

**文件：**
- 剧情大纲：`~/novel-project/01_档案/剧情大纲.md`（已完成，16章）
- 章节目志：`~/novel-project/01_档案/章节目志.md`（第1章已登记）
- 人物表：`~/novel-project/01_档案/人物表.md`（空）
- 正文目录：`~/novel-project/02_正文/`（第1章已存入）

**下一章：** 第2章（星枢府试炼）—— 沈忘闯迷踪幻阵，玄霄散人提出交易教他补全功法，他学会吞噬精血强行提修为，代价折损寿元；出阵入府后偷听到三年前陈渊修炼《逆命诀》走火入魔失踪的消息

---

## 内部维护笔记（供 Agent 参考）

### write_chapter.py 内部 bug 修复记录

| 日期 | Bug | 修复 |
|------|-----|------|
| 2026-05-02 | `_load_xianxia_names()` cwd 错误：依赖 `__file__`（exec() 时不存在）和 `Path.cwd()`（sandbox 下是 `/tmp/`），导致 subprocess 找不到 node_modules | 改为硬编码 `SCRIPT_DIR = PROJECT_DIR / "03_工具"`，subprocess cwd 始终为 `str(SCRIPT_DIR)` |
| 2026-05-02 | `getDao(15, {})` 参数错误：npm 包 `getDao(count)` 不接受 options 对象 | 去掉多余 `{}` 参数 |
| 2026-05-02 | `generate_outline("仙侠文")` 没有注入名词池 | 在 `generate_outline()` 里自动识别仙侠类型并注入名词池 |
| 2026-05-02 | `write_chapter()` 不读 `剧情大纲.md`，每次生成都随机发挥跑偏（重则主角名字/故事背景全变），即使同项目也无法保持连续性 | 在 `write_chapter()` 的 user_prompt 里加入 `outline = read_archive("剧情大纲.md")`，并添加约束："必须严格遵循剧情大纲，不得擅自更改主线走向/人物关系/核心反转" |

**⚠️ 教训**：`write_chapter()` 写入新章节前，必须确保 剧情大纲.md 已存在且在上下文中。若项目只有大纲但未保存到文件，`write_chapter()` 仍会随机发挥。

---

## 关键文件路径

| 文件 | 路径 |
|------|------|
| 核心脚本 | `~/novel-project/03_工具/write_chapter.py` |
| 导出脚本 | `~/novel-project/03_工具/export_for_fanqie.py` |
| 番茄上传工具 | `~/fanqie-novel-auto-uploader/`（需 clone） |
| 剧情大纲 | `~/novel-project/01_档案/剧情大纲.md` |
| 章节目志 | `~/novel-project/01_档案/章节日志.md` |
| 人物表 | `~/novel-project/01_档案/人物表.md` |
| 正文目录 | `~/novel-project/02_正文/` |

---

## 常见问题

**Q: terminal 运行 write_chapter.py 没有输出？**
A: 已知限制——hermes-agent 的 terminal 工具对直接运行 .py 脚本会拦截所有 stdout/stderr（rc=0 但输出为0字节）。永远用 execute_code 的 exec() 方式调用，详见上方「⚠️ 关键限制」章节。

**Q: generate_outline 的仙侠文名词池没注入？**
A: 已修复——现在 `generate_outline("仙侠文", ...)` 会自动在 prompt 里注入名词池（门派/功法/丹药/地名等），不需要手动调用 xianxia_name_pool()。

**Q: 章节太长被截断？**
A: 分两次生成，标记"上/下"，分别保存。

**Q: 导出 TXT 后章节标题重复？**
A: `export_for_fanqie.py` 已修复，优先使用 markdown 内文标题。

**Q: 番茄上传工具报错？**
A: 番茄作家助手页面结构会随版本更新，GUI 中有"校准选择器"功能可手动重新定位元素。

**Q: 章节上传到一半断了？**
A: 重新运行会自动跳过已上传章节（有进度文件 `.runtime/progress.json`）。

---

## 参考资料

35个PDF模板位置：
```
/home/lxgxdx/.hermes/cache/documents/doc_*.pdf
```
