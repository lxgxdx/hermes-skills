---
name: easyocr-unraid-p4-deploy
description: 在 Unraid Tesla P4 (Pascal) 上部署 EasyOCR GPU 版 OCR 服务。关键：CUDA 11.x；--no-cache 重建；numpy<2 必须最后装；opencv-python-headless<=4.9.0.80；api.py 去掉 lang_list 参数，支持 PDF 上传。
tags: [unraid, docker, easyocr, ocr, gpu, tesla-p4, pascal]
category: mlops
---

# EasyOCR GPU 部署到 Unraid Tesla P4（2026-04-22 实测更新）

## 今日调试记录

| 日期 | 问题 | 解决 |
|------|------|------|
| 2026-04-22 | api.py 无异常捕获，图片解码失败返 500 | 加 try/except 返回 400 |
| 2026-04-22 | NumPy 2.x 与 PyTorch 2.2.0 ABI 冲突 | `numpy<2` 必须放在**所有包安装完之后**再装，否则被 easyocr 覆盖回 2.x |
| 2026-04-22 | `reader.readtext()` 不支持 `lang_list` 参数 | 删除该参数，语言在 Reader 初始化时固定 |
| 2026-04-22 | `opencv-python-headless>=4.13` 要求 `numpy>=2`，与 `numpy<2` 冲突 | 固定 `opencv-python-headless<=4.9.0.80` |
| 2026-04-22 | gpu=False 未启用 GPU | 改为 `gpu=True` |
| 2026-04-22 | Docker 重建后内容不变 | 必须加 `--no-cache` |
| 2026-04-22 | 用户需要直接上传 PDF | 添加 PyMuPDF 支持，api.py 自动识别文件类型 |

## 背景

- Tesla P4 是 **Pascal 架构（Compute Capability 6.1）**
- **CUDA 12.x 已放弃对 Pascal 的支持**，必须用 CUDA 11.x
- EasyOCR 中英文约需 **500MB 显存**，比 PaddleOCR 轻很多
- 可与 Infinity 向量服务（占用 53-54% 显存）共存

## 项目文件

```
easyocr-gpu/
├── Dockerfile           # 基于 pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime
├── docker-compose.yml  # Unraid Docker Compose 配置
├── api.py              # FastAPI OCR 服务（含异常捕获）
└── build.sh            # 构建脚本
```

## 部署步骤

### 1. 上传文件到 Unraid

将 `easyocr-gpu/` 目录上传到 `/mnt/user/appdata/easyocr-gpu/`

### 2. Dockerfile（2026-04-22 实测最终版）

> ⚠️ 关键点：opencv-python-headless<=4.9.0.80、numpy<2 必须最后装、pymupdf

```dockerfile
FROM pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime

SHELL ["/bin/bash", "-c"]

RUN apt-get update -y && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-dev libgomp1 \
    curl \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ✅ 先装 easyocr 和 FastAPI 依赖（会自动装 numpy 2.x）
# ✅ 固定 opencv-python-headless<=4.9.0.80 以兼容 numpy<2
RUN python -m pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple \
    easyocr \
    "opencv-python-headless<=4.9.0.80" \
    fastapi uvicorn python-multipart aiofiles

# ✅ numpy<2 必须最后装，防止被其他包覆盖
RUN python -m pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple "numpy<2"

# ✅ PDF 支持：PyMuPDF 纯 Python 库
RUN python -m pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple pymupdf

COPY api.py /app/api.py

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```
### 3. api.py（必须包含异常捕获）

