---
name: tz-file-organizer
description: 统战重要会议材料整理。从备份文件夹（补充材料）批量整理到年度重要会议目录，并更新Excel会议目录。触发词：整理会议材料/备份目录/补充材料/重要会议/会议目录.xlsx/台账/批量导入Excel/日期核实/文件夹命名
---

# tz-file-organizer — 统战重要会议材料整理

从备份目录批量整理重要会议材料到年份目录，并更新Excel会议目录。

**⚠️ 重要路径提醒：**
- 目标目录：`.../6.备份/1.重要会议/YYYY`（正确）
- 易混目录：`.../3.材料/1.重要会议/`（不要操作）

操作前必须 `ls /mnt/nfs/.../6.备份/` 确认正确路径。

---

## Self-Evaluation Rubric（自评维度）

| 维度 | 满分 | 得分 | 扣分原因 |
|------|------|------|----------|
| Frontmatter质量 | 8 | __/8 | description字符数、触发词覆盖 |
| 工作流清晰度 | 15 | __/15 | 步骤是否编号、每步是否有输入/输出 |
| 边界条件覆盖 | 10 | __/10 | 异常fallback是否完整 |
| 触发词精准度 | 7 | __/7 | 触发词是否具体（非泛泛"整理材料"） |
| 路径正确性 | 10 | __/10 | 路径引用是否有效 |
| 依赖声明 | 10 | __/10 | 是否声明必需工具和环境 |
| 工具调用准确率 | 10 | __/10 | 命令是否可直接执行 |
| 输出格式正确率 | 10 | __/10 | 示例是否匹配真实输出格式 |
| 异常处理有效性 | 10 | __/10 | 错误→原因→修复是否完整 |
| 用户意图匹配 | 10 | __/10 | 触发词与实际场景的匹配度 |

**总分：__/100**

---

## 依赖声明

**必需命令：** `find`, `strings`, `pdftotext`, `tesseract`
**必需Python库：** `openpyxl`, `zipfile`（内置）, `re`（内置）, `subprocess`（内置）
**运行方式：** 在 venv 中执行（`source venv/bin/activate`）

---

## 核心路径

| 路径 | 说明 |
|------|------|
| `/mnt/nfs/YYYY年统战工作/6.巡查部机关/6.备份/补充材料/` | 源目录（4类文件夹都在这里） |
| `/mnt/nfs/.../6.备份/1.重要会议/YYYY/` | 目标目录 |
| `/mnt/nfs/.../6.备份/会议目录.xlsx` | Excel台账 |

---

## 整理工作流（4步）

### 步骤1：完整扫描补充材料

**输入：** 补充材料目录路径
**输出：** 所有子文件夹列表 + 每类文件夹的内容

**补充材料包含4类文件夹（缺一不可）：**
1. `YYYY年` — 常规年度会议
2. `YYYY年相关会议材料` — 专题会议
3. `YYYY全县统战工作会议` — 全县统战工作会议全套
4. `YYYY年M月DD日XXX` — 单场重要会议

```bash
SRC="/mnt/nfs/.../6.备份/补充材料"

# 扫描全部子文件夹
find "$SRC" -maxdepth 1 -type d | sort

# 逐类检查内容（以2024年为例）
for y in 2022 2023 2024 2025 2026; do
  for subdir in "$SRC/${y}年" "$SRC/${y}年相关会议材料" "$SRC/${y}全县统战工作会议"; do
    if [ -d "$subdir" ]; then
      echo "━━━ $(basename $subdir) ━━━"
      ls "$subdir"
    fi
  done
done
```

---

### 步骤2：提取并核实日期

**输入：** 会议文件夹路径
**输出：** 确认后的 `月日` + 会议名称

**优先级：通知"定于X月X日" > 讲话文件名日期 > 议程表日期 > 文件夹名日期**

**从 .docx 读日期：**
```python
import zipfile, re

def read_docx_date(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8')
        text = re.sub(r'<[^>]+>', '', xml)
        # 通知常用"定于12月16日"
        ding = re.findall(r'定于(\d{1,2}月\d{1,2}日)', text)
        # 正文日期"2024年12月16日"
        dates = re.findall(r'(20\d{2}年\d{1,2}月\d{1,2}日)', text)
        return ding[:1], dates[:2]
```

