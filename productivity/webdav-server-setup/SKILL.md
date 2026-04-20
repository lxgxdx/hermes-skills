---
name: webdav-server-setup
title: WebDAV Server Setup for Obsidian Sync
description: 快速部署 wsgidav WebDAV 服务器，支持 Obsidian 移动端同步。包含匿名访问配置、多目录支持、以及常见配置问题解决。
tags:
  - webdav
  - obsidian
  - sync
  - wsgidav
  - mobile
---

# WebDAV Server Setup for Obsidian Sync

快速部署一个轻量级 WebDAV 服务器，用于 Obsidian 移动端同步笔记库。

## 适用场景

- Obsidian iOS/Android 通过 WebDAV 同步服务器上的笔记库
- 需要匿名访问或简单认证的局域网文件共享
- 多个笔记库（wiki、klipper-wiki 等）需要分别挂载

## 安装依赖

```bash
python3 -m venv ~/.hermes/webdav-venv
~/.hermes/webdav-venv/bin/pip install wsgidav cheroot
```

## 快速启动（匿名访问）

最简单的单目录服务：

```bash
~/.hermes/webdav-venv/bin/wsgidav \
  --port=8080 \
  --host=0.0.0.0 \
  --root=/home/lxgxdx/wiki \
  --auth=anonymous \
  --browse \
  -v
```

**参数说明：**
- `--port=8080`: 服务端口
- `--host=0.0.0.0`: 监听所有网络接口
- `--root=/path/to/dir`: 要共享的目录
- `--auth=anonymous`: 匿名访问（无需密码）
- `--browse`: 启用目录浏览
- `-v`: 详细日志

## 配置认证访问

如果需要用户名密码认证，使用配置文件：

```yaml
# ~/.hermes/webdav.yaml
host: 0.0.0.0
port: 8080

provider_mapping:
  "/wiki": /home/lxgxdx/wiki

simple_dc:
  user_mapping:
    "*":
      accept: true
      credentials:
        - user: hermes
          password: hermes123

verbose: 1
```

启动命令：
```bash
~/.hermes/webdav-venv/bin/wsgidav -c ~/.hermes/webdav.yaml
```

## 多目录配置

wsgidav 不支持多个 `--root` 参数，但可以通过配置文件实现：

```yaml
host: 0.0.0.0
port: 8080

provider_mapping:
  "/wiki": /home/lxgxdx/wiki
  "/klipper-wiki": /home/lxgxdx/klipper-wiki
  "/hermes": /home/lxgxdx

simple_dc:
  user_mapping:
    "*": true  # 匿名访问所有目录

verbose: 1
```

## 开机自启（Systemd）

创建 systemd 服务文件：

```ini
# ~/.config/systemd/user/webdav.service
[Unit]
Description=Hermes WebDAV Server
After=network.target

[Service]
Type=simple
User=lxgxdx
ExecStart=/home/lxgxdx/.hermes/webdav-venv/bin/wsgidav --port=8080 --host=0.0.0.0 --root=/home/lxgxdx/wiki --auth=anonymous --browse -v
Restart=on-failure
RestartSec=5
StandardOutput=append:/tmp/webdav.log
StandardError=append:/tmp/webdav.log

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
systemctl --user daemon-reload
systemctl --user enable --now webdav.service
```

## Obsidian 移动端配置

**iOS/Android 设置：**
1. 打开 Obsidian → 设置 → 同步
2. 选择 **WebDAV**
3. 填写：
   - **文件夹**：本地文件夹名（如 `hermes-wiki`）
   - **WebDAV URL**：`http://192.168.88.213:8080/`
   - **用户名/密码**：根据配置填写（匿名访问留空）

**注意：**
- Obsidian 一次只能同步一个笔记库
- 多个笔记库需要在 Obsidian 中创建多个独立的笔记库配置
- 确保手机和服务器在同一局域网

## 常见问题

### 1. 401 Access not authorized
**原因**：`simple_dc.user_mapping` 配置格式错误
**解决**：使用 `"*": true` 或正确的 credentials 结构

### 2. 服务启动但无法访问
**原因**：防火墙或 SELinux 阻止
**解决**：
```bash
# 检查端口
ss -tlnp | grep 8080
# 临时关闭防火墙（测试用）
sudo ufw allow 8080
```

### 3. 多目录配置失败
**原因**：wsgidav 命令行不支持多个 `--root`
**解决**：使用配置文件 + `provider_mapping`

### 4. 性能问题
**建议**：
- 使用 `--auth=anonymous` 减少认证开销
- 避免在 WebDAV 上跑大型文件同步
- 考虑使用 Syncthing 替代（更适合大量小文件）

## 备选方案

如果 wsgidav 配置太复杂，考虑：

1. **Syncthing**：P2P 同步，更适合 Obsidian
2. **nginx WebDAV**：性能更好，配置更复杂
3. **rclone serve webdav**：支持多种后端

## 验证

```bash
# 检查服务是否运行
curl -s http://localhost:8080/

# 带认证测试
curl -u hermes:hermes123 http://localhost:8080/wiki/
```

## 参考

- [wsgidav GitHub](https://github.com/mar10/wsgidav)
- [Obsidian WebDAV Sync Docs](https://help.obsidian.md/Advanced+topics/Third-party+sync)
- [Systemd User Services](https://wiki.archlinux.org/title/Systemd/User)