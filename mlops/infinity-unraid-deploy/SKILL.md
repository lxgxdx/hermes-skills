---
name: infinity-unraid-deploy
description: 在 Unraid 上通过 Docker 部署 Infinity（基于 PyTorch 的向量 embedding 服务）。⚠️ Tesla P4 (Pascal 6.1) 不被 CUDA 12.x 镜像支持，P4 用户只能用 CPU 版或换 GPU。
tags: ["unraid", "docker", "infinity", "embedding", "nvidia", "gpu"]
category: mlops
---

# Infinity Unraid NVIDIA GPU 部署指南

## ⚠️ 重要前提：P4 显卡不兼容 CUDA 12.x

Tesla P4 是 **Pascal 架构（compute capability 6.1）**，但 Infinity 的所有 recent NVIDIA 镜像（`latest`、`0.0.77` 等）统一基于 **CUDA 12.9**，**已放弃对 Pascal 的支持**。

这不是 Infinity 的问题，而是 CUDA 12.x 本身的限制。

## 适用场景

- Tesla P4 / Pascal 架构 GPU（compute capability 6.1）
- 需要本地向量 embedding 服务
- GBrain 个人知识库对接

---

## Unraid Docker 配置

### 基础信息

| 字段 | 值 |
|------|-----|
| Name | `infinity-bge-m3` |
| Repository | `michaelf34/infinity:latest` |
| Extra Parameters | `--runtime=nvidia` |
| Network Type | 与 GBrain 同网络或 `host` |

### 端口映射

| 字段 | 值 |
|------|-----|
| Container Port | `80` |
| Host Port | `8080` |
| Protocol | `TCP` |

### 环境变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `INFINITY_MODEL_ID` | `BAAI/bge-m3` | HuggingFace 模型名 |
| `INFINITY_PORT` | `80` | 服务端口 |
| `INFINITY_DEVICE` | `cuda` | 使用 GPU |
| `HF_HOME` | `/app/.cache` | 模型缓存路径 |

### 卷映射

| Container Path | Host Path |
|----------------|-----------|
| `/app/.cache` | `/mnt/user/appdata/infinity-cache/` |

### ⚠️ DeepSeek 推荐配置的错误修正

| 错误配置 | 正确配置 |
|----------|----------|
| `MODEL_ID=BAAI/bge-m3` | `INFINITY_MODEL_ID=BAAI/bge-m3` |
| `/app/.cache/huggingface` | `/app/.cache` |

---

### 经验证可行的启动命令

```bash
docker run -d \
  --gpus '"device=0"' \
  --network host \
  -e MODEL_ID=BAAI/bge-m3 \
  -e INFINITY_PORT=80 \
  -e HF_HUB_ENABLE_HF_TRANSFER=0 \
  -v /mnt/user/appdata/infinity:/root/.cache/huggingface \
  --name infinity \
  michaelf34/infinity:latest
```

**关键参数：**
- `--network host`：避免 docker-proxy 转发问题
- `HF_HUB_ENABLE_HF_TRANSFER=0`：禁用 Rust 加速下载器，避免网络不稳时丢包报错
- 端口：容器内 80，映射到宿主机（如 `-p 8081:80` 或直接 host 模式）

### 验证

```bash
# 查看容器日志（应该有 "Uvicorn running on http://0.0.0.0:80"）
docker logs infinity

# 测试 embedding（注意路径是 /embeddings，不是 /v1/embeddings）
curl -X POST http://<unraid-ip>:8081/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": "hello world"}'
# 应返回 1024 维向量
```

## 性能基准（Tesla P4 实测）

| 测试类型 | 延迟 | 吞吐量 |
|----------|------|--------|
| 单条推理 | 50-65ms（平均56ms） | ~18条/秒 |
| 批量（10条） | 75ms | ~133条/秒 |

**⚠️ GBrain 批量写入时注意：** 单批次控制在 10 条以内，避免 GPU 任务拥挤。

## GBrain 侧配置

