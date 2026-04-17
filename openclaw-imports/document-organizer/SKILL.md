---
name: document-organizer
description: Organize documents by analyzing content and categorizing files. Supports PDF, Word, Excel reading and automatic folder organization.
metadata:
  {
    "openclaw":
      {
        "emoji": "📁",
        "requires": { "bins": ["python3"] },
      },
  }
---

# Document Organizer Skill 📁

自动分析文档内容并按类别整理文件到不同文件夹。

## 功能特点

### 📖 支持读取的文档格式
| 格式 | 扩展名 | 说明 |
|------|--------|------|
| PDF | .pdf | 提取文本内容 |
| Word | .docx / .doc | 提取段落文字 |
| Excel | .xlsx / .xls / .csv | 读取表格数据 |
| 文本 | .txt / .md | 读取文本内容 |

### 📂 自动分类规则
| 分类 | 关键词/扩展名 |
|------|---------------|
| 工作 | 报告、方案、计划、总结、周报、日报、会议、纪要 |
| 财务 | 账单、发票、报表、财务、预算、收入、合同 |
| 技术 | 代码、API、技术、文档、开发、手册、教程 |
| PDF文档 | .pdf |
| 表格 | .xlsx / .xls / .csv |
| 文档 | .docx / .doc / .txt / .md |
| 图片 | .jpg / .png / .gif / .bmp / .svg |
| 视频 | .mp4 / .mov / .avi / .mkv |
| 音频 | .mp3 / .wav / .flac |
| 压缩包 | .zip / .rar / .7z / .tar |
| 其他 | 无法分类的文件 |

## 使用方法

### 命令行使用
```bash
# 整理U盘文件夹
python3 ~/.openclaw/skills/document-organizer/organize.py /media/usb

# 整理桌面文档
python3 ~/.openclaw/skills/document-organizer/organize.py ~/Desktop

# 整理指定文件夹
python3 ~/.openclaw/skills/document-organizer/organize.py /path/to/folder
```

### 工作流程
1. 扫描文件夹中的所有文件
2. 读取文档内容（PDF/Word/Excel）
3. 提取关键词并分析分类
4. 创建分类文件夹
5. 自动移动文件到对应文件夹
6. 生成整理报告

## 输出示例

```
📁 开始整理文件夹: /media/usb
============================================================

📄 处理: 2026年工作报告.pdf
   分类: 工作
   → 已移动到: 工作/

📄 处理: 财务报表.xlsx
   分类: 财务
   → 已移动到: 财务/

📄 处理: 产品照片.jpg
   分类: 图片
   → 已移动到: 图片/

============================================================
📊 整理完成！
   总文件数: 25
   创建分类文件夹: 6
   - 工作: 5个文件
   - 财务: 3个文件
   - 图片: 8个文件
   - PDF文档: 4个文件
   - 表格: 2个文件
   - 文档: 3个文件
```

## 自定义分类规则

编辑 `organize.py` 中的 `DEFAULT_CATEGORIES` 字典来自定义分类规则：

```python
DEFAULT_CATEGORIES = {
    "你的分类": ["关键词1", "关键词2", ".扩展名"],
    "项目A": ["项目A", "ProjectA", ".aiproj"],
}
```

## 技术实现

- **PDF读取**: 使用 pypdf 库
- **Word读取**: 使用 python-docx 库
- **Excel读取**: 使用 pandas + openpyxl 库
- **文件操作**: Python pathlib + shutil
