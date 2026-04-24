---
name: pdf-image-ocr-scan
description: Unraid Tesla P4 OCR 扫描工具 — 将 PDF 或图片识别为 Word 文档。支持直接上传 PDF（多页自动拆分）或图片，调用 EasyOCR GPU API 识别，结果整理成 docx 保存到 TZB 目录。
tags: [ocr, easyocr, pdf, docx, unraid, gpu]
category: productivity
---

# PDF/图片 OCR 扫描工作流

## 服务信息
- **地址**：http://192.168.88.68:8082
- **端口**：8082
- **API**：POST /ocr（支持图片和 PDF）
- **健康检查**：GET /health

## OCR API 调用

### 1. 测试服务状态
```bash
curl http://192.168.88.68:8082/health
# 返回: {"status":"ok"}
```

### 2. 上传图片 OCR
```bash
curl -s -X POST http://192.168.88.68:8082/ocr \
  -F "image=@/path/to/image.jpg" \
  --connect-timeout 30 -m 120
```

### 3. 上传 PDF OCR（多页自动识别）
```bash
curl -s -X POST http://192.168.88.68:8082/ocr \
  -F "image=@/path/to/file.pdf" \
  --connect-timeout 60 -m 600
```

## 完整工作流（PDF → Word → TZB目录）

### Step 1：上传 PDF 并保存 OCR 结果
```bash
curl -s -X POST http://192.168.88.68:8082/ocr \
  -F "image=@/path/to/input.pdf" \
  --connect-timeout 60 -m 600 > /tmp/ocr_result.json
```

### Step 2：用 Python 整理成 Word
```python
import json
from docx import Document

with open('/tmp/ocr_result.json') as f:
    d = json.load(f)

doc = Document()

# 标题（OCR结果中提取或手动设置）
title = doc.add_heading("文档标题", level=0)
title.alignment = 1

# 从每页提取文本
for page in d.get("pages", []):
    items = page["results"]
    
    def sort_key(item):
        bbox = item.get("bbox", [[0,0],[0,0],[0,0],[0,0]])
        return (bbox[0][1], bbox[0][0])
    
    items_sorted = sorted(items, key=sort_key)
    
    current_line = []
    current_y = None
    para_texts = []
    
    for item in items_sorted:
        text = item["text"].strip()
        bbox = item.get("bbox", [[0,0],[0,0],[0,0],[0,0]])
        y = bbox[0][1]
        
        if not text:
            continue
        # 跳过页码和低置信度噪声
        if len(text) <= 2 and text.isdigit():
            continue
        if item["confidence"] < 0.15:
            continue
        
        if current_y is None:
            current_y = y
        
        if abs(y - current_y) < 25:
            current_line.append(text)
            current_y = y
        else:
            if current_line:
                combined = "".join(current_line)
                if combined.strip():
                    para_texts.append(combined)
            current_line = [text]
            current_y = y
    
    if current_line:
        combined = "".join(current_line)
        if combined.strip():
            para_texts.append(combined)
    
    for t in para_texts:
        if t.strip():
            doc.add_paragraph(t)
    doc.add_paragraph()  # 页间空行

doc.save("/tmp/输出文档名.docx")
print("OK")
```

### Step 3：上传到 TZB 目录
```bash
# TZB 挂载在 /mnt/nfs/
# 目录结构：/mnt/nfs/2026年统战工作/6.巡查部机关/

cp /tmp/输出文档名.docx /mnt/nfs/2026年统战工作/6.巡查部机关/
```

## 已知问题

- **识别率约 70-80%**：对中文政府红头文件、特殊排版、印章遮挡等场景识别率有限
- **竖排文字**：识别率较低
- **手写体**：不适用
- **表格**：表格结构会丢失，变成纯文本行