**⚠️ Infinity API 路径注意：**
- Infinity 只有 `/embeddings`，**没有** `/v1/embeddings` 前缀
- Infinity **不接受** `dimensions` 参数（会返回 422）

**⚠️ OpenAI SDK 兼容性问题（已验证 Bug）：**
OpenAI SDK（node-fetch based，4.104.0）调用 Infinity 会返回 **256 维全 0 向量**，但 curl、Python requests、Node.js 内置 fetch 均正常返回 1024 维。

症状：SDK 返回 `dim: 256, vec: [0,0,0...]`，Infinity 日志显示 `POST /embeddings 200`（但响应被 SDK 错误解析）。

**解决方案（已验证可用）：**

**方案一：用 fetch 改写 embedding.ts（推荐）**
用 Node.js 内置 `fetch` 替代 OpenAI SDK，可完全绕过兼容性问题。改动最小：

```typescript
// embedding.ts 中用 fetch 替代 OpenAI SDK
const resp = await fetch(`${baseURL}/embeddings`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ model: MODEL, input: texts }),
});
const data = await resp.json();
return data.data.map((d: any) => new Float32Array(d.embedding));
```

**方案二：配置 Nginx 反向代理**
在 Unraid 上装 Nginx 容器，把 `/v1/embeddings` 反向代理到 `/embeddings`：
```nginx
location /v1/embeddings {
  proxy_pass http://localhost:8081/embeddings;
}
```

**.env 配置（baseURL 不带 /v1）：**
```
EMBEDDING_BASE_URL=http://<unraid-ip>:8081
```

**验证本地 Infinity 是否正常：**
```bash
curl -X POST http://<unraid-ip>:8081/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": "hello world"}'
# 应返回 1024 维向量，dim: 1024
```

## ⚠️ Tesla P4 (Pascal) 不支持的解决方案

**注意：Tesla P4（Pascal 架构，compute capability 6.1）不被任何 CUDA 12.x 镜像支持。**

Infinity 的所有 recent 镜像（`latest`、`0.0.77`、`0.0.70` 等）统一基于 **CUDA 12.9**，已放弃 Pascal 支持。

**可用方案：**

| 方案 | P4 支持 | 说明 |
|------|---------|------|
| `michaelf34/infinity:latest-cpu` | ✅ | CPU 运行，慢但能用 |
| `michaelf34/infinity:0.0.70-nvidia-torch25` | ❌ | 仍是 CUDA 12，不支持 |
| Ollama embedding | ✅ | Ollama 本身对老卡兼容好，但 `/api/embeddings` 与 OpenAI SDK 不完全兼容 |
| 换 GPU | — | Tesla T4（Pascal 之后 Turing）最便宜升级方案 |

**结论**：P4 用户目前只能使用 CPU 版的 infinity，或者换一块 GPU。

## 通过 Compose Manager Plus 部署（推荐）

**项目目录：** `/boot/config/plugins/compose.manager/projects/infinity-bge-m3/`

**docker-compose.yml：**
```yaml
services:
  infinity:
    image: michaelf34/infinity:latest
    container_name: infinity-bge-m3
    restart: unless-stopped
    environment:
      - INFINITY_MODEL_ID=BAAI/bge-m3
      - INFINITY_PORT=80
      - HF_HOME=/app/.cache
      - HF_HUB_ENABLE_HF_TRANSFER=0
    ports:
      - "8081:80"
    volumes:
      - /mnt/user/appdata/infinity-cache:/app/.cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Compose Manager Plus 安装：`wget -O /boot/config/plugins/compose.manager.plg https://raw.githubusercontent.com/localjanitor/compose-manager-plus/main/compose.manager.plg`

## 参考
- GitHub: https://github.com/michaelfeil/infinity
- Docker: https://hub.docker.com/r/michaelf34/infinity
- 备选镜像标签: `latest-trt-onnx`（TensorRT + ONNX）
- Compose Manager Plus: https://github.com/localjanitor/compose-manager-plus
