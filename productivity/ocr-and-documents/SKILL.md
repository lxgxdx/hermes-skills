---
name: ocr-and-documents
description: >
  文档/PDF/图片内容提取工作流。当前模型为 minimax-cn/MiniMax-M3（有原生多模态视觉），
  优先用 vision_analyze 直接读取 PDF/图片/扫描件。M2.7 无视觉才回退到 EasyOCR
  流水线（192.168.88.68:8082）。doc/docx/wps 仍走 libreoffice 转 txt。触发词：
  提取文字/读取PDF/扫描件/识别图片/OCR/文件内容/读文件/看图。
tags: ["OCR", "PDF", "文档解析", "多模态", "vision", "扫描件"]
category: productivity
---

# 文档/PDF/图片内容提取

**核心原则（M3 时代）：优先 vision_analyze，回退 OCR。**

---

## ⚡ QuickRef

| 文件类型 | 首选方法 | 兜底 |
|---------|---------|------|
| **图片（jpg/png/webp/截图）** | `vision_analyze` | EasyOCR（仅需 bbox 时）|
| **PDF 文字型**（pdftotext 有输出）| `pdftotext` | `vision_analyze` |
| **PDF 扫描件**（pdftotext 空）| `vision_analyze`（pdftoppm 转图后）| EasyOCR |
| **docx/doc/wps** | `libreoffice --convert-to txt` | ❌ 无法 vision |
| **手写笔记/低质量扫描** | `vision_analyze` | EasyOCR + 人工核 |

---

## 🆕 M3 多模态范式（2026-06 确立）

**当前对话模型是 M3**（`minimax-cn/MiniMax-M3`），**有原生多模态视觉**：
- 可直接"看"任何图片/PDF
- 不需要先 OCR 抽文字再喂给模型
- 准确度比 EasyOCR 高（特别是手写/混合排版/表格）

**`vision_analyze` 工具签名：**
```python
vision_analyze(
    image_url: str,    # 本地路径 / http(s) URL / data: URL
    question: str      # 你想问的（"提取所有文字"/"这是哪份文件"/"表格内容"）
)
```

**支持格式：** png, jpg, jpeg, webp, gif（静态）, pdf（M3 原生支持）

---

## 工作流（决策树）

```
要读文件内容 →
  ├─ 文件类型？
  │
  ├─ .docx/.doc/.wps → libreoffice 转 txt
  │   libreoffice --headless --convert-to txt --outdir /tmp file.docx
  │   cat /tmp/file.txt
  │
  ├─ 图片（png/jpg/截图）→ 直接 vision_analyze
  │   vision_analyze(image_url="/path/to/img.png",
  │                  question="提取所有文字" 或 "这是什么文件？")
  │
  └─ .pdf →
      ├─ 试 pdftotext（最快）
      │   pdftotext -l 2 file.pdf -    # 首页2页
      │   ├─ 有文字 → 用文字
      │   └─ 空（<10字节）→ 是扫描件
      │
      └─ 扫描件 → vision_analyze
          # 方式 A：直接传 PDF 路径（M3 一般支持）
          vision_analyze(image_url=pdf_path,
                        question="这是哪个单位的什么文件？标题/落款/正文要点？")
          
          # 方式 B：先转图片（更稳）
          pdftoppm -f 1 -l 1 -png -r 200 file.pdf /tmp/p
          vision_analyze(image_url="/tmp/p-1.png", question="...")
```

---

## 代码片段（Hermes Python 环境）

### 读 PDF（智能判断文字型 vs 扫描件）

```python
import subprocess
from hermes_tools import vision_analyze

def read_pdf(pdf_path, max_pages=5, question="提取所有文字内容"):
    # 1. 先试 pdftotext
    result = subprocess.run(
        ['pdftotext', '-l', str(max_pages), pdf_path, '-'],
        capture_output=True, text=True, timeout=30
    )
    text = result.stdout.strip()
    if len(text) > 50:  # 文字型 PDF
        return {'method': 'pdftotext', 'text': text}
    
    # 2. 扫描件 — 转图片 + vision_analyze
    img_prefix = '/tmp/pdf_page'
    subprocess.run(['pdftoppm', '-f', '1', '-l', '1', '-png', '-r', '200',
                    pdf_path, img_prefix], timeout=30)
    img_path = f'{img_prefix}-1.png'
    
    return {
        'method': 'vision_analyze',
        'result': vision_analyze(image_url=img_path, question=question)
    }
```

