---
name: openwrt-openclash-deploy
description: OpenWRT 上部署 OpenClash 的完整流程，包括内核下载、Country.mmdb 问题解决、ShadowSocks 订阅配置。触发词：OpenClash/ssr-plus/路由器代理/OpenWRT VPN
---

# OpenWRT OpenClash 部署指南

## 场景
从 ShadowSocksR Plus+ (ssr-plus) 迁移到 OpenClash，解决 GitHub/DockerHub 访问不稳定问题。

## 前提条件
- OpenWRT 路由器（x86_64 架构）
- 已有 ShadowSocks 订阅链接
- SSH 访问权限（root 用户）

## 安装 OpenClash

### 方法 1：通过 LUCI 界面
1. 系统 → 软件包 → 搜索 `luci-app-openclash` → 安装
2. 服务 → OpenClash → 全局设置

### 方法 2：通过 SSH
```bash
opkg update
opkg install luci-app-openclash
```

## 配置 OpenClash

### 1. 添加订阅
- LUCI → 服务 → OpenClash → 全局设置
- 订阅设置 → 填入 ShadowSocks 订阅 URL
- 格式：`https://example.com/api/v1/client/subscribe?token=xxx`

### 2. 启用 OpenClash
在 LUCI 界面勾选「启动 OpenClash」

## 内核下载问题解决

### 问题：TUN 内核下载失败
```
【TUN】版本内核更新失败，请检查网络或稍后再试！
```

### 解决方案：手动下载 Meta 内核

**步骤 1：下载内核文件**
```bash
# 在能访问 GitHub 的机器上下载
curl -L -o /tmp/clash-linux-amd64-compatible.tar.gz \
  "https://raw.githubusercontent.com/vernesong/OpenClash/core/dev/meta/clash-linux-amd64-compatible.tar.gz"

# 解压并重命名
tar -xzf /tmp/clash-linux-amd64-compatible.tar.gz
cp clash clash_meta
chmod +x clash_meta
```

**步骤 2：上传到 OpenWRT**
```bash
# 打包
tar -czf /tmp/openclash_core.tar.gz clash_meta

# 上传
scp /tmp/openclash_core.tar.gz root@192.168.88.1:/tmp/

# SSH 登录 OpenWRT 安装
mkdir -p /etc/openclash/core
tar -xzf /tmp/openclash_core.tar.gz -C /etc/openclash/core/
chmod +x /etc/openclash/core/clash_meta
```

**步骤 3：启用 Meta 内核**
在 LUCI 界面启用 Meta 内核选项

## Country.mmdb 问题解决

### 问题：MMDB invalid
```
MMDB invalid, remove and download
```

### 解决方案：让 OpenClash 自动下载
```bash
# 运行 OpenClash 的 IP DB 下载脚本
/usr/share/openclash/openclash_ipdb.sh

# 验证文件
ls -la /etc/openclash/Country.mmdb
# 正常大小：约 200KB
```

## 启动和测试

### 启动 OpenClash
在 LUCI 界面点击「启动」

### 测试代理连接
```bash
# 测试 GitHub（通过代理）
curl -sI --connect-timeout 15 --proxy http://192.168.88.1:7890 https://github.com

# 测试 Docker Hub
curl -sI --connect-timeout 15 --proxy http://192.168.88.1:7890 https://registry.hub.docker.com
```

## 故障排除

### 1. OpenClash 未启动
检查 LUCI 界面中 OpenClash 是否已启用

### 2. 内核文件权限问题
```bash
chmod +x /etc/openclash/core/clash_meta
ls -la /etc/openclash/core/
```

### 3. 订阅节点未加载
- 检查订阅 URL 是否正确
- 检查网络连接（OpenWRT 能否访问订阅服务器）

### 4. Country.mmdb 持续无效
```bash
# 删除并重新下载
rm /etc/openclash/Country.mmdb
/usr/share/openclash/openclash_ipdb.sh

# 创建软链接
ln -sf /etc/openclash/Country.mmdb /etc/openclash/core/Country.mmdb
```

### 6. LUCI 面板可以开启但内核崩溃
**症状：**
- LUCI 面板可以点击"启动"，但 OpenClash 无法正常运行
- 系统日志显示大量错误：`egrep: /etc/clash/config.yaml: No such file or directory`
- 脚本语法错误：`/usr/share/clash/check_dtun_core_version.sh: line 9: syntax error: unexpected "elif"`

**根因：**
1. **配置文件路径不匹配**：OpenClash 脚本在找 `/etc/clash/config.yaml`，但实际配置文件在 `/etc/openclash/config/config.yaml`
2. **脚本语法错误**：某些检查脚本有语法问题
3. **init.d 脚本 UCI 错误**：`uci: Entry not found` 和 `sh: out of range` 错误

**解决方案：**
1. **创建配置文件符号链接**：`ln -sf /etc/openclash/config/config.yaml /etc/clash/config.yaml`
2. **修复脚本语法错误**：检查 `/usr/share/clash/check_dtun_core_version.sh` 文件，修复换行符问题
3. **手动测试内核**：直接运行 `/etc/openclash/core/clash_meta` 验证内核是否正常工作
4. **检查 UCI 配置**：确保 `uci show openclash` 显示正确的配置路径和启用状态

## 性能优化

### 1. 规则分流配置
- LUCI → OpenClash → 规则设置
- 启用「规则分流」
- 添加 GitHub、DockerHub 等域名到代理规则

### 2. 节点选择策略
- 启用「自动选择」
- 设置「延迟测试」

## 维护命令

### 日常检查
```bash
# 查看进程
ps | grep clash_meta

# 测试连接
curl -s --proxy http://192.168.88.1:7890 https://api.github.com | head -3
```

### 清理临时文件
```bash
# 清理日志
rm /tmp/openclash.log
```

## 注意事项

1. **内核兼容性**：确保下载的内核与 OpenWRT 架构匹配（x86_64）
2. **内存使用**：OpenClash 比 ssr-plus 更耗内存，确保路由器有足够 RAM
3. **规则更新**：定期更新分流规则以获得最佳体验
4. **备份配置**：配置稳定后备份 `/etc/openclash/` 目录

## 与 ssr-plus 对比

| 特性 | ssr-plus | OpenClash |
|------|----------|-----------|
| 配置复杂度 | 简单 | 复杂 |
| 功能丰富度 | 基础 | 丰富 |
| 规则分流 | 有限 | 强大 |
| 资源占用 | 低 | 中高 |
| GitHub/DockerHub 优化 | 一般 | 优秀 |
| 多节点管理 | 手动 | 自动 |

## 迁移建议

1. **先测试**：在非高峰时段迁移，避免影响网络
2. **保留备份**：备份 ssr-plus 配置，随时可回退
3. **逐步优化**：先确保基本功能正常，再优化规则分流
4. **监控性能**：观察路由器 CPU/内存使用情况