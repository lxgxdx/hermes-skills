# 演讲者备注（Speaker Notes）嵌入机制

## 两种嵌入方式

### 方式一：自动嵌入（推荐）

`svg_to_pptx.py` 在导出时**自动**将 `notes/` 目录下的 markdown 文件注入为每页备注。

**前提条件**：先运行 `total_md_split.py`：

```bash
python scripts/total_md_split.py <项目路径>
# 生成 notes/01_cover.md, notes/02_section.md, ... 等分页文件
```

每页对应的 markdown 文件名格式：**`<序号>_<slug>.md`**

例如：
```
notes/
  01_cover.md       → Slide 1 的备注
  02_why_ai.md     → Slide 2 的备注
  03_three_waves.md → Slide 3 的备注
  ...
```

**验证方法**：生成后用 python-pptx 读取备注内容：
```python
from pptx import Presentation
prs = Presentation("output.pptx")
for i, slide in enumerate(prs.slides):
    print(f"Slide {i+1}: {slide.notes_slide.notes_text_frame.text[:50]}")
```

### 方式二：事后手动写入（适合精修备注内容）

当需要更精细地控制备注内容时（如多段备注、长篇讲稿），用 python-pptx 直接写入：

```python
from pptx import Presentation

prs = Presentation("output.pptx")
for i, slide in enumerate(prs.slides):
    notes = slide.notes_slide.notes_text_frame
    # 读取对应的 notes/<序号>_<slug>.md 文件内容
    notes_text = open(f"notes/{i+1:02d}_*.md").read()  # 自定义逻辑
    notes.text = notes_text
prs.save("output_with_notes.pptx")
```

## 分页文件命名规则

**文件名必须与 PPT 页码严格对应**：
- `svg_output/` 中的 SVG 文件：`01_cover.svg`, `02_why_ai.svg`, ...
- `notes/` 中的 markdown 文件：`01_cover.md`, `02_why_ai.md`, ...

**slug 部分**可自由命名，但序号必须从 `01` 开始、连续递增。

## 实际验证记录（2026-05-06）

生成15页机关AI培训PPT，流程：
1. 直接写15个SVG到 `svg_output/`（跳过 `total_md_split.py`）
2. 运行 `svg_to_pptx.py -s svg_output -o /tmp/test.pptx`
3. 结果：**已有备注数据**（从之前某次 `total_md_split.py` 运行遗留）

说明：`svg_to_pptx.py` 会自动读取 `notes/` 目录下的分页 markdown，无需显式调用 `total_md_split.py`（只要 `notes/` 目录和分页文件存在）。

**最佳实践**：始终先运行 `total_md_split.py`，确保备注分页文件最新。

## 备注格式（markdown → PPTX）

markdown 内容会按段落（`\n\n` 分隔）转换为 PPTX 中的多个文本段落（`<a:p>`）。

保留：普通文本、emoji（如 ✅、🎯）、数字编号。

不保留（会变成纯文本）：markdown 标题语法（`#`、`##`）、链接、`**bold**` 等富文本标记。

如需在备注中使用富文本，需要直接操作 XML。
