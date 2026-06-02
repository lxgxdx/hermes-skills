# 信息稿 docx 排版铁律（2026-06-02 确立）

> **来源**：2026-06-02 飞书 185500 session 完成首篇《常住台胞医保先行先试暴露统一标准缺位值得关注》1.0 草稿后确立。本文件是信息稿 docx 排版的**唯一权威标准**。

## 1. 字体/字号/对齐（与 4 月份 8 篇范本 100% 对齐）

| 元素 | 字体 | 字号 | 对齐 |
|------|------|------|------|
| **署名** | 仿宋 | 16pt | 居中 |
| **标题** | 方正小标宋简体 | 22pt（二号） | 居中 |
| **章节标题**（一/二/三、表现/原因/建议） | 黑体 | 14pt（四号） | 默认（左对齐） |
| **正文** | 仿宋 | 12pt（小四） | 默认（首行缩进 2 字符） |
| **小标题首句** | 仿宋 | 12pt | **加粗** |

## 2. 页面设置

| 项目 | 值 |
|------|------|
| 页面尺寸 | A4 21.59×27.94cm |
| 上边距 | 2.54cm |
| 下边距 | 2.54cm |
| 左边距 | 3.18cm |
| 右边距 | 3.18cm |
| 行距 | 1.5 倍 |
| 首行缩进 | 2 字符 |

## 3. 目录命名约定

```
/mnt/nfs/2026年统战工作/8.信息工作/
├── 1.二手交易平台非法传度授箓问题亟需引起重视/  ← 数字编号递增
├── 2.选题名称/
├── 3.选题名称/
├── 4.选题名称/
├── 5.台陆委会污名化两岸宗教交流为统战工具/
├── 6.选题名称/
└── 7.常住台胞医保先行先试暴露统一标准缺位值得关注/  ← 6/2 首篇用 7
    ├── 1.0_草稿.docx  ← 起草稿
    ├── 终稿.docx      ← DeepSeek 终稿
    └── IMG_*.png      ← 素材照片（如有）
```

**编号分配规则**：
- 数字编号 = 已占用序号，**不可重复**
- 新信息稿从下一个未占用数字开始（如 1-6 已用，新稿用 7）
- 用户提到编号时按本地实际目录确认，不要凭印象

## 4. 参考链接排版技巧（6/2 实测坑）

### 4.1 坑：md 源被空行拆段

如果 md 源是：
```markdown
[1] 标题A
https://URL_A

[2] 标题B
https://URL_B
```

直接生成 docx 时，`[1] 标题A` 和 `https://URL_A` 会被拆成两段。

### 4.2 解决：md 起草时合到一段

```markdown
[1] 标题A https://URL_A
[2] 标题B https://URL_B
```

或生成 docx 后用 Python 合并相邻的非空行（脚本见 `/tmp/md_to_docx.py`，6/2 已 patch）。

### 4.3 最终段落格式

每条参考链接独立成段，格式：
```
[序号] 标题（日期），发布机构，URL
```

示例：
```
[1] 《湖南省医保局关于解决常住台胞医疗保障有关问题推动落实同等待遇的答复》（2025-07-23），湖南省医疗保障局，https://...
[2] 《关于促进两岸经济文化交流合作的若干措施》（2019-11-04），国务院台湾事务办公室，https://www.gwytb.gov.cn/zccs/zccs_61195/a26tacs/
```

## 5. 用户校对常见改动点（6/2 实战推断）

用户从飞书拿走 1.0 草稿后会去电脑校对，可能改动：

- **内容精简**：某段太长，删减重复表述
- **补数据**：某个数据要进一步核实/补充
- **改联系人**："联系人：XXX" 改成具体人名（信息稿末尾固定）
- **参考链接改脚注**：部分信息稿把参考链接做成 Word 脚注而非文末列表

→ 校对后再走 1.0 → 终稿的流程。

## 6. 完整生成流程（与 document-editor skill 配合）

```python
import sys
sys.path.insert(0, '/home/lxgxdx/.hermes/skills/ppt-work/document-work/document-editor')
from editor import WordDocumentEditor
from docx.shared import Pt, Cm

editor = WordDocumentEditor()

# 页面设置
editor.set_page_setup(
    page_width=Cm(21.59),
    page_height=Cm(27.94),
    top=Cm(2.54), bottom=Cm(2.54),
    left=Cm(3.18), right=Cm(3.18)
)

# 署名（仿宋 16pt 居中）
editor.add_paragraph('五莲县委统战部', font_name='仿宋', font_size=Pt(16), align='center')

# 标题（方正小标宋简体 22pt 居中）
editor.add_paragraph(
    '常住台胞医保先行先试暴露统一标准缺位值得关注',
    font_name='方正小标宋简体', font_size=Pt(22), align='center'
)

# 章节标题（黑体 14pt）
editor.add_paragraph('一、表现特征', font_name='黑体', font_size=Pt(14))

# 正文（仿宋 12pt 首行缩进 2 字符）
editor.add_paragraph(
    '正文内容...',
    font_name='仿宋',
    font_size=Pt(12),
    first_line_indent_chars=2,
    line_spacing=1.5
)

# 小标题首句加粗
p = editor.add_paragraph(
    '小标题首句内容...',
    font_name='仿宋', font_size=Pt(12), bold=True,
    first_line_indent_chars=2, line_spacing=1.5
)

# 参考链接
editor.add_paragraph('参考数据源', font_name='黑体', font_size=Pt(12))
editor.add_paragraph(
    '[1] 标题（日期），发布机构，URL',
    font_name='仿宋', font_size=Pt(10), line_spacing=1.5
)

# 联系人
editor.add_paragraph('联系人：XXX  联系方式：XXX', font_name='仿宋', font_size=Pt(12))

# 保存并验证文件大小
path = '/mnt/nfs/2026年统战工作/8.信息工作/N.选题名称/1.0_草稿.docx'
editor.save(path)
import os
size = os.path.getsize(path)
assert size > 0, f"❌ 文件大小为 0 字节：{path}"
print(f"✅ 文件已落地：{path}，大小：{size} 字节")
```

## 7. 验证清单

每次生成信息稿 docx 后逐项自检：

- [ ] 标题居中 + 方正小标宋简体 22pt
- [ ] 章节标题黑体 14pt
- [ ] 正文仿宋 12pt 首行缩进 2 字符
- [ ] 页面 A4 + 上下 2.54cm + 左右 3.18cm
- [ ] 行距 1.5 倍
- [ ] 小标题首句加粗
- [ ] 参考链接独立段落（每条一段）
- [ ] 联系人置于文末
- [ ] 文件大小 > 0 字节（落盘验证）
- [ ] 数字编号不与已用编号冲突

## 8. 已知局限

- **不能直接跑 Python heredoc 中文**：用 `write_file` 写脚本 → `terminal` 执行
- **Word 渲染问题**：仅设置 `run.font.name` 不够，必须设置 `w:eastAsia` 才能让 Windows Word 正确渲染中文
- **飞书预览 vs Word 渲染**：飞书 Web 预览可能正常，下载到 Windows Word 打开字体可能错位