**从 .doc 读日期（python-docx 无法读取 .doc）：**
```bash
strings "/path/to/通知.doc" | grep -E "202[0-9]年[0-9]+月[0-9]+日" | head
```

**从讲话文件名读日期（格式"讲话（2024年2月28日）"）：**
```python
import re
dates = re.findall(r'（(\d{4}年\d{1,2}月\d{1,2}日））', text)
# 例：（2024年2月28日）→ 提取为 2月28日
```

**从 PDF 读日期：**
```bash
pdftotext -layout "/path/to/file.pdf" - 2>/dev/null | grep -E "月|日|202"
strings "/path/to/file.pdf" 2>/dev/null | grep -E "D:202" | head -3
```

**OCR 图片（微信截图）：**
```bash
tesseract /path/to/image.jpg stdout -l chi_sim 2>/dev/null | head -20
```

**日期陷阱：**
- `定于12月16日（星期五）上午9:00` → 实际是 **12月16日**（不用管括号内）
- 讲话文件 `(2024年2月28日)` → 通常就是会议日期
- 议程表 `2022年8月3日 9:00` → 实际是 **8月3日**
- ⚠️ "1月上旬"、"8月下旬" → **日期未定**，需从其他文件交叉确认

---

### 步骤3：创建目标文件夹并复制文件

**输入：** 步骤2的日期+名称 + 源文件
**输出：** 新建的目标文件夹

**命名格式：** `月日+会议名称`，如 `4月18日文旅系统联合侨联成立`

**同日多会：** 同日不同名目分开命名：
- `1月24日教体系统联合侨联成立`
- `1月24日卫健系统联合侨联成立`

```bash
SRC="/mnt/nfs/.../6.备份/补充材料/2024年"
DST="/mnt/nfs/.../6.备份/1.重要会议/2024"

mkdir -p "$DST/4月18日文旅系统联合侨联成立"
cp -n "$SRC/源文件夹/"* "$DST/4月18日文旅系统联合侨联成立/" 2>/dev/null
echo "完成 ✓"
```

---

### 步骤4：更新Excel会议目录

**输入：** 新增条目列表
**输出：** 重新排序并编号的Excel

**Excel格式：**

| 列 | 内容 | 示例 |
|----|------|------|
| A | 序号 | 1 |
| B | 年份 | 2024 |
| C | 开会日期（MM.DD） | 04.18 |
| D | 会议名称 | 党外人士座谈会 |
| E | 原文件夹名称 | 2024.04.18_文旅系统联合侨联成立 |
| F | 备注 | — |

```python
import openpyxl

src = '/mnt/nfs/.../6.备份/会议目录.xlsx'
wb = openpyxl.load_workbook(src)
ws = wb.active

# 用"原文件夹名称"(列E)去重，防止同日多会误合并
seen_folders = set()
valid_rows = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] is not None and isinstance(row[0], int):
        folder = row[4]
        if folder not in seen_folders:
            seen_folders.add(folder)
            valid_rows.append(list(row))

# 新增条目：(序号留空, 年份, MM.DD, 会议名称, YYYY.MM.DD_名称, 备注)
new_entries = [
    (None, '2024', '04.18', '文旅系统联合侨联成立', '2024.04.18_文旅系统联合侨联成立', None),
]

for e in new_entries:
    if e[4] not in seen_folders:
        seen_folders.add(e[4])
        valid_rows.append(list(e))

# 按年份+MM.DD排序
def sort_key(row):
    year = int(row[1])
    mmdd = row[2]  # '04.18'
    month = int(mmdd.split('.')[0])
    day = int(mmdd.split('.')[1])
    return (year, month, day)

valid_rows.sort(key=sort_key)

# 重新编号
for i, row in enumerate(valid_rows, start=1):
    row[0] = i

# 重建工作表
while ws.max_row > 1:
    ws.delete_rows(ws.max_row)

headers = ['序号', '年份', '开会日期', '会议名称', '原文件夹名称', '备注']
for col, h in enumerate(headers, 1):
    ws.cell(row=1, column=col, value=h)

for i, row_data in enumerate(valid_rows, start=2):
    for col, val in enumerate(row_data, 1):
        ws.cell(row=i, column=col, value=val)

wb.save(src)
print(f"已写入 {len(valid_rows)} 条记录 ✓")
```