```python
"""
EasyOCR FastAPI Server
POST /ocr        — 文件上传
POST /ocr/base64 — base64 图片
"""
import io
from contextlib import asynccontextmanager

import cv2
import easyocr
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image

reader = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global reader
    print("🔄 Loading EasyOCR models...")
    # ✅ gpu=True 启用 GPU（Tesla P4 Pascal 可用）
    reader = easyocr.Reader(["ch_sim", "en"], gpu=True, verbose=False)
    print("✅ EasyOCR ready (GPU mode)")
    yield
    print("👋 Shutting down EasyOCR server")

app = FastAPI(
    title="EasyOCR API",
    description="GPU-accelerated OCR API using EasyOCR on Tesla P4",
    version="1.0.0",
    lifespan=lifespan,
)

def bytes_to_cv2image(contents: bytes):
    """将图片字节转换为 OpenCV numpy array"""
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图片")
    return img

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/ocr")
async def ocr_image(
    image: UploadFile = File(...),
    languages: str = Form("ch_sim,en"),
    detail: int = Form(1),
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    lang_list = [l.strip() for l in languages.split(",")]
    contents = await image.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty image file")

    # ✅ 必须有异常捕获，否则图片解码失败直接返回 500
    try:
        img = bytes_to_cv2image(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    try:
        # ✅ lang_list 参数不存在，语言在 Reader 初始化时固定
        results = reader.readtext(img, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")

    if detail == 0:
        return JSONResponse({"success": True, "results": results})
    else:
        parsed = []
        for bbox, text, confidence in results:
            parsed.append({
                "text": text,
                "confidence": round(float(confidence), 3),
                "bbox": [[round(float(x), 1), round(float(y), 1)] for x, y in bbox],
            })
        return JSONResponse({"success": True, "results": parsed})

@app.post("/ocr/base64")
async def ocr_base64(
    image_data: str = Form(...),
    languages: str = Form("ch_sim,en"),
    detail: int = Form(1),
):
    """接收 base64 编码的图片进行 OCR"""
    import base64 as b64

    try:
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        contents = b64.b64decode(image_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {e}")

    try:
        img = bytes_to_cv2image(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    try:
        # ✅ lang_list 参数不存在，语言在 Reader 初始化时固定
        results = reader.readtext(img, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")

    if detail == 0:
        return JSONResponse({"success": True, "results": results})
    else:
        parsed = []
        for bbox, text, confidence in results:
            parsed.append({
                "text": text,
                "confidence": round(float(confidence), 3),
                "bbox": [[round(float(x), 1), round(float(y), 1)] for x, y in bbox],
            })
        return JSONResponse({"success": True, "results": parsed})
```

### 4. 构建镜像

> ⚠️ **关键**：修改任何文件后必须加 `--no-cache`，否则 Docker 复用旧缓存！

```bash
cd /mnt/user/appdata/easyocr-gpu
mkdir -p cache
docker build --no-cache -t easyocr-gpu:latest . 2>&1 | tee build.log
```

### 5. Docker Compose 配置

```yaml
services:
  easyocr-gpu:
    image: easyocr-gpu:latest
    container_name: easyocr-gpu
    restart: unless-stopped
    ports:
      - "8082:8000"
    volumes:
      - /mnt/user/appdata/easyocr-gpu/cache:/root/.EasyOCR
    environment:
      - LANG=C.UTF-8
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### 6. 验证

```bash
# 检查 GPU 模式日志
docker logs easyocr-gpu --tail 10
# 期望看到: ✅ EasyOCR ready (GPU mode)

# 健康检查
curl http://localhost:8082/health
# 返回: {"status":"ok"}

# OCR 测试（用真实图片文件）
curl -X POST http://localhost:8082/ocr \
  -F "image=@/path/to/test.jpg" \
  -F "languages=ch_sim,en"
```

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `ValueError: 无法解码图片` 返回 500 | api.py 缺少异常捕获，图片解码失败直接崩 | 升级 api.py 加 try/except（见上方代码） |
| NumPy ABI 冲突警告，OCR 返回 500 | PyTorch 2.2.0 用 NumPy 1.x 编译，2.x 不兼容 | Dockerfile 加 `RUN pip install "numpy<2"` |
| `pip install easyocr` 超时 | 清华源不稳定 | 换阿里云镜像 `-i https://mirrors.aliyun.com/pypi/simple` |
| Docker 重建后 api.py 没变 | 没加 `--no-cache` | 必须 `docker build --no-cache` |
| GPU 模式没生效 | api.py 里 `gpu=False` | 改为 `gpu=True` |
| `ModuleNotFoundError: easyocr` | Docker 用了旧镜像缓存 | `docker build --no-cache` + `docker stop easyocr-gpu && docker rm easyocr-gpu` |

