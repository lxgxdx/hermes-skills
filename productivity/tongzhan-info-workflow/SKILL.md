---
name: tongzhan-info-workflow
description: 统一战线信息稿工作流。触发词：搜索选题/信息稿/开始写/做信息。包含每日选题推送（问题类+经验类）、初稿生成、终稿（DeepSeek API）生成完整流程。
---

# 统一战线信息稿工作流

## 触发条件
用户说"搜索选题"、"做信息稿"、"开始写"、"做信息"等类似表达时触发本流程。

---

## ⚠️ 微信沟通格式规范（必须遵守）

用户（lxgxdx）明确要求通过微信沟通时：
- **不用 Markdown 表格** → 用 bullet 列表（`- 项目`）代替
- **重要内容用加粗** → 用 `**加粗内容**` 
- **代码块包裹内容可左右滑动** → 表格等复杂内容用三个反引号包裹

这是用户明确表达的沟通偏好，违反会导致信息可读性差。

---

## 一、每日选题推送

### 时间
每天 07:30 飞书推送

### 内容
- **经验类**：8个选题（本地做法4个 + 外地借鉴4个）
- **问题类**：8个选题（民族宗教4个 + 台湾4个）

### 格式
```
### 1.【类别】选题标题
- **简述**：这个问题/经验是什么（50字以内）
- **依据**：为什么选这个（30字以内，如"网上案例""本地素材""本地做法""外地经验"等）
- **可写角度**：简要说明可以从哪几个方面展开（30字以内）
```

### 搜索方式（定时任务，凌晨执行）

**外网搜索（Searxng 元搜索）**：
- 地址：`http://localhost:7777`（2026年5月实测可用）
- 接口：`/search?q=关键词&format=json`
- ⚠️ **Searxng 服务在 cron 环境下可能返回空结果**（服务临时不可用或连接超时）。处理方式见"7.1 Searxng 返回 0 条结果"段落。

```python
import urllib.request, urllib.parse, json

def searxng_search(query, max_results=8):
    """使用 Searxng 元搜索引擎搜索网页
    
    注意：必须用 urllib.parse.quote() 编码中文_query_部分，否则中文查询返回 0 条结果。
    同时用 r.get("title", "") 而非 r["title"]，避免 KeyError。
    """
    base_url = "http://localhost:7777"
    # ⚠️ 关键词部分用 quote() 编码，params 整体用 urlencode() 包装
    params = urllib.parse.urlencode({
        "q": query,          # query 本身已含中文，urlencode 会正确处理
        "format": "json",
        "engines": "google,baidu",
        "limit": max_results
    })
    url = f"{base_url}/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    results = data.get("results", [])[:max_results]
    return [(r.get("title", ""), r.get("url", ""), r.get("content", "")) for r in results]
```

> ⚠️ **Searxng 服务不可用时的兜底策略**：如果 searxng_search() 所有查询均返回空结果（连 `results` 列表都是空的），说明服务本身不可用。此时必须切换到以下兜底方案，不得跳过搜索直接凭记忆编造选题：
> 1. **delegate_task 并行搜索本地 docx**（最高效，见下方"策略A"）—— 工作总结、范文等 docx 文件中已有大量本地创新做法
> 2. **浏览器 Bing 搜索**（手动获取 URL）：`https://cn.bing.com/search?q=关键词`（百度会弹验证码，Google 会重定向到验证页，Bing 国内版通常可用）
> 3. **外地借鉴选题改为"方法论参考"**：从本地材料中提及的外出考察学习方向提炼方法论，不依赖外网搜索
> 4. **结合领域常识和政策背景补充选题**，确保每个选题有据可查
>
> **验证 Searxng 是否恢复**：手动跑 `curl "http://localhost:7777/search?q=统一战线&format=json&limit=2"` 看是否返回含 `results` 的 JSON

**本地搜索（两层策略）**：

**第一层：search_files** — 快速定位文件
- 搜索 /mnt/nfs/2026年统战工作 目录下的 docx/doc 文件
- ⚠️ **`search_files` 的 `target=content` 对中文关键词返回 0 结果**（不论 `file_glob` 设什么），这是工具已知局限
- 因此 `content` 模式只用于英文/拼音搜索；中文搜索改用第二层

**本地素材搜索（两种策略）**：

> ⚠️ **直接用 python-docx 遍历所有 docx 文件**是最高效的方式，比逐个读取更省力。推荐用 `delegate_task` 并行执行大规模 docx 内容扫描。

