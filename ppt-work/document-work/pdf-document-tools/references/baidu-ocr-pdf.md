---
name: pdf-ocr
description: PDF扫描件转Word文档。支持中文OCR识别，自动裁掉页眉页脚，保留插图，彩色章节封面页保留为图片。使用百度OCR API（免费额度1000次/月）。当用户要求把扫描PDF转成文字/Word时触发。
---

# PDF扫描件 OCR 转换技能 📄

## 🆕 M3 多模态优先提示

当前模型（MiniMax-M3）有原生多模态视觉。对**少量页数（1-10 页）** 的扫描件 PDF，优先用 vision_analyze，比百度 OCR 更快更准（省百度 OCR 免费额度）：

```python
# 少量页：M3 vision_analyze 优先
import subprocess
from hermes_tools import vision_analyze

for page in range(1, 4):  # 前 3 页
    subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page),
                    '-png', '-r', '200', 'input.pdf', f'/tmp/v_page'])
    vision_analyze(image_url=f'/tmp/v_page-{page:03d}.png',
                   question=f"提取第 {page} 页所有文字，按段落输出。")
```

**什么时候用百度 OCR（本 skill 的原始流程）：**
- **大批量文档** (>30页) — vision 一个一个传效率低
- **需要结构化 word 输出**（页眉页脚裁剪、插图保留）
- **M3 多模态不可用**（如 M2.7 对话，或扫描件内容被安全审核拦截）

## 配置
- **百度 OCR API Key**: vOBOM7tO0lL8cKMJdZy453Ai
- **百度 OCR Secret Key**: bib8MvDPTfXXdPz4JyzIyDCvCeKxtpyu
- **免费额度**: **1000次/月**（1次=1页），592页以内一次免费跑完
- **接口**: 通用文字识别（高精度版）`accurate_basic`

## 依赖安装
```bash
pip install pymupdf python-docx pillow
```

## 使用方法

```bash
python3 /home/lxgxdx/.hermes/skills/openclaw-imports/pdf-ocr/scripts/pdf_to_docx.py <PDF路径> [输出目录]
```

输出文件在 `[输出目录]/xxx_全文_ocr.docx`，文件较大时用脚本压缩图片：

```bash
python3 /home/lxgxdx/.hermes/skills/openclaw-imports/pdf-ocr/scripts/compress_docx.py <docx路径> <输出路径>
```

## 处理策略

| 页面类型 | 判断方式 | 处理方式 |
|---------|---------|---------|
| 正文页 | 默认 | 裁掉顶部6%（页眉）+底部4%（页脚），OCR识别文字 |
| 插图页 | OCR无文字输出 | 保留为图片嵌入Word |
| 彩色封面/章节页 | 彩色像素占比>25% | 保留为图片，加灰色标注 |

## 已知限制
- **图文混排页**（图表里有文字）：OCR会把图表内文字识别为正文，需人工替换
  - 解决：用户找到问题页，告知PDF页码，截图后手动替换
- **白底目录页**：不会被自动识别为特殊页，会被OCR识别（效果一般）
  - 解决：转换后人工替换目录页为图片

## 实战案例（《预测之书》592页）
- 处理时间：约20分钟（含0.6s/页间隔）
- 输出原始大小：303MB（嵌入144张图片）
- 压缩后大小：3.4MB（图片降分辨率至600px宽，质量60%）
- 识别效果：正文准确率高，图表页需人工处理
- 每50页自动保存一次进度，防止中途崩溃

## 注意事项
- 免费版 QPS=2，脚本已加0.6秒/页间隔
- 裁剪比例（页眉6%/页脚4%）可在脚本顶部调整
- OCR完成后建议抽查几页校对准确率
- 原始高清版保留在服务器，压缩版用于分发