---

## 日期核实（步骤2的核心）

**必须从通知的"定于"字段提取真实开会日期，不能用文件夹名或修改时间。**

```python
import zipfile, re, subprocess, os

def get_dates_from_folder(folder_path):
    """从文件夹内所有文件提取日期信息，用于交叉验证"""
    for fname in sorted(os.listdir(folder_path)):
        path = f'{folder_path}/{fname}'
        if not os.path.isfile(path):
            continue
        try:
            if fname.endswith('.docx'):
                with zipfile.ZipFile(path) as z:
                    content = z.read('word/document.xml').decode('utf-8')
                    clean = re.sub(r'<[^>]+>', '', content)
                    ding = re.findall(r'定于(\d{1,2}月\d{1,2}日)', clean)
                    dates = re.findall(r'(20\d{2}年\d{1,2}月\d{1,2}日)', clean)
                    yield fname, ding, dates
            elif fname.endswith('.doc'):
                result = subprocess.run(['strings', path], capture_output=True, timeout=5)
                text = result.stdout.decode('utf-8', errors='ignore')
                ding = re.findall(r'定于(\d{1,2}月\d{1,2}日)', text)
                dates = re.findall(r'(20\d{2}年\d{1,2}月\d{1,2}日)', text)
                yield fname, ding, dates
        except:
            pass

# 使用示例
ROOT = '/mnt/nfs/.../6.备份/1.重要会议/2024'
for fname in os.listdir(ROOT):
    folder = f'{ROOT}/{fname}'
    print(f"【{fname}】")
    for fn, ding, dates in get_dates_from_folder(folder):
        if ding or dates:
            print(f"  通知日期={ding[:1]}, 正文日期={dates[:1]}")
```

**历史错误记录（已核实）：**

| 错误记录 | 正确日期 | 问题 |
|---------|---------|------|
| `2022.07.31_半年情况通报会` | 8月16日 | 通知"定于8月16日" |
| `2022.08.06_统战工作领导小组` | 8月3日 | 议程表显示8月3日 |
| `2022.12.15_县委统战工作会议` | 12月16日 | 通知"定于12月16日" |
| `2025.12.10_涉侨纠纷多元化解工作站` | 12月11日 | 公众号稿确认12月11日 |

---

## 验证步骤

```bash
# 1. 检查各年份文件夹数量
for y in 2022 2023 2024 2025 2026; do
  echo "=== $y ==="
  ls /mnt/nfs/.../6.备份/1.重要会议/$y/ | wc -l
done

# 2. 检查Excel行数
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('/mnt/nfs/.../6.备份/会议目录.xlsx')
ws = wb.active
print(f'Excel共 {ws.max_row-1} 条记录')
"

# 3. 抽样核实日期（随机抽3个文件夹读通知）
ROOT='/mnt/nfs/.../6.备份/1.重要会议/2024'
for folder in $(ls $ROOT | shuf | head -3); do
  echo "━━━ $folder ━━━"
  ls "$ROOT/$folder/"
done
```

---

## 异常处理索引

| 情况 | 解决方法 |
|------|---------|
| `.doc` 读不出 | 改用 `strings` 命令 |
| strings 超时 | 加 `timeout=5` 参数 |
| PDF 无文字 | 用 `pdftotext` 或读 `D:` 元数据 |
| 微信截图 | 用 `tesseract -l chi_sim` OCR |
| 同日多会 | 用文件夹名（列E）去重，不用日期 |
| 日期模糊（"1月上旬"） | 从其他文件交叉确认，找到具体日期才能归档 |
| Excel 序号乱 | 重新遍历+排序后重建 |
| 目标路径选错 | 先 `ls /mnt/nfs/.../6.备份/` 确认 |
