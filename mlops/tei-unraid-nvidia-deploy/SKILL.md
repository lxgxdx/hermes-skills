---
name: tei-unraid-nvidia-deploy
description: 在 Unraid 上通过 Docker 部署 TEI (text-embeddings-inference) 调用 NVIDIA GPU做向量嵌入服务。⚠️ Tesla P4 (Pascal 6.1) 不被支持，需 A10/T4 或更新显卡。
tags: ["unraid", "docker", "tei", "embedding", "nvidia", "gpu"]
category: mlops
---

# TEI + Unraid + NVIDIA GPU 部署指南

## 背景

TEI (Text Embeddings Inference) 是 Hugging Face 出品的 embedding 专用Serving框架，原生支持 OpenAI 兼容 API (`/v1/embeddings`)，比 Ollama 的 embedding 接口更可靠（Ollama embedding 有返回空维度的已知bug）。

## 适用场景

- 本地运行 GBrain 向量搜索
- 需要调用 NVIDIA GPU 做 embedding（BGE-M3 等模型）
- Unraid 服务器部署

## 模型要求

BGE-M3 输出 **1024 维**，不是标准的 1536 维。注意 GBrain 侧配置要同步修改 DIMENSIONS。

---

## Unraid Docker 配置（完整步骤）

### 基础信息

| 字段 | 值 |
|------|-----|
| Name | `tei-bge-m3` |
| Repository | `ghcr.io/huggingface/text-embeddings-inference:cuda-latest` |
| Network Type | `bridge`（或与 GBrain 同网络） |
| Extra Parameters | `--runtime=nvidia` |

### 端口映射

| 字段 | 值 |
|------|-----|
| Container Port | `80` |
| Host Port | `8080` |
| Protocol | `TCP` |

### Environment Variables

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `MODEL_ID` | `BAAI/bge-m3` | HuggingFace 模型名 |
| `MAX_BATCH_TOKENS` | `8192` | 批处理大小控制 |
| `PORT` | `80` | TEI 服务端口 |
| `HUGGINGFACE_HUB_CACHE` | `/data` | 模型文件存放路径 |

### Volume Mappings（卷映射）

| Container Path | Host Path | 说明 |
|----------------|-----------|------|
| `/data` | `/mnt/user/appdata/tei-data/` | 持久化存储模型文件 |

---

## 验证

### 检查容器是否正常运行

```bash
# 查看容器日志
docker logs tei-bge-m3

# 检查健康状态
curl http://<unraid-ip>:8080/health
# 期望返回: {"status":"ok"}
```

### 测试实际 embedding

```bash
curl -X POST http://<unraid-ip>:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input":"测试文本"}'
# 期望返回: 1024维浮点数数组
```

---

## GBrain 侧配置

TEI 跑通后，需要修改 `~/gbrain/src/core/embedding.ts` 三处：

1. **baseURL**: 改为 `http://<unraid-ip>:8080`
2. **MODEL**: `Qwen/Qwen3-Embedding-8B` → `BAAI/bge-m3`
3. **DIMENSIONS**: `1536` → `1024`（BGE-M3 是1024维）

---

## 已知坑

1. `--runtime=nvidia` 是 Unraid 调用 NVIDIA 显卡的必填参数
2. BGE-M3 输出1024维，不是1536维，GBrain 侧 DIMENSIONS 必须同步修改
3. TEI 首次启动要拉取镜像 + 加载模型，需要等待1-2分钟
4. Ollama 的 `/api/embeddings` 接口与 OpenAI SDK 不兼容，不能替代 TEI
5. `cuda-latest` 标签会根据 CUDA 版本自动选择合适镜像

### GPU 兼容性（重要！）

**Tesla P4（Pascal 架构，compute capability 6.1）不被任何现代 Docker 镜像支持。**

TEI 官方支持的 GPU：

| 架构 | Compute Capability | 镜像标签 |
|------|-------------------|----------|
| Ampere 8.0 (A100, A30) | 8.0 | `1.9` |
| Ampere 8.6 (A10, A40) | 8.6 | `86-1.9` |
| Ada Lovelace (RTX 40xx) | 8.9 | `89-1.9` |
| Hopper (H100) | 9.0 | `hopper-1.9` |
| Turing (T4) | 7.5 | `turing-1.9` |
| **Pascal (P4, P40, P100)** | **6.0-6.1** | **❌ 不支持** |

`cuda-latest` 镜像内置 CUDA 12.x，已放弃 Pascal 支持。

**报错**：`cuda compute cap 61 is not supported`

**P4 用户可选方案**：

| 方案 | P4 支持 | 说明 |
|------|---------|------|
| `ghcr.io/huggingface/text-embeddings-inference:cpu-1.9` | ✅ | CPU 版，慢但能跑 |
| `michaelf34/infinity:latest-cpu` | ✅ | Infinity CPU 版，慢 |
| Ollama embedding | ⚠️ | 兼容老卡，但 `/api/embeddings` 返回维度为0（确认 bug） |
| 换 GPU | — | Tesla T4（几百块）是最彻底的解决方案 |

### Ollama Embedding Bug（已确认）

**测试时间**：2026-04-18
**测试环境**：Unraid IP 192.168.88.68，Ollama 端口 11434
**测试模型**：`bge-m3`、`qwen3-embedding`

```bash
curl http://192.168.88.68:11434/api/embeddings \
  -X POST -d '{"model": "bge-m3", "input": "测试文本"}'
# 返回 embedding: [] （维度为0）
```

两个模型均返回 **0 维**。Ollama 的 `/api/embeddings` 接口与 OpenAI SDK 不兼容，不能替代专用 embedding 服务。

### ⚠️ 两个 Infinity 项目容易混淆

| 项目 | 用途 | Docker 镜像 |
|------|------|-------------|
| **michaelf34/infinity** | embedding 推理服务（生成向量） | michaelf34/infinity:latest |
| **infiniflow/infinity** | 向量数据库（存储+检索，类似 Qdrant） | infiniflow/infinity |

用户需要的是 **michaelf34/infinity**，但其所有 recent NVIDIA 镜像基于 CUDA 12.x，**P4 同样不支持**。
