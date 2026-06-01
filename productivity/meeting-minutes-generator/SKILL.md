---
name: meeting-minutes-generator
description: 将飞书妙记/Whisper转录的部务会录音文字稿，按党政公文格式整理为Word会议记录。
category: productivity
---

# 会议记录生成器

## 触发条件

用户说"整理会议记录"或提供了录音文字稿文件路径时使用。

## 前置确认（整理前必须询问）

1. **请假人员**：本次部务会有无请假成员，缺席者归入"请假人员"
2. **列席人员**：除孙秀美（记录）、李国栋（办公室主任）外，议题表中标注的临时列席人员是谁
3. **说话人映射**：文字稿中非固定称呼（老谢/俊芳/秀美等）分别对应哪位成员

## 部务会成员固定名单

| 姓名 | 分管领域 | 发言规则 |
|------|---------|---------|
| 张道伟 | 主持（主要领导） | 三重一大末位发言 |
| 徐军光 | 主持日常工作 | 三重一大末位发言 |
| 苑芳江 | 党建、共青团妇、精神文明 | 副科级，不参与三重一大表决 |
| 席光锋 | 党外知识分子、民主党派、职教社 | 副科级，不参与三重一大表决 |
| 徐慎文 | 新的社会阶层人士、侨务、侨联 | 副科级，不参与三重一大表决 |
| 李兵 | 民族宗教 | 三重一大末位发言 |
| 潘姿安 | 办公室、台港澳、信息宣传 | 三重一大末位发言（本次请假） |
| 孙秀美 | 记录 | 不发言，归入出席人员 |
| 李国栋 | 办公室主任 | 不发言，归入列席人员 |

**三重一大事项末位发言顺序**：潘姿安 → 李兵 → 徐军光 → 张道伟（主持人末位）
- 本次潘姿安请假，实际顺序：李兵 → 徐军光 → 张道伟

## 文件识别与读取

**议题表**（.doc/.docx 二进制格式，不能直接 python-docx 读取）：
```bash
libreoffice --headless --convert-to txt:"Text" "会议议题.doc" --outdir /tmp/
cat /tmp/会议议题.txt
```

**文字稿**（.docx 格式）：
```bash
# 方式1：python-docx 直接读
python3 -c "
from docx import Document
doc = Document('文字记录：REC0091 2026年6月1日.docx')
for p in doc.paragraphs:
    print(p.text)
"

# 方式2：libreoffice 转 txt
libreoffice --headless --convert-to txt:"Text" "文字记录：REC0091 2026年6月1日.docx" --outdir /tmp/
```

**模板文件**（会议记录（模板）.docx）：
```bash
libreoffice --headless --convert-to txt:"Text" "会议记录（模板）.docx" --outdir /tmp/
```

## 格式规范

### 标题层级（按模板）

| 层级 | 格式 | 字体 | 加粗 | 字号 |
|------|------|------|------|------|
| 大标题 | 文件名 | 方正小标宋简体 | 否 | 22pt，居中 |
| 副标题 | （2026年第N次部务会） | 仿宋 | 否 | 16pt，居中 |
| 议题标题 | 一、学习…… | 黑体 | 否 | 16pt |
| 分管汇报小标题 | （一）XXX同志汇报…… | 楷体 | 否 | 16pt |
| 正文 | 会议内容段落 | 仿宋 | 否 | 16pt，首行缩进 |
| 编号条目 | 1. 内容 | 仿宋 | 否 | 16pt，首行缩进 |

### 排版规范

- **行间距**：固定值 28 磅（所有段落）
- **页边距**：上下左右各 2.54cm
- **首行缩进**：正文段落首行缩进 0.74cm（2字符）；标题不缩进
- **对齐**：正文两端对齐（JUSTIFY）；大标题/副标题居中

### 格式禁忌

- 正文不使用斜体、不使用 `*` 包围
- 不嵌套【（一）领学】【（二）研究贯彻意见】等层级

