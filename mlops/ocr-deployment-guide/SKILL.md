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

---

## 🆕 M3 多模态时代的 OCR 策略（2026-06 更新）

当前对话模型有原生多模态视觉，对**少量文档/图片**可直接用 `vision_analyze`，无需 OCR 服务：

| 场景 | 做法 | 说明 |
|------|------|------|
| 单张图片/截图 | `vision_analyze` | 99%+ 准确，无需部署 OCR |
| 1-5 页扫描件 | pdftoppm 转图 → vision_analyze | 比 EasyOCR 更准 |
| 大批量文档（50+ 页） | **EasyOCR 好** | vision 一个一个传太慢 |
| 自动化脚本（无交互） | **EasyOCR 好** | 纯 API，不需要 LLM 上下文 |
| 需要 bbox 坐标 | **EasyOCR 好** | vision 不返回坐标 |
| M2.7 或审核拦截 | **EasyOCR 好** | 退而求其次 |

**结论：OCR 服务（EasyOCR on P4）仍然是基础设施必备，但日常小文档处理优先走 vision。**

---

## Deployment: Unraid Tesla P4

> See `unraid-p4-ocr-deploy` skill for the complete deployment guide (Unraid Docker UI, CA template,镜像选择, docker-compose.yml). See `easyocr-unraid-p4-deploy` skill for a fully实测 (2026-04-22) Dockerfile + api.py with exception handling, numpy<2 fix, and PyMuPDF PDF support. Key facts:

- **Correct image**: `paddlecloud/paddleocr:2.6-gpu-cuda11.2-cudnn8-latest` — NOT `paddlepaddle/paddleocr-gpu` (doesn't exist)
- **EasyOCR vs PaddleOCR**: EasyOCR ~500MB VRAM, PaddleOCR 1.5-2.5GB; EasyOCR preferred for VRAM-constrained P4
- **EasyOCR Dockerfile**: Use `pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime` base; fix `numpy<2` ordering; `opencv-python-headless<=4.9.0.80`; always rebuild with `--no-cache`
- **Port**: `8008:8008`, health check at `http://<unraid-ip>:8008/health`
- **Unraid method**: Use Docker UI (not `docker compose` CLI)

---

## Troubleshooting

> See `ocr-api-troubleshooting` skill for the complete diagnostic guide. Key patterns:

**Health passes but OCR returns 500**: GPU failure is silent — EasyOCR doesn't always raise clear errors when GPU access fails. Check:
1. CUDA driver match: `nvidia-smi` on host vs container CUDA version
2. GPU visibility: `torch.cuda.is_available()` inside container
3. GPU memory: other services (Infinity vector service) consuming VRAM
4. Fallback to CPU: set `gpu=False` in `easyocr.Reader()` initialization

**Prevention**: Implement graceful degradation in `api.py`:
```python
try:
    reader = easyocr.Reader(["en"], gpu=True, verbose=False)
except Exception as e:
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
```

**Emergency fix (no SSH)**: Stop container via Unraid UI → edit `api.py` to `gpu=False` → rebuild with `--no-cache` → restart.

---

## Key Takeaways

1. **VRAM估算必须实测** — 官方数字往往偏高，EasyOCR实测仅~500MB
2. **健康检查通过 ≠ OCR工作** — 必须做功能测试
3. **GPU失败是静默的** — EasyOCR不会总抛出明确错误
4. **CPU fallback是生产可靠性保障**
5. **镜像名要核实** — `paddlepaddle/paddleocr-gpu` 不存在
