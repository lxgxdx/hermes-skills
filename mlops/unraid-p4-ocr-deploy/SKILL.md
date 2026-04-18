---
name: unraid-p4-ocr-deploy
description: Unraid Tesla P4 上部署 OCR 服务供 Hermes 调用
version: 2026-04-18
status: implemented
---

# Unraid P4 OCR 部署

## 需求背景
用户希望在 Unraid Tesla P4 上部署 OCR 服务，仅供 Hermes Agent 调用。

## 实现方案

### 文件位置
`/tmp/ocr/`（已生成）：
- `docker-compose.yml` — 启动模板
- `Dockerfile` — 构建 PaddleOCR GPU 镜像
- `ocr_api.py` — FastAPI 服务（含 `/predict` 和 `/predict_base64`）
- `README.md` — 部署说明

### 服务端点
- `POST /predict` — 上传图片文件，返回 `{"success", "texts", "confidences", "elapsed_ms"}`
- `POST /predict_base64` — 接受 base64 编码图片
- `GET /health` — 健康检查

### 部署步骤（重要：Unraid 不使用命令行 docker compose）

### 方式一：通过 Unraid Docker UI 手动创建容器（推荐）

1. 进入 Unraid Web GUI → **Docker** 标签页
2. 点击 **Add Container**（或类似按钮）
3. 填写配置（对应 docker-compose 的内容）：
   - **Image**: `paddleocr-gpu:latest`（需先在 Unraid 构建，或用现有镜像名）
   - **Name**: `paddle_ocr_gpu`
   - **Network**: `bridge`（或自定义网络）
   - **Port Mappings**: `8008:8008`
   - **Environment Variables**: `NVIDIA_VISIBLE_DEVICES=all`, `CUDA_VISIBLE_DEVICES=0`
   - **GPU**: 勾选 GPU 支持（Tesla P4）
   - **Memory Limit**: `4G`
   - **Shared Memory**: `4gb`
   - **Shm Size**: `4gb`
4. 点击 **Apply** 创建并启动容器
5. 验证：`http://<unraid-ip>:8008/health` 返回 `{"status":"ok"}`

### 方式二：通过 Community Applications (CA) 提交模板