**策略A（推荐）：delegate_task 并行大规模搜索**

当需要从 /mnt/nfs/2026年统战工作 下挖掘本地素材时，用 delegate_task 并行搜索 docx 内容：

```
搜索关键字（如"欧美同学会"、"芳华同灼"、"网络人士"等）
遍历目录 /mnt/nfs/2026年统战工作 下所有 .docx 文件
排除"已成稿"文件夹
对每个命中文件，用 python-docx 读取段落文本
返回：文件名 + 命中段落摘要
```

示例 prompt（发给 delegate_task）：
> "Search local docx files under /mnt/nfs/2026年统战工作/ for content related to [TOPIC]. Return which files contain relevant content, key facts/numbers/activities mentioned, and any specific programs or mechanisms described. Focus on meeting plans (配档表), summaries (总结), or work 要点/要点. Ignore files in 已成稿 folder."

delegate_task 的 `max_concurrent_children` 上限为 3，超过会报错。

**策略B：读取 references/known-local-docs.md**

文件中已预先摘录了关键 docx 的内容摘要，优先从这里提取数字和做法，再按需精读原文。

**策略C：直接 python-docx 精读**

针对已知的关键文件路径，用 subprocess 调用 python-docx 读取段落文本：

```python
import subprocess
fpath = "/mnt/nfs/2026年统战工作/.../xxx.docx"
safe = fpath.replace("'", "'\"'\"'")
result = subprocess.run(
    ["python3", "-c",
     f"import docx; doc=docx.Document('{safe}'); "
     f"[print(p.text.strip()) for p in doc.paragraphs if p.text.strip()]"],
    capture_output=True, text=True, timeout=30
)
print(result.stdout)
```

**第二层：python-docx 直接读取内容**
- 定位到具体文件后，用 python-docx 直接读取段落文本进行内容分析
- 关键文件清单（优先读）：
  - `6.巡查部机关/3.材料/4.工作总结及要点/2025/2025年全县统战工作情况.docx` — 年度全局工作
  - `6.巡查部机关/7.上报材料/4.工作总结及要点/2024/县委统战部2024年度工作总结.docx` — 去年工作亮点
  - `8.信息工作/范文/2026年/4月/` — 最新范文（已发布的经验类信息稿）
  - `1.办公室/34.奋进十五五民企宣传/` — 民营企业特色做法
  - `1.办公室/10.接待工作/4.23厉华珍调研信息工作/` — 信息工作专项汇报

```python
import subprocess, os

def read_docx_paragraphs(fpath):
    """读取 docx 文件所有段落文本，兼容中文路径"""
    safe = fpath.replace("'", "'\"'\"'")
    result = subprocess.run(
        ["python3", "-c",
         f"import docx; doc=docx.Document('{safe}');"
         f"[print(p.text.strip()) for p in doc.paragraphs if p.text.strip()]"],
        capture_output=True, text=True, timeout=15
    )
    return result.stdout

# 示例：读取 2025 年工作总结前 30 段
fpath = "/mnt/nfs/2026年统战工作/6.巡查部机关/3.材料/4.工作总结及要点/2025/2025年全县统战工作情况.docx"
text = read_docx_paragraphs(fpath)
print(text[:3000])
```

> ⚠️ **`.doc` 文件无法直接读取**：`search_files` 的 `target=content` 对 `.doc`（Office 97-2003 二进制格式）返回空结果，python-docx 也会报 `PackageNotFoundError`。必须先转换为 txt：
> ```bash
> mkdir -p /tmp/tz_docs
> libreoffice --headless --convert-to txt "文件名.doc" --outdir /tmp/tz_docs/
> ```
> 然后用 `read_file` 读取生成的同名 `.txt` 文件。
> 验证文件格式：`file "文件名.doc"`（含 "Composite Document File V2 Document" 即为旧格式）。

**Searxng 配置说明**：
- 配置文件：`/mnt/user/appdata/searxng/settings.yml`
- 务必在 `search.formats` 下加入 `json`，否则 API 返回 403
- 容器内端口 8080，映射到宿主机 8083

**问题类（每天 01:00 执行）**：
- 外网（Searxng）：
  - **民族宗教方向**：搜索政府网站 + 权威媒体，找具体案例
    - 搜索词如：`民族宗教 问题 乱象 2025 统一战线`、`佛教道教 商业化 违规 2025`、`网络宗教 非法 传播 2025`、`宗教活动 场所 乱象 2025`
  - **台湾方向**：

