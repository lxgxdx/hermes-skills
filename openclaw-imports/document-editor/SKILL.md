---
name: document-editor
description: Advanced document editing for Word and Excel with formal formatting, including Chinese government document standards, table styling, and cell formatting.
metadata:
  {
    "openclaw":
      {
        "emoji": "📝",
        "requires": { "bins": ["python3"] },
      },
  }
---

# Document Editor Skill 📝

高级文档编辑工具，支持Word和Excel深度格式化，完美适配**机关公文格式规范国家标准**。

## 📋 公文格式规范（国家标准）

### 页面设置
| 项目 | 参数 |
|------|------|
| 纸张 | A4（210mm × 297mm） |
| 上边距 | 3.7 cm |
| 下边距 | 3.5 cm |
| 左边距 | 2.8 cm |
| 右边距 | 2.6 cm |
| 文档网格 | 每页22行、每行28字 |
| 行距 | 固定值 28 磅 |

### 字体配置
| 元素 | 字体 | 字号 | 加粗 | 行距 | 与前段空行 |
|------|------|------|------|------|-----------|
| 总标题 | 方正小标宋简体 | 二号 | ❌ | 32磅 | — |
| 标题下单位/署名 | 楷体_GB2312 | 三号 | ❌ | 28磅 | ❌ |
| 主送机关/正文 | 仿宋_GB2312 | 三号 | ❌ | 28磅 | ✅ |
| 一级标题（一、） | 黑体 | 三号 | ❌ | 28磅 | ✅ |
| 二级标题（（一）） | 楷体_GB2312 | 三号 | ❌ | 28磅 | ✅ |
| 三级标题（一是） | 仿宋_GB2312 | 三号 | ✅ | 28磅 | ✅ |
| 落款 | 仿宋_GB2312 | 三号 | ❌ | 28磅 | ✅ |
| 页码 | 宋体 | 四号 | ❌ | 28磅 | — |

> **三级标题格式细节（重要）**：
> - 格式如："一是严格值班纪律。" "二是做好安全检查。" "三是加强检查。"
> - **只加粗标题本身**（到句号为止），解释说明不加粗
> - 示例：**一是严格值班纪律。** 值班人员不得擅自离岗，遇紧急情况应及时报告带班领导。
> - **每个"一是/二是/三是"应作为独立段落**，避免加粗标题连在一起
> - 英文数字使用 Times New Roman 字体

> **微信发送注意**：
> - 表格请用 Markdown 代码块（```）格式发送，微信支持左右滑动浏览
> - 格式如："一是严格值班纪律。" "二是做好安全检查。" "三是加强检查。"
> - **只加粗标题本身**（到句号为止），解释说明不加粗
> - 示例：**一是严格值班纪律。** 值班人员不得擅自离岗，遇紧急情况应及时报告带班领导。
> - **每个"一是/二是/三是"应作为独立段落**，避免加粗标题连在一起
> - 英文数字使用 Times New Roman 字体

> **注意**：方正小标宋字体需要单独安装。

### 段落格式
| 项目 | 参数 |
|------|------|
| 行距 | 固定值 28 磅 |
| 段前/段后 | 0 行 |
| 对齐方式 | 两端对齐（总标题居中，其他全部两端对齐） |
| 首行缩进 | 2 字符（约 0.74 cm），落款右对齐、无缩进 |
| 段落间隔 | 通过空行实现，不用段前段后间距 |
| 段前间距 | 根据标题级别设置 |
| 段后间距 | 根据标题级别设置 |

### 页码规范
- 位置：页面底端（页脚）
- 格式：—　1　—（四号宋体）
- 单页码居右，双页码居左
- 封面、目录、版记不标页码

### 落款日期
- 位置：正文下空若干行，右空四字
- 日期格式：阿拉伯数字，如 2026年2月1日

## 使用方法

### Python代码调用

#### Word文档示例 - 公文格式
```python
from editor import WordDocumentEditor, GONGWEN_FONTS, GONGWEN_PAGE

# 创建公文文档（自动应用公文页面设置）
editor = WordDocumentEditor()

# 添加文档总标题（黑体二号居中）
editor.add_heading("关于XXXX的通知", level=0)

# 添加一级标题（黑体三号）
editor.set_title("一、基本情况")

# 添加二级标题（楷体三号）
editor.set_title("二、工作要求", level=2)

# 添加三级标题（仿宋三号加粗）
editor.set_title("三、具体措施", level=3)

# 添加正文（仿宋三号，首行缩进2字符，固定28磅行距）
editor.add_paragraph("根据上级文件精神，结合本单位实际情况...")

# 添加编号列表
editor.add_numbered_list(["第一项", "第二项", "第三项"], level=1)