1. 准备 CA 模板文件（YAML/JSON 格式，包含容器所有配置）
2. 在 [Unraid 论坛](https://forums.unraid.net/) 发帖创建支持线程
3. 通过 [CA 提交表单](https://form.asana.com/?k=qtIUrf5ydiXvXzPI57BiJw) 提交审核
4. 审核通过后，用户可在 Apps 标签页搜索安装

### 方式三：命令行部署（不推荐，仅理论参考）

> ⚠️ Unraid 官方不推荐直接用 `docker compose` 命令行管理容器，因为 Unraid 的 Docker 环境与传统 Linux 不同。

```bash
# 复制到 Unraid
scp -r /tmp/ocr root@<unraid-ip>:/mnt/user/appdata/ocr/

# SSH 登录 Unraid 后
cd /mnt/user/appdata/ocr
docker build -t paddleocr-gpu:latest .
docker run -d \
  --name paddle_ocr_gpu \
  --gpus '"device=0"' \
  -p 8008:8008 \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e CUDA_VISIBLE_DEVICES=0 \
  --shm-size 4gb \
  -m 4g \
  paddleocr-gpu:latest
```

### 关于 `/tmp/ocr/` 文件用途

`/tmp/ocr/` 下的文件（docker-compose.yml、Dockerfile、ocr_api.py）是**设计参考**，用于：
1. 确认容器配置（环境变量、端口、GPU、内存限制）
2. 供 CA 模板开发者参照填写 UI 字段
3. 备用：如有特殊需求需完全手动构建镜像

### 技术细节
- 基础镜像：`nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04`
- OCR 框架：PaddleOCR GPU (`paddlepaddle-gpu==2.6.0`, `paddleocr==2.7.3`)
- API 框架：FastAPI + Uvicorn
- 共享内存：`shm_size: 4gb`（大图处理需要）

### P4 显存调优（关键）
Tesla P4 有 **8GB** 显存（不是4GB），OCR 占用约 2GB，可留足显存给 Emby 硬解：

```python
_ocr_engine = PaddleOCR(
    use_angle_cls=True,
    lang="ch",
    use_gpu=True,
    show_log=False,
    rec_batch_num=4,
    max_batch_size=4,
    det_limit_side_len=1920,
)
```

Docker Compose 内存限制：
```yaml
limits:
  memory: 2G  # 2GB 足够PaddleOCR运行，留显存给Emby
```

显存占用估算（8GB P4）：
- PaddleOCR 峰值：~2GB
- Emby 硬解（1080p）：~1-2GB
- Emby 硬解（4K）：~2-3GB
- 总计可同时跑满 8GB

### Unraid Docker Compose WebUI 部署（推荐方式）

Unraid Docker 页面有一个 **Compose** 标签页（第三方插件提供），通过它可以用 Docker Compose 部署：

**Stack Settings：**
- Stack name: `paddle-ocr`

**Compose File：**
```yaml
version: "3.8"

services:
  ocr_gpu:
    build:
      context: /mnt/user/appdata/ocr
      dockerfile: Dockerfile
    image: paddleocr-gpu:latest
    container_name: paddle_ocr_gpu
    restart: unless-stopped
    ports:
      - "8008:8008"
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=0
    networks:
      - dockernetwork
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
        limits:
          memory: 2G
    shm_size: 4gb
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

networks:
  dockernetwork:
    external: true
```

**Env File：** 留空

**UI Labels：**
```yaml
labels:
  com.docker.compose.project: "paddle-ocr"
  org.opencontainers.image.title: "PaddleOCR GPU"
  org.opencontainers.image.description: "PaddleOCR GPU OCR Service"
```

**前提条件：**
- 文件（Dockerfile、ocr_api.py）需上传到 `/mnt/user/appdata/ocr`
- 确认 `dockernetwork` 网络已存在（`docker network ls` 可查）

### 关于 `/tmp/ocr/` 文件用途

`/tmp/ocr/` 下的文件（docker-compose.yml、Dockerfile、ocr_api.py）是**设计参考**，用于：
1. 确认容器配置（环境变量、端口、GPU、内存限制）
2. 供 CA 模板开发者参照填写 UI 字段
3. 备用：如有特殊需求需完全手动构建镜像

### 技术细节
- 基础镜像：`nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04`
- OCR 框架：PaddleOCR GPU (`paddlepaddle-gpu==2.6.0`, `paddleocr==2.7.3`)
- API 框架：FastAPI + Uvicorn
- 共享内存：`shm_size: 4gb`（大图处理需要）

### 关键认知纠正
- **Unraid 有 Docker Compose WebUI** — Docker 页面 → Compose 标签页（第三方插件）
- 通过 WebUI 编辑 compose file、env file、ui labels、stack settings 来部署
- 网络使用 `external: true` 声明已存在的网络（如 `dockernetwork`）
- 提交 CA 模板需要：准备模板文件 → 论坛发帖 → 官方表单提交 → 审核（约48小时）
- 普通用户直接在 Docker UI 填写配置更实用

### 注意事项
- Docker Hub 访问受限，无法直接拉取第三方预构建镜像，必须用 Dockerfile 自建镜像
- 如果 CUDA 版本不匹配，换 `nvidia/cuda:12.x` 基础镜像
- 服务端口默认 `8008`，对应容器内端口 8008
- 一直运行会占用 P4 显存约 1.5-2GB（无法动态释放，除非停容器）
- 容器 GPU 显存限制靠 `nvidia-container-toolkit` + `CUDA_VISIBLE_DEVICES` 实现

### 关键认知纠正
- **Unraid 不是用 `docker compose` 部署的** — 这是传统 Linux Docker 概念
- Unraid 用 **Community Applications (CA)** 作为 Docker 应用的"应用商店"，或在 Docker 标签页手动创建容器
- 提交 CA 模板需要：准备模板文件 → 论坛发帖 → 官方表单提交 → 审核（约48小时）
- 普通用户直接在 Docker UI 填写配置更实用

### 注意事项
- Docker Hub 访问受限，无法直接拉取第三方预构建镜像，必须用 Dockerfile 自建镜像
- 如果 CUDA 版本不匹配，换 `nvidia/cuda:12.x` 基础镜像
- 服务端口默认 `8008`，对应容器内端口 8008
- 一直运行会占用 P4 显存约 1.5-2GB（无法动态释放，除非停容器）
- 容器 GPU 显存限制靠 `nvidia-container-toolkit` + `CUDA_VISIBLE_DEVICES` 实现