⚠️ **Searxng 对台湾相关关键词返回空结果是常态（引擎超时或被屏蔽）。** 2026年5月实测确认：google/baidu/bing 引擎对所有台湾方向搜索词（包括"台胞在大陆困难"、"两岸关系新问题"等）均返回0条结果，与查询词选择无关。

**台湾方向的正确兜底策略（必须执行，不得跳过）**：
1. **调用模型常识生成选题**：直接用 deepseek-v4-flash 的领域知识生成4个台湾方向选题，基于对台工作政策背景（如《惠台31条》《惠台26条》落实情况、国台办历年发布会内容等），确保选题符合中央对台工作精神
2. **选题方向参考**（已验证适合问题类信息稿）：
   - 台商在大陆转型升级困境（融资难、政策不对称）
   - 台湾青年就业创业隐性壁垒（学历认证、资质互认）
   - 两岸婚姻家庭子女教育问题（入学、户籍衔接）
   - 台胞社保医疗衔接难题（转移接续、就医结算）
3. **标注"网上案例"或"对台工作会议反映"**：不在依据中捏造具体链接，但确保选题方向有政策依据
4. **民族宗教方向不受影响**：Searxng 对民族宗教类中文关键词返回结果正常，继续使用外网搜索
- 本地：搜索 /mnt/nfs/2026年统战工作 目录下 docx/doc 文件，找近期台胞台商相关工作动态（如2024年工作总结提及的"亿丰台资获奖"等）

**经验类（每天 02:00 执行）**：
- 本地：搜索 /mnt/nfs/2026年统战工作 目录，整理本地创新做法
- 外网（Searxng）：搜索外地统战工作创新经验（方法论层面，不重复本地具体工作）
  - 搜索词如：`统战工作 经验做法 创新 2025`

### 搜索结果时间核验（必须步骤）

**重要**：选题必须基于近3个月内的内容，时间标注到具体日期。

在生成选题前，对所有搜索结果进行时间筛选：
- 优先选择：近1个月内（2026年4月-5月）
- 可选：近3个月内（2026年2月以后）
- 不选：3个月以前的内容（除非是长期存在的老问题且有新的进展）

时间判断依据：网页标题、URL日期、摘要内日期。无法判断时间的搜索结果，标注"[时间待核实]"，不优先使用。

### 搜索 "2026" 关键词的局限（重要发现）
- Searxng 对"2026"作为独立关键词索引效果差，直接搜"2026 xxx"往往返回空结果
- **正确做法**：不依赖年份关键词，直接搜具体事件/政策名称
  - 错误：`民族宗教 问题 2026`
  - 正确：`非法网络招徕 专项整治 两部门 最新`（从摘要/标题中自然出现日期）
- **时间判断**：从搜索结果的标题、URL路径、摘要内容中提取具体日期
- **无日期结果**：标注"[时间待核实]"，不优先使用

### 推送路径
结果保存至 `/mnt/nfs/2026年统战工作/8.信息工作/选题库/`
- `问题类选题_YYYYMMDD.md`
- `经验类选题_YYYYMMDD.md`

---

## 二、选题标准与写作规范（范文分析总结）

> 以下是从10+篇范文（问题类2篇完整正文、经验类10篇）中提炼的实战规律，直接指导选题和写作。

### 2.1 好选题的判断标准

**问题类选题必须满足：**
1. **有具体新闻事件触发**：如"张雪机车夺冠"→两岸机车贸易壁垒；不宜选"两岸关系面临的挑战"等宏观空泛话题
2. **有具体数据支撑**：如"1466.5万辆摩托车""综合税率超40%"；不选纯概念阐述
3. **有来源可查**：政策文件、统计数据、媒体报道
4. **有地方切入角度**：最好与本地统战工作能找到结合点

**经验类选题必须满足：**
1. **有具体做法**：不是"做好XX工作"，而是"三措并举激活新阶层"
2. **有品牌名称**："一路同行""木兰荟""三单管理"等标识性名称
3. **有数字成效**：30家企业、20余场活动、1000余人次等具体数据
4. **有明确对象**：新阶层、女企业家、商会、民企等

### 2.2 标题怎么写