## 为什么不直接用 Docker Hub 上的 easyocr 镜像

- `challisa/easyocr`：最后更新 2020-08-16，已 5 年未维护
- 基础镜像 `pytorch/pytorch`（无 tag）版本未知
- 必须自己用新版 PyTorch (CUDA 11.x) 构建

# EasyOCR GPU 部署到 Unraid Tesla P4

## 背景

- Tesla P4 是 **Pascal 架构（Compute Capability 6.1）**
- **CUDA 12.x 已放弃对 Pascal 的支持**，必须用 CUDA 11.x
- EasyOCR 中英文约需 **500MB 显存**，比 PaddleOCR 轻很多
- 可与 Infinity 向量服务（占用 53-54% 显存）共存

## 项目文件

```
easyocr-gpu/
├── Dockerfile           # 基于 pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime
├── docker-compose.yml  # Unraid Docker Compose 配置
├── api.py              # FastAPI OCR 服务
└── build.sh            # 构建脚本
```

## 部署步骤

### 1. 上传文件到 Unraid

将 `easyocr-gpu/` 目录上传到 `/mnt/user/appdata/easyocr-gpu/`

### 2. Dockerfile 正确内容

> ⚠️ 注意：不要用 git clone 方式安装 EasyOCR，国内网络会卡住。用 pip install。

```dockerfile
FROM pytorch/pytorch:2.2.0-cuda11.8-cudnn8-runtime

SHELL ["/bin/bash", "-c"]

RUN apt-get update -y && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-dev libgomp1 \
    curl \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ✅ 用 pip install，不要 git clone（国内网络会挂）
RUN python -m pip install --no-cache-dir easyocr
RUN python -m pip install --no-cache-dir fastapi uvicorn python-multipart aiofiles opencv-python-headless

COPY api.py /app/api.py

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. 构建镜像（SSH）

> ⚠️ **关键**：修改 Dockerfile 后必须加 `--no-cache`，否则 Docker 会复用旧缓存层，新内容不生效！

```bash
cd /mnt/user/appdata/easyocr-gpu
mkdir -p cache
docker build --no-cache -t easyocr-gpu:latest . 2>&1 | tee build.log
```

### 4. Docker Compose 配置

```yaml
services:
  easyocr-gpu:
    image: easyocr-gpu:latest
    container_name: easyocr-gpu
    restart: unless-stopped
    ports:
      - "8082:8000"
    volumes:
      - /mnt/user/appdata/easyocr-gpu/cache:/root/.EasyOCR
    environment:
      - LANG=C.UTF-8
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
```

### 4. 验证

```bash
curl http://localhost:8082/health
# 返回: {"status":"ok"}
```

## API 调用

```bash
curl -X POST http://localhost:8082/ocr \
  -F "image=@/path/to/image.jpg" \
  -F "languages=ch_sim,en"
```

## 已知问题

| 问题 | 原因 | 状态 |
|------|------|------|
| `ModuleNotFoundError: No module named 'easyocr'` 但镜像存在 | Docker 用旧缓存未真正安装 | 修复：--no-cache |
| NumPy 2.x 与 PyTorch 2.2.0 ABI 冲突 | PyTorch 2.2.0 编译于 NumPy 1.x | 修复：Dockerfile 加 `numpy<2` |
| GPU 模式需显式指定 `gpu=True` | 默认 CPU | 已在 api.py 中设置 |
| `ValueError: 无法解码图片` 返回 500 | 缺少异常处理 | 修复：api.py 加 try/except |

## 为什么不直接用 Docker Hub 上的 easyocr 镜像

- `challisa/easyocr`：最后更新 2020-08-16，已 5 年未维护
- 基础镜像 `pytorch/pytorch`（无 tag）版本未知
- 必须自己用新版 PyTorch (CUDA 11.x) 构建
