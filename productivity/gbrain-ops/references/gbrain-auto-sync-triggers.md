# GBrain 主动同步触发清单

## 必须同步的场景（对话结尾检查）

以下任一发生时，当前对话结束前必须 `gbrain put`：

- [ ] 用户纠正了我的工作流/格式/偏好（"不是说过不要XXX吗"）
- [ ] 发现新的工具技巧、绕过方法、调试路径
- [ ] 创建或修改了 Skill
- [ ] 重要约定（"有deadline要主动汇报"）
- [ ] 非 trivial 的问题解决方案（搜索/查了多种方案才解决）
- [ ] 用户给了模板/示例（"按这个风格生成"）
- [ ] API/服务故障及修复过程（token失效、404等）

## 推荐 slug 格式

```
<category>-<what>-<date>

示例：
gbrain-embedding-siliconflow-fix-2026-05-12
ppt-master-wechat-style-template-2026-05-11
hermes-active-sync-protocol-2026-05-12
```

## 快速同步命令

```bash
# shell 方式
~/.bun/bin/bun run ~/gbrain/src/cli.ts put <slug> --stdin << 'EOF'
内容...
EOF

# 环境确认
EMBEDDING_BASE_URL=http://192.168.88.68:8081 ~/.bun/bin/bun run ~/gbrain/src/cli.ts embed --slugs <slug>
~/.bun/bin/bun run ~/gbrain/src/cli.ts search <关键词>
```

## 跨 session 记忆原则

收到用户问题/请求时，**先**搜 GBrain 再行动：
```
gbrain search <关键词>  # 或
session_search <关键词>  # Hermes 历史
```