### 读图片

```python
from hermes_tools import vision_analyze

# 截图
vision_analyze(image_url='/tmp/screenshot.png',
              question="这个截图里有什么？请详细描述")

# 扫描件图片
vision_analyze(image_url='/tmp/scan.jpg',
              question="提取所有文字，按段落格式输出")
```

### 读 doc/docx/wps

```python
import subprocess
import os

def read_doc(path, outdir='/tmp/extract'):
    os.makedirs(outdir, exist_ok=True)
    subprocess.run([
        'libreoffice', '--headless', '--convert-to', 'txt',
        '--outdir', outdir, path
    ], timeout=120, capture_output=True)
    base = os.path.splitext(os.path.basename(path))[0]
    txt_path = os.path.join(outdir, base + '.txt')
    with open(txt_path) as f:
        return f.read()
```

---

## 何时回退到 EasyOCR（192.168.88.68:8082）

**只有这些情况走 OCR：**
1. **M2.7 对话**（无视觉能力）— 别无选择
2. **需要 bbox 坐标**（如要画红框/裁剪特定区域）— vision_analyze 不返回坐标
3. **vision_analyze 失败/超时**（极少发生）
4. **批量自动化脚本**（脚本环境里没有 LLM 上下文）— 用 OCR 拿纯文本

**EasyOCR 调用规范：**
```bash
# 单图
curl -s -X POST http://192.168.88.68:8082/ocr \
  -F "image=@/path/to/img.png" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for r in d.get('results', []):
    print(r['text'], r.get('confidence', 0))
"

# ⚠️ 字段名是 image 不是 file（这是常见踩坑点）
# 错误用法：-F "file=@..." → {"detail": "Field required: image"}
```

**健康检查：**
```bash
curl -s http://192.168.88.68:8082/health
```

---

## 性能与质量对比

| 指标 | vision_analyze (M3) | EasyOCR |
|------|---------------------|---------|
| 速度（单页 PDF） | 2-3 秒 | 1-2 秒 |
| 准确度（印刷中文） | 99%+ | 95-98% |
| 准确度（手写/草书） | 90%+ | 50-70% |
| 表格理解 | ✅（结构化）| ❌（纯文本流）|
| bbox 坐标 | ❌ | ✅ |
| 跨页上下文 | ✅ | ❌ |
| API 复杂度 | 1 个函数 | curl + JSON 解析 |

**结论：能 vision 就别 OCR。**

---

## Pitfalls（踩过的坑）

1. **不要无脑走 OCR** — M3 时代 vision_analyze 几乎总是更好
2. **不要假设 pdftotext 一定有内容** — 扫描件出来就 5 字节（页面标识符）
3. **EasyOCR 字段名是 `image` 不是 `file`** — 错就报 422
4. **vision_analyze 加载大 PDF 可能慢**（>50MB）— 先 `pdftoppm` 转单页
5. **不要同时跑 OCR 和 vision_analyze** — 二选一，结果取并集会重复
6. **libreoffice 转 doc 是同步的，wps 文件有时转出乱码** — 兜底用 `wvText` 或 `antiword`
7. **扫描件里嵌入的小字/水印** — vision_analyze 经常漏读，必要时显式问"有没有水印/小字/页眉页脚"

---

## 适用场景示例

- ✅ **批量文件重命名前判定单位**（tongzhan-file-batch-rename 调用本 skill 读内容）
- ✅ **政府公文 PDF 内容核对**（M3 政府公文识别能力强）
- ✅ **扫描件归档 OCR 索引**（vision_analyze 给摘要，OCR 给全文）
- ✅ **截图 QA**（UI 走查、bug 反馈）
- ✅ **微信/飞书接收的图片**理解
- ❌ **手写密集笔记** — 仍需人工核

---

## 相关技能

- `tongzhan-file-batch-rename` — 批量文件改名，**重度依赖本 skill**（每个文件都要读内容判定党委/党组）
- `meeting-minutes-generator` — 录音转录后用 vision_analyze 识别公文格式
- `ocr-and-documents` (本 skill) — 上游 OCR 能力