**问题类标题格式：**
```
「关于XXX的原因/问题/建议」
```
- 范例：`关于厘清无党派人士认定范围的建议`
- 范例：`关于两岸机车贸易壁垒梗阻民族品牌融合发展的原因及对策建议`
- 关键：问题指向要明确，不用"浅谈""思考"等模糊词

**经验类标题格式：**
```
「五莲县+动作+对象+成效」
```
- 范例：`五莲县三措并举激活基层新阶层统战工作"新"活力`
- 范例：`五莲县做优"一路同行"品牌 汇聚"新"力量赋能发展`
- 关键：动宾结构突出（激活、建强、开展、推动），成效要可见

### 2.3 内容怎么展开

**问题类正文结构（最典型范例：两岸机车贸易壁垒）：**
```
一、背景
  具体事件+时间+数据（2026年3月张雪机车夺冠，台湾市场数据）
二、原因分析
  分3个维度，每个有：观点+数据/案例支撑
  避免：只列标题没有分析
三、对策建议
  3条，每条有具体措施，不是空话
  如：支持两岸民营企业产业链协同合作
```

**经验类正文结构（最典型范例：三措并举激活新阶层）：**
```
标题（一句话说明主体+核心做法，不超2句）

一、做法1名称（动宾结构）
  具体内容+数字成效（30家企业、10余条问题）
二、做法2名称
  具体内容+数字成效
三、做法3名称
  具体内容+数字成效

（联系人：XXX，联系方式：XXX）
```

### 2.4 充实度检查清单

生成初稿前，对照以下清单自检：

- [ ] 有具体案例/事件（如：商品listing、新闻事件、典型做法）
- [ ] 有具体数字（如：金额、比例、案件数、人数、企业数）
- [ ] 有消息来源标注（如："XX部门2026年X月X日公布"、"XX统计显示"）
- [ ] 有时间标注（具体到年月，不用"近年来""最近"）
- [ ] 原因分析段不止列标题，有深入分析
- [ ] 建议不止喊口号，有具体可操作的措施

---

## 三、搜索选题 → 发送用户选择 → 生成初稿

### 标准流程（按顺序执行）

**第一步：搜索选题**
- 按下方"搜索方式"执行，生成8个选题
- 每个选题必须包含：具体时间（近3个月内的具体日期）、消息来源

**第二步：发送选题给用户（飞书）**
- 必须发送飞书，等待用户选择（如"选题目8"）
- **不允许在用户未选择前就生成初稿**
- 飞书目标：`feishu:oc_7c656031826c26b15f17d010097f3619`

**第三步：用户选择后生成初稿**
1. 读取格式要求文件：`/mnt/nfs/2026年统战工作/8.信息工作/信息报送格式要求.txt`
2. 读取初稿参考范例：`/mnt/nfs/2026年统战工作/8.信息工作/1.二手交易平台非法传度授箓问题亟需引起重视/1.0.docx`
3. 创建文件夹：`/mnt/nfs/2026年统战工作/8.信息工作/序号.选题名称/`
4. **搜集素材**（详细搜索，不省略）：
   - Searxng 外网搜索具体案例、数据、政策文件
   - 本地文件搜索相关背景材料
   - 必须找到**具体数据**（如金额、比例、案件数等）
   - 必须找到**消息来源**（如"XX部门2026年X月X日公布"、"XX网数据显示"等）
5. **生成初稿**：详细完整，对照参考范文的充实程度
6. **自检**：对照"充实度检查清单"检查初稿，缺什么补什么
7. **保存**：`/8.信息工作/序号.选题名称/1.0.docx`
8. **发送飞书**：把初稿全文发到飞书，等待用户确认

**第四步：用户确认初稿后，生成终稿**
- 调用 DeepSeek API 生成终稿
- 保存：`/8.信息工作/序号.选题名称/终稿.docx`
- 发送飞书

### 初稿格式（问题类）
```
标题（黑体三号居中，「关于XXX的原因/建议」格式）
一、背景/基本情况
  （一）具体事件+时间+数据
  （二）涉及面估算
二、原因分析
  （一）...
  （二）...
三、对策建议
  （一）...
```

### 初稿格式（经验类）
```
标题（黑体三号居中，五莲县+动作+成效格式）
主体部分：若干小节
  做法名称（动宾结构）
  具体内容+数字成效
联系人：XXX  联系方式：XXX
```

### 初稿到 docx 格式
使用 `document-editor` skill 中的 `WordDocumentEditor` 类生成 docx。

