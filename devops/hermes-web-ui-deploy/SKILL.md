---
name: hermes-web-ui-deploy
description: hermes-web-ui 安装、启动、局域网访问配置
---

# hermes-web-ui 部署笔记

## 安装
```bash
npm install -g hermes-web-ui
```

## 启动（关键：默认只监听 127.0.0.1！）
```bash
# 本地访问
hermes-web-ui start

# 局域网访问——必须加 HOST=0.0.0.0
HOST=0.0.0.0 hermes-web-ui start [port]
```

## 常用命令
```bash
hermes-web-ui status     # 查看状态
hermes-web-ui stop       # 停止
hermes-web-ui restart    # 重启
hermes-web-ui update     # 更新
```

## Token 认证
启动后在 `~/.hermes-web-ui/server.log` 查看当前 token。
访问格式：`http://IP:8648/#/?token=<TOKEN>`

## 已知问题
- `HOST=0.0.0.0` 环境变量 trick 仅在本次启动生效，下次 restart 可能恢复监听 127.0.0.1
- 每次全新 start 都会换新 token

## 端口
默认 8648，可在 start 后加端口号指定
