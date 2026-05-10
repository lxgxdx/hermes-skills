# MiniMax CN 图像生成 API（image-01）

`image_generate` 工具未配置 FAL_KEY 时，使用此方法直接调用 MiniMax CN 图像生成 API。

## 端点

```
POST https://api.minimaxi.com/v1/image_generation
```

## 认证

从 `~/.hermes/.env` 读取 `MINIMAX_CN_API_KEY`，放在 `Authorization: Bearer <key>` 请求头中。

## 请求格式

```bash
MINIMAX_KEY=$(grep MINIMAX_CN_API_KEY ~/.hermes/.env | cut -d= -f2)
curl -s -X POST "https://api.minimaxi.com/v1/image_generation" \
  -H "Authorization: Bearer $MINIMAX_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "image-01",
    "prompt": "英文 prompt（图像生成提示词）",
    "aspect_ratio": "16:9"
  }'
```

## 参数说明

| 参数 | 值 | 说明 |
|------|----|------|
| `model` | `image-01` | MiniMax 图像生成模型 |
| `prompt` | 字符串 | 英文提示词（中文内容需翻译为英文） |
| `aspect_ratio` | `16:9` / `1:1` / `9:16` | 画幅比例 |

## 响应处理

成功响应示例：
```json
{
  "id": "064e10b8de3b4f1ee392bcb29d1de51f",
  "data": {
    "image_urls": ["https://...jpeg?Expires=...&OSSAccessKeyId=...&Signature=..."]
  },
  "base_resp": {"status_code": 0, "status_msg": "success"}
}
```

图片 URL 有效期约 24 小时。下载到本地：
```bash
curl -s -L "URL" -o /tmp/output.jpg
```

## 中文内容处理

图像生成 prompt 建议使用英文。中文元素（如标题、标签）可以用英文描述风格，但：
- Deep blue → `#1E3A5F` 这样的颜色代码可混用
- 数字和基本词汇可直接写
- 如需精确中文字体效果，可先生成英文底图，再叠加文字层

## 公众号配图推荐配置

| 用途 | aspect_ratio | 风格 |
|------|-------------|------|
| 封面图 | `16:9` | 深色背景 + 品牌色点缀 |
| 文中配图 | `16:9` | 信息图解、流程图 |
| 竖版推送封面 | `9:16` | 全屏大图 |
| 头像/Logo | `1:1` | 简洁图形 |

## 配色参考（公众号风格）

```
深海军蓝背景：#1E3A5F
活力橙点缀：#FF6B35
金黄高亮：#FFD23F
纯白文字：#FFFFFF
浅灰辅助：#F5F5F5
```
