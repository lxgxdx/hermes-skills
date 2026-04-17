---
name: tei-unraid-nvidia-deploy
description: 在 Unraid 上通过 Docker 部署 TEI (text-embeddings-inference) 调用 NVIDIA GPU做向量嵌入服务
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
| Repository | `ghcr.io/huggingface/text-embeddings-inference:latest` |
| Network Type | `bridge` |

### 端口映射

| 字段 | 值 |
|------|-----|
| Container Port | `80` |
| Host Port | `8080` |
| Protocol | `TCP` |

### 模型目录挂载

| 字段 | 值 |
|------|-----|
| Config Type | `Path` |
| Name | `/model` |
| Value | `/mnt/user/ollama/models`（你实际的模型路径） |

### Extra Arguments（关键！）

```
--runtime=nvidia --gpus '"device=GPU-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"' --model-id BAAI/bge-m3 --revision main
```

⚠️ `GPU-...` 替换成你实际的 GPU UUID（从 `nvidia-smi` 或 Unraid GPU 配置页面获取）。

⚠️ `--runtime=nvidia` 是 Unraid 调用 NVIDIA 显卡的必填参数，仅有 `--gpus all` 不够。

⚠️ 引号嵌套：`'"device=..."'` 是必须的。

### Environment Variables（两个必须）

| 变量名 | 值 |
|--------|-----|
| `NVIDIA_VISIBLE_DEVICES` | `GPU-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` |
| `NVIDIA_DRIVER_CAPABILITIES` | `all` |

---

## 验证

### 检查容器是否正常运行

```bash
curl http://<unraid-ip>:8080/health
# 期望返回: {"status":"ok"}
```

### 测试实际 embedding

```bash
curl -X POST http://<unraid-ip>:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input":"测试文本","model":"BAAI/bge-m3"}'
# 期望返回: 1024维浮点数数组
```

---

## GBrain 侧配置

TEI 跑通后，需要修改 `~/gbrain/src/core/embedding.ts` 三处：

1. **baseURL**: 改为 `http://<unraid-ip>:8080`（硅基流动 → TEI）
2. **MODEL**: `Qwen/Qwen3-Embedding-8B` → `BAAI/bge-m3`
3. **DIMENSIONS**: `1536` → `1024`（BGE-M3 是1024维）

---

## 已知坑

1. Unraid 上必须用 `--runtime=nvidia`，单独 `--gpus all` 不够
2. 必须设置 `NVIDIA_VISIBLE_DEVICES` 和 `NVIDIA_DRIVER_CAPABILITIES`
3. BGE-M3 输出1024维，不是1536维，GBrain 侧 DIMENSIONS 必须同步修改
4. TEI 首次启动要拉取镜像 + 加载模型，需要等待1-2分钟
5. Ollama 的 `/api/embeddings` 接口与 OpenAI SDK 不兼容，不能替代 TEI