**⚠️ 重要：python-docx 中文 Unicode 腐败问题（必须避免）**

直接向 WordDocumentEditor 传入中文文本时，绝不可使用 Python Unicode 转义字符串（如 `\u83B2` 表示"莲"），python-docx 内部会将中文字符按 OCR 式错误替换：
- `\u83B2`（莲）→ 莱
- `\u8BC9`（诉）→ 请
- `\u8BF7`（求）→ 竟/求
- `\u805A`（聚）→ 点

**正确做法：将文本写入 UTF-8 文件，再从文件读取传入**

```python
import sys
sys.path.insert(0, '/home/lxgxdx/.hermes/skills/ppt-work/document-work/document-editor')
from editor import WordDocumentEditor

# 写入临时文件（绕过 python-docx Unicode 腐败）
with open('/tmp/title.txt', 'w', encoding='utf-8') as f:
    f.write("《五莲县实行"三单"管理闭环解决民企诉求》")
with open('/tmp/body.txt', 'w', encoding='utf-8') as f:
    f.write("五莲县建立"收集单、交办单、反馈单"闭环管理机制...")

editor = WordDocumentEditor()
editor.set_page_setup(top=3.5, bottom=3.2, left=2.7, right=2.7)

# 从文件读取标题和正文
with open('/tmp/title.txt', 'r', encoding='utf-8') as f:
    title_text = f.read()
with open('/tmp/body.txt', 'r', encoding='utf-8') as f:
    body_text = f.read()

editor.add_paragraph(title_text, font_name="黑体", font_size=14, bold=True, align="center")
editor.add_paragraph(body_text, font_name="仿宋_GB2312", font_size=14, first_line_indent=True)
editor.save("/path/to/output.docx")
```

> **为什么heredoc不行**：终端 heredoc 中的中文引号等特殊字符会导致 SyntaxError，改用 write_file + terminal 运行 .py 文件的方式最稳。

---

## 四、初稿确认后：生成终稿

### 调用 DeepSeek API
从 `~/.hermes/.env` 的 `DEEPSEEK_API_KEY` 读取密钥。

- **模型**：deepseek-chat
- **端点**：https://api.deepseek.com/chat/completions
- **重要**：请求时必须加 `"reasoning":"skip"`，否则 content 为空

```python
import os, json, urllib.request

with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        if line.startswith("DEEPSEEK_API_KEY="):
            api_key = line.split("=", 1)[1].strip()

payload = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "prompt内容"}],
    "max_tokens": 4096,
    "reasoning": "skip"
}

req = urllib.request.Request(
    "https://api.deepseek.com/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    result = json.load(resp)
    content = result["choices"][0]["message"]["content"]
```

### 系统提示词（传给 DeepSeek）
```
你是统战信息稿写作专家，负责将详细初稿精炼为符合报送标准的终稿。

【格式要求 - 问题类】
- 结构：背景/原因/建议（背景可不写）
- 总字数：2-3页篇幅
- 字体：中文仿宋_GB2312三号，英文/数字 Times New Roman 三号
- 段落间距：28
- 页边距：上3.5cm、下3.2cm、左右2.7cm

【格式要求 - 经验类】
- 总字数：400-500字，不超过500字
- 标题前空两格，黑体三号，不换行直接接正文
- 字体：中文仿宋_GB2312三号，英文/数字 Times New Roman 三号
- 段落间距：28
- 页边距：上3.5cm、下3.2cm、左右2.7cm

【内容要求】
- 精简提炼，概括性叙述
- 不使用多级数字标题，纯正文叙述
- 标题简短有力（如"亟需引起重视"体）
- 删除所有OCR识别错误和原文冗余内容
- 保持原文核心信息和主要观点不变

请直接输出终稿全文，不要解释。
```

### 输出
1. 保存：`/8.信息工作/序号.选题名称/终稿.docx`
2. 推送飞书：把终稿发到飞书

---

## 五、关键路径

```
/mnt/nfs/2026年统战工作/8.信息工作/
├── 选题库/
│   ├── 问题类选题_YYYYMMDD.md
│   └── 经验类选题_YYYYMMDD.md
├── 1.二手交易平台非法传度授箓问题亟需引起重视/
│   ├── 1.0.docx（初稿）
│   ├── 终稿.docx（终稿）
│   └── IMG_*.png（素材照片）
└── 2.新选题名称/
    ├── 1.0.docx
    └── 终稿.docx
```

---

