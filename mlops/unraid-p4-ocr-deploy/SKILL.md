---
name: unraid-p4-ocr-deploy
description: Unraid Tesla P4 上部署 OCR 服务供 Hermes 调用
version: 2026-04-19
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

### 镜像选型结论（重要更正）

**`paddlepaddle/paddleocr-gpu` 不存在！** 这是本次排查最重要的教训。

Docker Hub 上有两个容易混淆的仓库：
- `paddlepaddle/paddle` — PaddlePaddle 框架本体（无 OCR），GPU 版 12GB+
- `paddlecloud/paddleocr` — **预装了 PaddleOCR 的完整镜像** ✅

**正确镜像：`paddlecloud/paddleocr:2.6-gpu-cuda11.2-cudnn8-latest`**
- 体积：~6GB
- 预装 PaddleOCR，无需本地 build
- CUDA 11.2 + cuDNN 8，完美支持 Pascal 架构（P4 CC 6.1）
- 最后拉取时间：2026-04-19（说明镜像活跃可用）

### 凌晨部署步骤（极简版，只需一条命令）

```bash
# 凌晨 2:00-5:00 执行
docker pull paddlecloud/paddleocr:2.6-gpu-cuda11.2-cudnn8-latest
```

然后更新 `/mnt/user/appdata/ocr/docker-compose.yml`：

```yaml
services:
  ocr_gpu:
    image: paddlecloud/paddleocr:2.6-gpu-cuda11.2-cudnn8-latest
    container_name: paddle_ocr_gpu
    restart: unless-stopped
    ports:
      - "8008:8008"
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
        limits:
          memory: 4G
    shm_size: 4gb
    volumes:
      - ./models:/root/.paddleocr

networks:
  default:
    name: ocr_net
```

**不需要 Dockerfile，不需要 build，直接用预装镜像。**

### 验证
```bash
curl http://localhost:8008/health
# 应返回：{"status":"ok"}
```

### 常用镜像源测试结果（2026-04-19）
| 镜像源 | 状态 | 备注 |
|--------|------|------|
| `paddlecloud/paddleocr:2.6-gpu-cuda11.2-cudnn8-latest` | ✅ 存在，~6GB | 预装 OCR，直接用 |
| `paddlepaddle/paddleocr-gpu` | ❌ 不存在 | 误以为是官方镜像 |
| `paddlepaddle/paddle` (GPU版) | ⚠️ 12.8GB太大 | 国内网络难拉 |
| `nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04` | ⚠️ 可拉但慢 | 需本地 build |

### 注意事项
- `version: "3.8"` 已废弃，docker-compose.yml 顶层不要加 version
- Docker Hub 访问可能受限，如拉取失败需要本地构建镜像
- 如果 CUDA 版本不匹配，换 `nvidia/cuda:12.x` 基础镜像
- 服务端口默认 `8008`，对应容器内端口 8008
- 一直运行会占用 P4 显存约 1.5-2GB（无法动态释放，除非停容器）
- 容器 GPU 显存限制靠 `nvidia-container-toolkit` + `CUDA_VISIBLE_DEVICES` 实现

### 部署步骤优先级

1. **先试镜像加速器**（配置 `/etc/docker/daemon.json`）——最简单
2. **再试本地构建**（手动 `docker build`）——完全离线
3. **最后用 Docker UI 手动创建**——最通用

### 关键认知纠正
- **Unraid 不是用 `docker compose` 部署的** — 这是传统 Linux Docker 概念
- Unraid 用 **Community Applications (CA)** 作为 Docker 应用的"应用商店"，或在 Docker 标签页手动创建容器
- 提交 CA 模板需要：准备模板文件 → 论坛发帖 → 官方表单提交 → 审核（约48小时）
- 普通用户直接在 Docker UI 填写配置更实用

### 注意事项
- `version: "3.8"` 已废弃，docker-compose.yml 顶层不要加 version
- Docker Hub 访问可能受限，如拉取失败需要本地构建镜像
- 如果 CUDA 版本不匹配，换 `nvidia/cuda:12.x` 基础镜像
- 服务端口默认 `8008`，对应容器内端口 8008
- 一直运行会占用 P4 显存约 1.5-2GB（无法动态释放，除非停容器）
- 容器 GPU 显存限制靠 `nvidia-container-toolkit` + `CUDA_VISIBLE_DEVICES` 实现