## 人员列席格式

```
出席人员：
张道伟、徐军光、苑芳江、席光锋、徐慎文、李　兵、孙秀美

请假人员：
潘姿安

列席人员：
李国栋、朱芳、丰朔
```

- 只写姓名，不用职务，同类用顿号隔开
- 孙秀美归入**出席人员**，李国栋归入**列席人员**
- 临时列席人员（朱芳、丰朔等）**不出现在人员列表**，仅在对应议题标题括号内标注

## 议题处理规则

### 领学类议题（一、二）
- 领学人领学一句概括 + 会议指出/强调合并表述
- 不逐句记录领学过程

### 审议类议题（三：三重一大）
- 汇报人说明 → 分管领导逐一发言（原话，末尾表态）
- 表决结果：经审议，原则通过，修改完善后印发执行
- 格式：`姓名：同意` 或 `姓名：同意，+具体意见`

### 研究类议题（四：信息宣传）
- 情况通报（一句概括）+ 领导要求（分条：一要、二要……）
- 不逐句记录讨论过程

### 汇报类议题（五）
- 按发言人分块，每位分管领导独立小标题
- 事项用分号分隔，重要成果单独成句
- 领导对汇报的点评跟在汇报人之后

### 讲话类议题（六）
- 归纳为3-5条要点（一要、二要……），不逐句转写

## 工作流程

1. **读议题表**：libreoffice 转 txt，确认议题顺序和列席人员
2. **读文字稿**：两个 REC 文件通读一遍，标记说话人编号对应的发言内容
3. **推断说话人映射**：对照①议题表领学/汇报人 ②文字稿中说话内容，交叉验证
4. **询问用户确认**：请假人员、临时列席人员、说话人映射是否正确
5. **生成文档**：按本 skill 格式规范写 Python 脚本生成 Word
6. **保存**：`/mnt/nfs/2026年统战工作/1.办公室/9.部务会/日期/会议记录_YYYY年第N次部务会.docx`

## 常见错误（踩坑记录）

### ❌ 议题内容搞反（v2/v3版）
原因：看到议题名"民族工作"就假设是李兵，没对照文字稿核实
正确：议题一/二的内容完全由文字稿决定，议题表只决定顺序

### ❌ 说话人映射套用上次
每次会议说话人编号对应的人名不同，必须通过领学人说了什么+议题表领学人是谁来交叉验证

### ❌ 嵌套层级过多
模板格式不用【（一）领学】【（二）研究贯彻意见】，议题直接一、二、三标出

### ❌ 人员带职务列示
模板格式只写姓名，不用职务，不标注"不发言，负责记录"

## 参考文件

- `references/build_meeting_record_v5.py` — v5版生成脚本（含完整代码模板）
- `会议记录（模板）.docx` — 用户提供的格式模板（参照此格式生成）

## 核心代码片段

```python
FONT_FZXBSJK = "方正小标宋简体"
FONT_HT = "黑体"
FONT_KT = "楷体"
FONT_FS = "仿宋"

def set_font(run, font_name, size, bold=False):
    run.font.name = font_name
    run.font.size = Pt(size)
    run.font.bold = bold
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)

def set_lnSpc(p, val=28):
    pPr = p._element.get_or_add_pPr()
    lSpc = OxmlElement('w:lnSpc')
    lSpcVal = OxmlElement('w:lnSpcVal')
    lSpcVal.set(qn('w:val'), str(val))
    lSpc.append(lSpcVal)
    pPr.append(lSpc)

def info(doc, text, sb=0, sa=3):
    """正文段落 仿宋 首行缩进"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after = Pt(sa)
    p.paragraph_format.first_line_indent = Cm(0.74)
    run = p.add_run(text)
    set_font(run, FONT_FS, 16)
    set_lnSpc(p)
    return p

def agenda(doc, text):
    """议题标题 黑体"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    set_font(run, FONT_HT, 16, bold=False)
    set_lnSpc(p)
    return p
```