# 添加附件说明
editor.add_attachment_note(["1. XXX审批表", "2. YYY汇总表"])

# 添加落款
editor.add_sender_info("XX部门", "2026年2月1日")

# 保存
editor.save("公文模板.docx")
```

#### Excel表格示例
```python
from editor import ExcelDocumentEditor

editor = ExcelDocumentEditor()

# 添加数据
data = [
    ["序号", "姓名", "部门", "基本工资", "绩效奖金", "实发工资"],
    ["1", "张三", "技术部", "8000", "2000", "=D2+E2"],
    ["2", "李四", "市场部", "7500", "2500", "=D3+E3"],
]
editor.add_data(data)

# 格式化表头
editor.format_header(row=1, 
                    font_name="黑体", 
                    font_size=11, 
                    bg_color="D9D9D9")

# 设置列宽
for i in range(1, 7):
    editor.set_column_width(i, [8, 12, 12, 12, 12, 15][i-1])

# 设置行高
editor.set_row_height(1, 20)

# 添加边框
editor.add_borders("all")

# 格式化数字
editor.format_numbers(4, "#,##0.00")
editor.format_numbers(5, "#,##0.00")
editor.format_numbers(6, "#,##0.00")

editor.save("工资表.xlsx")
```

### 命令行使用

```bash
# Word文档操作
python3 ~/.openclaw/skills/document-editor/editor.py word -t '标题' -c '内容' -o output.docx

# Excel文档操作
python3 ~/.openclaw/skills/document-editor/editor.py excel -d '姓名,年龄,城市' -o output.xlsx
```

## 高级功能

### 设置页面边距
```python
editor.set_page_setup(top=3.7, bottom=3.5, left=2.8, right=2.6)
```

### 添加空行
```python
editor.add_empty_line(count=2)  # 添加2个空行
```

### 编号列表
```python
# 一级编号：一、二、三、
editor.add_numbered_list(["第一项", "第二项"], level=1)

# 二级编号：（一）（二）（三）
editor.add_numbered_list(["第一项", "第二项"], level=2)

# 三级编号：1. 2. 3.
editor.add_numbered_list(["第一项", "第二项"], level=3)
```

### 自定义段落格式
```python
editor.add_paragraph(
    "自定义内容",
    font_name="微软雅黑",    # 字体
    font_size=Pt(12),        # 字号
    align="center",          # 对齐方式
    bold=True,               # 加粗
    first_line_indent=True,  # 首行缩进
    line_spacing=Pt(24),     # 行距
    space_before=12,         # 段前间距
    space_after=12           # 段后间距
)
```

## 实际应用场景

### 场景1：制作正式公文
```python
editor = WordDocumentEditor()
editor.set_page_setup()  # 默认公文边距

# 标题
editor.add_heading("关于做好2026年春节期间值班工作的通知", level=0)

# 正文
editor.add_paragraph("各科室、全体员工：")
editor.add_paragraph("根据国务院办公厅通知精神，结合本单位实际情况，现将有关事项通知如下：", first_line_indent=True)

# 一级标题
editor.set_title("一、放假时间")

# 正文
editor.add_paragraph("2026年1月28日至2月4日放假，共8天。", first_line_indent=True)

# 二级标题
editor.set_title("二、值班安排", level=2)
editor.add_paragraph("节日期间安排专人值班，值班电话：010-12345678。", first_line_indent=True)

# 落款
editor.add_empty_line(2)
editor.add_sender_info("综合办公室", "2026年1月20日")

editor.save("值班通知.docx")
```

### 场景2：制作表格
```python
editor = ExcelDocumentEditor()

data = [
    ["姓名", "部门", "基本工资", "绩效奖金", "实发工资"],
    ["张三", "技术部", "8000", "2000", "10000"],
    ["李四", "市场部", "7500", "2500", "10000"],
    ["王五", "财务部", "8500", "1800", "10300"],
]
editor.add_data(data)

# 格式化工
editor.format_header(bg_color="4472C4", font_name="微软雅黑", font_size=11)
editor.set_column_width(1, 12)
editor.set_column_width(2, 12)
editor.set_column_width(3, 15)
editor.set_column_width(4, 15)
editor.set_column_width(5, 15)
editor.set_row_height(1, 22)
editor.add_borders("all")
editor.format_numbers(3, "#,##0.00")
editor.format_numbers(4, "#,##0.00")
editor.format_numbers(5, "#,##0.00")

editor.save("工资表.xlsx")
```

## 技术栈

- **Word**: python-docx 库
- **Excel**: openpyxl 库
- **字体**: 支持所有系统已安装的中文字体
- **兼容性**: 生成的文档可在Microsoft Office、WPS中打开
