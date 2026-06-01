# MiniMax 模型升级参考

## Hermes 模型名格式

使用 `minimax-cn` provider 时，模型名前缀 `minimax-cn/` 会被自动规范化删除。因此：

| 设置值 | 实际调用名称 |
|--------|------------|
| `minimax-cn/MiniMax-M3` | `MiniMax-M3` |
| `minimax-cn/MiniMax-M2.7-highspeed` | `MiniMax-M2.7-highspeed` |

MiniMax Anthropic 兼容端点的模型名就是 `MiniMax-M3`（不加版本后缀）。

## 一键升级命令

```bash
# 1. 修改默认模型
hermes config set model.default minimax-cn/MiniMax-M3

# 2. 立即验证（不必重启 gateway）
hermes chat -q "简单回复：我是MiniMax-M3吗？" -m "minimax-cn/MiniMax-M3" --provider minimax-cn
```

如果回应确认是 M3，则升级成功。新会话自动使用新模型。

## 关键配置

| 配置项 | 值 |
|--------|-----|
| provider | `minimax-cn` |
| base_url | `https://api.minimaxi.com/anthropic`（.env 中 `MINIMAX_CN_BASE_URL`） |
| api_key | .env 中 `MINIMAX_CN_API_KEY` |
| REST API 端点 | `https://api.minimax.io/anthropic/v1`（境外） |

## 回退

```bash
hermes config set model.default minimax-cn/MiniMax-M2.7-highspeed
```

## 注意事项

- `hermes model` 命令是交互式的，不可在非交互环境使用
- 模型切换后需重启 gateway 才能对网关消息生效
- 单次 `hermes chat -q` 可用 `-m` 临时指定模型，不用改配置