## 六、参考文件

| 文件 | 路径 |
|------|------|
| 格式要求 | /mnt/nfs/2026年统战工作/8.信息工作/信息报送格式要求.txt |
| 问题类范文（详尽） | /mnt/nfs/2026年统战工作/8.信息工作/（例子）台湾老兵骨灰迁回大陆诉求升温需引起重视.docx |
| 问题类范文（最新） | /mnt/nfs/2026年统战工作/8.信息工作/8.台商在大陆资金汇回渠道便捷性有待提升/终稿.docx |
| 问题类范文（完整案例） | /mnt/nfs/2026年统战工作/8.信息工作/范文/2026年/4月/（五莲县信息）关于两岸机车贸易壁垒梗阻民族品牌融合发展的原因及对策建议.docx |
| 经验类批量参考 | /mnt/nfs/2026年统战工作/8.信息工作/范文/2026年/4月/ |
| **本地重要文档清单** | `references/known-local-docs.md`（本 skill 目录，含关键文件路径+内容摘要+数字备忘） |
| **选题排重规则** | `references/选题排重规则.md`（已刊发稿件禁止关键词 + 近3天每日选题记录 + 5月未挖掘方向清单；每次经验类 cron 必须读取） |
| **当月选题线索汇总** | `8.信息工作/范文/2026年/4月/4月份下半月信息宣传选题汇总.docx` — 各联络员自提选题草稿，含白鹭湾打卡点、侨联读书日、张雪机车、基层新阶层、网络统战等方向；是本地选题最直接的来源 |
| **公众号内容制作（HTML截图方案）** | `references/公众号内容制作.md` — AI生图随机性高，用HTML+Chrome截图代替；包含标准工作流、配色模板、MiniMax API备选方案 |

---

## 定时任务（Cron）执行注意事项

> 以下是 cron 凌晨跑每日选题的实战经验，直接照抄任务描述的 Python 代码会导致问题。

### 定时任务必须遵循的标准流程

**经验类定时任务（每天 02:00）**：
1. **Searxng 搜索** — 调用 skill 中的 `searxng_search()`，外地经验搜索词：`统战工作 经验做法 创新 2025`、`民族宗教 工作 亮点 经验 2025`、`对台工作 创新举措 经验 2025`、`统战部 信息工作 经验 交流 2025`
2. **若 Searxng 返回空** → 跳过外网搜索，直接进入本地素材
3. **本地素材搜索** — 读取 `references/known-local-docs.md` 中已摘要的文件，或直接 python-docx 读取关键 docx（见下方关键文件清单）
4. **生成 8 个选题**（本地 4 + 外地 4）
5. **保存输出**：`/mnt/nfs/2026年统战工作/8.信息工作/选题库/经验类选题_YYYYMMDD.md`
6. **不做飞书推送**（cron 无用户交互，选题库文件即为最终交付物）

### 关键本地文件清单（经验类 cron 必读）

> 按此顺序读取，每读完一个文件直接提炼可用选题，优先使用 references 中已有摘要。

| 优先级 | 文件名 | 内容价值 |
|--------|--------|---------|
| ★★★ | `8.信息工作/范文/2026年/4月/4月份下半月信息宣传选题汇总.docx` | 各联络员自提选题草稿，是本地选题最直接的种子来源 |
| ★★★ | `8.信息工作/4.五莲县实行三单管理闭环解决民企诉求/1.0.docx` | 已刊发三单管理机制全文，数字成效完整（办结率93%/满意率97%） |
| ★★★ | `8.信息工作/范文/2026年/4月/（五莲县信息）五莲县三措并举激活基层新阶层统战工作"新"活力.docx` | 已刊发新阶层激活经验，含12乡镇全覆盖数据 |
| ★★★ | `8.信息工作/范文/2026年/4月/（五莲县信息）以统战联络赋能青商兴农 助力五莲高质量发展.docx` | 青商会、助农实践，含具体活动场次和惠及人数 |
| ★★ | `8.信息工作/范文/2026年/4月/五莲县"分层联动"抓实《民族团结进步促进法》普法宣传.docx` | 民族普法数字化创新，1.9万党员覆盖数据 |
| ★★ | `6.巡查部机关/3.材料/4.工作总结及要点/2025/2025年全县统战工作情况.docx` | 年度全局总结，含各领域全年数字数据 |

