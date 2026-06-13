---
name: pdf-document-tools
description: Class-level guide to PDF document processing — covers PDF→image conversion, OCR for scanned PDFs (Baidu OCR, EasyOCR), the M3 multimodal-vision fast path, and the trade-offs between pure utility scripts and API-based OCR. Load when working with scanned PDFs, batch-converting PDF pages to images, or choosing between vision_analyze, Baidu OCR, and EasyOCR pipelines.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [pdf, ocr, easyocr, baidu-ocr, vision, scanned-pdf, pymupdf, docx]
    related_skills: [ocr-and-documents, tongzhan-file-batch-rename, meeting-minutes-generator]
---

# PDF Document Tools

PDF processing in Hermes falls into three families, each with its own trade-off:

1. **M3 multimodal vision (`vision_analyze`)** — fastest and most accurate for 1-10 page scanned PDFs. First choice on `minimax-cn/MiniMax-M3`. See the upstream umbrella `ocr-and-documents` for the decision tree.
2. **API-based OCR** — Baidu OCR for batch Chinese (1000 calls/month free), EasyOCR on the Unraid Tesla P4 GPU (192.168.88.68:8082). Use for >30-page batches, when M3 vision is unavailable, or when you need bbox coordinates.
3. **Pure utility scripts** — PyMuPDF-based page→image conversion when you just need to render PDF pages as PNG/JPG without OCR.

> **The 3 skills folded into this umbrella (`pdf-ocr`, `pdf-image-ocr-scan`, `pdf-to-image-preview`) were the pre-M3-vision era's primary entry points.** They're preserved as references below for back-compat and for users on M2.7 / M3-vision-unavailable. **On M3, prefer the `ocr-and-documents` umbrella's `vision_analyze` path** — it's faster, more accurate, and doesn't burn Baidu quota.

## Sections

1. [PDF → Image utility script](references/pdf-to-image-utility.md) — the original `pdf-to-image-preview` skill. PyMuPDF-based batch converter. [Script lives at `scripts/convert_pdf_to_images.py`](scripts/convert_pdf_to_images.py).
2. [Baidu OCR (PDF → Word)](references/baidu-ocr-pdf.md) — the original `pdf-ocr` skill. Chinese OCR with header/footer cropping and image preservation.
3. [EasyOCR GPU pipeline (PDF/image → Word)](references/easyocr-pdf.md) — the original `pdf-image-ocr-scan` skill. Unraid Tesla P4 deployment.
4. [PDF→image usage guide](references/usage-guide.md) — companion notes from the original `pdf-to-image-preview` package.

## Decision Tree

```
要处理 PDF 文件 →
  ├─ 文字型 PDF（pdftotext 有输出）→ pdftotext（最快）
  │
  ├─ 扫描件 PDF
  │   ├─ 1-10 页 + M3 可用 → vision_analyze（首选）
  │   ├─ 11-30 页 + M3 可用 → vision_analyze（pdftoppm 转图更稳）
  │   ├─ >30 页 或 M3 不可用
  │   │   ├─ 需要结构化 Word 输出 → Baidu OCR (baidu-ocr-pdf.md)
  │   │   ├─ 需要 bbox 坐标 → EasyOCR (easyocr-pdf.md)
  │   │   └─ 只需要图片，不需要 OCR → pdf-to-image-utility.md
  │   └─ 部署好的 Unraid Tesla P4 + EasyOCR 自动化 → EasyOCR
  │
  └─ 只要 PDF 页面渲染为图片（不 OCR）→ pdf-to-image-utility.md
```

## When to Load This Umbrella

- Working with scanned PDFs (政府公文, 报告, 合同)
- Choosing between vision_analyze / Baidu OCR / EasyOCR
- Batch-converting PDF pages to images for archival or QA
- Auditing legacy PDF-OCR workflows before the M3 vision upgrade
- Setting up a new OCR pipeline and need to compare options

## When to Use the Upstream `ocr-and-documents` Instead

`ocr-and-documents` is the broader class-level umbrella covering all document types (PDF, docx, images, screenshots, libreoffice, etc.) with the M3-vision-first decision tree. Load that one if:

- You're not sure which path to take
- You need to handle mixed file types
- You want the canonical M3-vision-first workflow

Use this `pdf-document-tools` umbrella when you've narrowed down to "this is a PDF problem" and want the per-engine recipes (Baidu OCR, EasyOCR, PyMuPDF utility).

## Scripts

- `scripts/convert_pdf_to_images.py` — PyMuPDF-based PDF→PNG/JPG batch converter. Supports custom DPI, output dir, optional ZIP packaging. No OCR, just rasterization.

## Related Skills

- `ocr-and-documents` — broader class-level umbrella (M3 vision + libreoffice + OCR fallbacks)
- `tongzhan-file-batch-rename` — uses PDF reading to identify organizational unit (党委/党组/etc.) for renaming
- `meeting-minutes-generator` — uses PDF reading to identify 公文 format in meeting materials
- `doc-file-conversion` — older `.doc` (Office 97-2003) handling
