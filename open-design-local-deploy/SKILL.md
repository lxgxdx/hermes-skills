---
name: open-design-local-deploy
description: >
  Open Design 本地源码部署完整流程。适用于 cron 环境（无 Docker/Python/Node 24）下部署。
  触发词：Open Design/deploy/open-design/设计师平台
version: 1.0.0
category: productivity
---

# Open Design 本地源码部署

## 适用场景

在 Linux/cron 环境（非 Docker，无 Python）中，从源码部署 Open Design 并接入 Hermes 检测。

## 核心依赖

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Node.js | **Node 24** | 关键要求，其他版本可能失败 |
| npm | 最新版 | 用于安装依赖 |
| Hermes | 可用 | 用于执行 Hermes 检测 |

## 部署步骤

### Step 1: 准备源码目录

```bash
# 清理并重建目录（避免旧版本干扰）
rm -rf /tmp/open-design
mkdir -p /tmp/open-design

# clone 或复制源码到 /tmp/open-design
cd /tmp/open-design
git clone <repo-url> .
# 或：cp -r <source> /tmp/open-design
```

### Step 2: 安装 Node 24（如未安装）

```bash
# 用 n 安装 Node 24（n 是 Node 版本管理器）
npm install -g n
n 24

# 验证
node -v  # 应显示 v24.x.x
which node
```

> ⚠️ Docker 容器内通常无 Python/Node，不适合此方案。本地 Linux 环境首选。

### Step 3: 安装依赖

```bash
cd /tmp/open-design
npm install
```

### Step 4: 启动服务

```bash
# 开发模式（前台）
npm run dev

# 或后台运行
npm run dev > /tmp/open-design.log 2>&1 &
echo $! > /tmp/open-design.pid
```

### Step 5: Hermes 检测

在 Hermes 中检测 Open Design 是否正常运行：

```python
# 方法：检查进程 + 端口
import subprocess

# 检查进程是否存在
proc = subprocess.run(["pgrep", "-f", "open-design"], capture_output=True)
if proc.returncode == 0:
    print("Open Design 进程运行中")

# 检查端口是否监听
result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
if "3000" in result.stdout or "5173" in result.stdout:
    print("服务端口已监听")
```

## 已知问题

### inotify limit 导致监听失败

**症状**: `npm run dev` 报错类似：
```
Error: ENOSPC: System limit for number of file watchers reached
```

**解决**:
```bash
# 临时生效
echo 524288 > /proc/sys/fs/inotify/max_user_watches

# 永久生效（Ubuntu/Debian）
echo "fs.inotify.max_user_watches=524288" >> /etc/sysctl.conf
sysctl -p
```

### Hermes 检测失败（端口未监听）

**排查**:
1. 确认进程在运行：`pgrep -f "open-design"` 或 `ps aux | grep open-design`
2. 确认端口监听：`ss -tlnp | grep -E "3000|5173|8080"`
3. 查看日志：`tail -50 /tmp/open-design.log`
4. 尝试手动启动并观察输出

### Node 版本不对

**症状**: `npm install` 成功但 `npm run dev` 报语法错误或模块未找到。

**解决**: 确认 Node 版本是 24：
```bash
node -v  # 必须显示 v24.x.x
n 24     # 如不是，重新安装
```

## 与 Docker 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **本地源码（推荐）** | 有 Python/Node、Hermes 可检测 | 需要手动管理进程 |
| Docker | 部署简单 | 容器内无 Python/Node，Hermes 无法检测进程 |

## 持久化注意事项

`/tmp/open-design` 是临时目录，系统重启后会被清空。

如需持久化：
1. 迁移到 `~/open-design/` 或其他持久化路径
2. 创建启动脚本并配置为 cron/daemon
3. 注意 `~/open-design` 路径更稳定

## 验证清单

- [ ] `node -v` 显示 v24.x.x
- [ ] `npm install` 无报错
- [ ] `npm run dev` 启动成功（前台无报错）
- [ ] `ss -tlnp` 确认端口监听
- [ ] Hermes 能检测到进程/端口