> ⚠️ **不要把 cron 任务中的 Python 脚本硬编码进执行步骤**。Searxng 地址/端口可能变化，调用 skill 中的 `searxng_search()` 函数或通过 `execute_code` 内联均可，比复制粘贴整个脚本更稳定。

---

## 定时任务（Cron）执行注意事项

> 以下是 cron 凌晨跑每日选题的实战经验，直接照抄任务描述的 Python 代码会导致问题。

### 定时任务必须遵循的标准流程

**经验类定时任务（每天 02:00）**：
1. **读取历史选题文件（排重）** — 读取前1-3天的 `经验类选题_YYYYMMDD.md`，记录已用过的选题关键词，生成时主动规避
2. **Searxng 搜索** — 调用 skill 中的 `searxng_search()`，外地经验搜索词：`统战工作 经验做法 创新 2025`、`民族宗教 工作 亮点 经验 2025`、`对台工作 创新举措 经验 2025`、`统战部 信息工作 经验 交流 2025`
3. **若 Searxng 返回空** → 跳过外网搜索，直接进入本地素材
4. **本地素材搜索** — 读取 `references/known-local-docs.md` 中已摘要的文件，或直接 python-docx 读取关键 docx（见下方关键文件清单）
5. **生成 8 个选题（本地 4 + 外地 4）** — 生成时比对历史文件，已出现过的本地做法类选题（如"三单管理""分层联动""青商兴农"等）不再重复，优先从未挖掘过的领域选题
6. **保存输出**：`/mnt/nfs/2026年统战工作/8.信息工作/选题库/经验类选题_YYYYMMDD.md`
7. **不做飞书推送**（cron 无用户交互，选题库文件即为最终交付物）

### 已重复过的本地选题（2026年5月历史记录，生成时必须规避）

以下为已出现过的本地选题，生成新报告时**必须回避**，从其他未挖掘领域重新选题：

> ⚠️ **重要区分**：
> - **每日选题文件（经验类选题_YYYYMMDD.md）的重复** → 仅属于同一批次的短期排重（05/05~05/08）
> - **范文文件夹已刊发稿件的重复** → 长期排重，必须查 `references/选题排重规则.md`
>
> 两者必须同时检查。生成前读取 `references/选题排重规则.md`，同时读取近3天 `经验类选题_*.md`，两个清单的并集才是完整的禁止关键词集合。

| 首次出现 | 已用选题 | 关键词（须规避） |
|---------|---------|---------------|
| 05/05 | 女企业家商会"木兰荟·企业行" | 木兰荟、女企业家商会 |
| 05/05 | "分层联动"《民族团结进步促进法》普法宣传 | 分层联动、民族团结进步促进法 |
| 05/05 | "三单"管理闭环解决民企诉求 | 三单、三单管理、民企诉求 |
| 05/05 | 青商兴农/青商会 | 青商、青商会、兴农 |
| 05/06 | "三层联动"民族政策法规普法 | 三层联动 |
| 05/06 | 三措并举激活新阶层 | 三措并举、新阶层 |
| 05/06 | 青年企业家商会助农 | 青年企业家商会 |
| 05/07 | "寻美·五莲"新阶层活动 | 寻美·五莲 |
| 05/07 | 五征集团互嵌式发展国家级试点 | 五征集团、互嵌式发展 |
| 05/07 | 牧云谷"石榴籽"幸福乡村 | 牧云谷、石榴籽 |
| 05/07 | "e路同行"电商助农 | e路同行、电商助农 |
| 05/07 | 基地矩阵模式（新阶层） | 基地矩阵 |
| 05/07 | 全流程闭环宗教治理 | 全流程闭环、宗教治理 |
| 05/07 | 数字矩阵大宣传 | 数字矩阵 |
| 05/08 | "三单"闭环管理（重复！） | 三单 |
| 05/08 | "三措并举"新阶层（重复！） | 三措并举 |
| 05/08 | "分层联动"普法（重复！） | 分层联动 |
| 05/08 | 青商兴农（重复！） | 青商兴农 |

**完整禁止关键词清单**（范文文件夹长期覆盖 + 每日文件短期重复）：详细清单见 `references/选题排重规则.md`。

**5月尚未挖掘的本地选题方向（优先使用）：**
- 欧美同学会 / 留学人员统战工作
- 党外干部培养选拔亮点
- 台港澳侨界统战工作动态
- 新的社会阶层人士规范化建设（新联会机制完善）
- 统战干部能力提升 / 培训机制
- 民族宗教风险隐患排查（换个角度）
- 党外知识分子实践基地深化（"芳华同灼"品牌深挖）
- 工商联"企业家登攀大讲堂"品牌深化
- 商会规范化建设（县工商联直属商会建设）

