---
name: ocr-deployment-guide
description: OCR 服务部署指南 — 选型、显存评估与部署决策
version: 2026-04-20
status: implemented
---

# OCR 部署选型与显存评估指南

## 选型矩阵

| 方案 | 显存需求 | 中文支持 | 速度 | 部署难度 |
|------|---------|---------|------|---------|
| PaddleOCR GPU | ~2GB+（官方说 8GB+）| 优秀 | 快 | 较复杂 |
| **EasyOCR GPU** | **~700MB（实测）** | 较好 | 快 | 简单 |
| cnocr | 0（纯 CPU） | 较好 | 慢 | 最简 |
| Tesseract | 0（纯 CPU） | 需装语言包 | 快 | 极简 |

## 关键教训：显存估算必须实测

**重要经验**：PaddleOCR 官方文档说 8GB 起步，EasyOCR 官方文档没有明确显存要求。
实际测试数据（Issue #1326，用户 brownsloth 在 15GB 显卡上测试）：

- EasyOCR 英文模型：加载 ~250MB + 推理 ~34MB = **~284MB**
- EasyOCR 中英文模型（ch_sim + en）：
  - 检测模型 CRAFT：~200MB
  - 中文识别模型 chinese_sim.pth：~300-500MB（字符集 5000+ 汉字）
  - 推理中间张量：~50-100MB
  - **合计：~600-850MB**

**错误来源**：我最初说 "PaddleOCR 占用 1.5-2GB" 是严重低估，官方明确写 8GB+。EasyOCR 我说 1.5-2GB 也是高估，实为 ~700MB。

## 部署原则

1. **先查官方文档 + GitHub Issues**，不要凭感觉给数字
2. **实测优于估算**：有 GPU 就先跑个 quick test 验证显存占用
3. **显存紧张时优先选 CPU 方案**：cnocr/Tesseract 完全不占显存
4. **多语言 OCR 显存需求 > 单语言**：字符集越大模型越大

## EasyOCR 已安装检查

```bash
pip3 show easyocr  # 检查是否已安装
python3 -c "import easyocr; print(easyocr.__version__)"
```

## EasyOCR GPU 快速验证（Python）

```python
import easyocr
reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
# 首次加载模型约需 30-60 秒
result = reader.readtext('test.jpg')
print(result)
```

## Tesseract 备选（完全 CPU）

```bash
tesseract --version  # 检查是否已装
sudo apt install tesseract-ocr-chi-sim  # 装中文语言包
tesseract image.jpg stdout -l chi_sim  # 命令行使用
```

## Unraid P4 显存查询

```bash
ssh root@<unraid-ip> "nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader"
```