> ⚠️ **排重是强制要求**：生成选题时必须同时读取 (1)`references/选题排重规则.md` 和 (2)近3天 `经验类选题_*.md`，两者禁止关键词合并后才是完整排重范围。本地做法类4个选题，每一个都必须不在上述两个清单之列。

### 关键本地文件清单（经验类 cron 必读）

### 7.1 Searxng 返回 0 条结果
- **检查 JSON 格式**：先跑 `curl "http://localhost:7777/search?q=统一战线&format=json&limit=2"` 看返回是否含 `results` 数组
- **中文编码**：Python 中 query 字符串整体用 `urllib.parse.urlencode({"q": query, ...})` 编码，quote 只用于 URL 路径参数而非整段查询；Searxng 元搜索对 URL 编码格式敏感
- **确认 `search.formats` 包含 `json`**：配置文件 `/mnt/user/appdata/searxng/settings.yml`，必须在 `search.formats` 中加入 `json`，否则 JSON API 返回 403
- **Searxng 容器端口**：容器内 8080，2026年5月实测通过 `localhost:7777` 映射可达
- 容器重启命令（在 Unraid 上）：`docker restart searxng`
- **全部查询都返回空**：执行 curl 验证后仍无 `results`，说明服务不可用，切换到兜底策略（见上方"搜索方式"中的 Searxng 不可用兜底策略）

### 7.2 search_files 对中文关键词返回 0
- **这是工具已知局限**，`target=content` 模式对中文检索失效，无论 file_glob 设什么都返回0
- 改用 `execute_code` 内联 Python（subprocess + python-docx）直接读取 docx 内容，比 terminal heredoc 更稳定（heredoc 的中文引号等特殊字符易引发 SyntaxError）
- 文件名本身含中文可正常搜索：`pattern=*.docx` 按文件名搜索可用，但中文内容检索必须用 python-docx
- `execute_code` 中读 docx 的标准模式：

```python
import subprocess
result = subprocess.run(
    ["python3", "-c",
     "from docx import Document; doc = Document(r'" + fpath.replace("'", "'\"'\"'") + "'); "
     "[print(p.text.strip()) for p in doc.paragraphs if p.text.strip()]"],
    capture_output=True, text=True, timeout=30
)
text = result.stdout  # 或 result.stderr
```

### 7.3 delegate_task 并发数限制
- `max_concurrent_children` 默认值为 3，超过会报错 "Too many tasks: X provided"
- 经验类 cron 搜索外地经验时，如需并行多组关键词，拆分为每批 ≤3 个任务
- 示例（4组关键词拆2批）：
  ```python
  delegate_task(tasks=[group1_keywords, group2_keywords])  # 2个任务，OK
  delegate_task(tasks=[group3_keywords, group4_keywords])  # 第2批
  ```
- 搜索4组不同关键词时，务必拆成2次调用，每次2个并行任务

### 7.3 python-docx 读取报 PackageNotFoundError
- 文件是旧版 `.doc` 格式（非 `.docx`），python-docx 无法读取
- 用 `file "文件名.doc"` 验证，含 "Composite Document File V2 Document" 即为旧格式
- 用 libreoffice 转换：`libreoffice --headless --convert-to txt "文件名.doc" --outdir /tmp/tz_docs/`

---

## 八、注意事项

1. **经验类选题以本地为主**：外地借鉴只参考方法论，不抄具体做法
2. **问题类优先有具体案例**的选题，避免空洞宏观的话题
3. **终稿由 AI 审核合适性**：发现有不合适的地方，打回 DeepSeek 重写
4. **定时任务模型**：凌晨搜索用 deepseek-v4-flash，控制成本
5. **初稿不需要严格控字**：详细完整即可，字数不限
6. **Searxng API 必须加 `format=json` 参数**：否则返回 HTML，解析失败
7. **台湾搜索策略**：用直接搜索话题而非 site 限定。Searxng 的 google/baidu 引擎对 `site:cna.com.tw` 等台湾域名搜索效果差，建议不加 site 限定直接搜具体话题
8. **初稿必须自检**：生成后对照"充实度检查清单"，缺数据/来源/案例必须补充后再发飞书
