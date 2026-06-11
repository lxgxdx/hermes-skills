---
name: home-assistant-ops
description: Home Assistant 安全操作规范 — 只读边界原则。详细信息查 Wiki（~/ha-wiki/）。
category: smart-home
---

# Home Assistant Operations Guide

## 安全边界（必须遵守）

**只读模式**：只能读取状态/配置，**绝对不能**执行任何操作。

禁止的行为：
- 开灯/关灯、调节温度、开关设备
- 触发自动化、脚本、场景
- 修改 configuration.yaml
- 调用任何写操作 service

如果用户要求执行操作，礼貌拒绝并说明只能读不能写。

---

## 连接信息

**HA 地址**：`http://192.168.88.183:8123`

**凭证文件**：`~/.hermes/.env`（包含 HASS_URL 和 HASS_TOKEN，**不**硬编码在 Skill 里）

```bash
# 查看当前 HA 配置（不暴露 Token）
grep HASS ~/.hermes/.env
```

---

## API 调用方法

所有调用通过 `ha_*` 工具（HA MCP 工具），不暴露 Token。

### 查询所有实体
```
ha_list_entities
ha_list_entities(domain="light")
ha_list_entities(area="客厅")
```

### 查询单个实体状态
```
ha_get_state(entity_id="light.living_room")
```

### 查询可用服务（只读）
```
ha_list_services
ha_list_services(domain="light")
```

---

## 详细信息位置

- Jinja2 模板：`~/ha-wiki/concepts/jinja2-templates.md`
- Lovelace 卡片：`~/ha-wiki/concepts/lovelace-cards.md`
- 各卡片插件：`~/ha-wiki/concepts/*.md`
- 自动化模板：`~/ha-wiki/concepts/automation-templates.md`
- 实体清单：`~/ha-wiki/entities/`
- HA 概念：`~/ha-wiki/concepts/`
- **HA Add-on 调试**：见 `references/hassio-supervisor-api.md`
- **Add-on 装不上快速诊断脚本**：`scripts/check-ha-addon.sh`

---

## HA Add-on 调试（Supervisor API）

⚠️ **此节与只读边界不冲突**：诊断只读，修复由用户决定。

### 关键鉴权坑（必看）

`~/.hermes/.env` 里的 `HASS_TOKEN` 是 **HA Core 的 long-lived token**（用户级）。
`/api/hassio/*` 走 **Supervisor API**，需要带 **hassio/admin scope 的 token**。两者**不通用**：

- 用 HASS_TOKEN 调 `/api/hassio/addons` → **401 Unauthorized**
- Supervisor API 的 token 路径：HA UI → 用户头像 → 长期访问令牌 → 创建（用户必须是 admin）

获取 Supervisor token 后调用方式：

```bash
SUP_TOKEN="<long-lived token from HA UI>"
curl -sS -H "Authorization: Bearer *** "http://192.168.88.183:8123/api/hassio/addons"
```

### Add-on 装不上 / 打不开 web 的三大常见根因

按概率排序，遇到先排查：

**1. GHCR 镜像私有（最常见，~60%）**
GHCR（`ghcr.io/<owner>/<image>`）默认私有，HA Add-on Store 装时走**匿名 pull**，私有包直接 401。
**诊断**：
```bash
curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
  "https://ghcr.io/v2/<owner>/<image>/manifests/latest"
# 返回 401 = 私有，必须改 public
```
**修复**：https://github.com/users/<owner>/packages/container/<image>/settings
→ Danger Zone → Change package visibility → Public（**GitHub API 不支持改 visibility，必须手动**）

**2. Add-on 容器没起 / s6 重启循环（~30%）**
`run.sh` 用了 `set -e` 或 `nohup ... &` 把进程脱离 s6 进程组，s6 报 "not running" 反复重启，日志循环 `legacy-services stopping/stopped`。
**诊断**：在 Add-on 页面 → Log 标签 → 找 `legacy-services` 或 `bashio::` 错误
**修复模式**：s6 容器内多进程应该用 **s6 service 拆分**（daemon / web 各一个 s6 service），不要用 nohup

**3. Ingress 路径不对（~10%）**
如果 `config.yaml` 设了 `ingress: true`，**HA 通过 `/api/hassio/ingress/<addon_slug>/` 反代到容器内部端口**。
- ❌ 直接访问 `http://<ha_ip>:3000` 失败（端口未映射到 host）
- ✅ 走侧边栏入口（自动出现）或 `/api/hassio/ingress/<slug>/` 路径
- Add-on `ports: 3000/tcp: null` 表示**不**暴露给 host（这是正常的）

### 调试用户自己仓库的 Add-on 必读

用户问"我部署的某个 GitHub 仓库 Add-on 装不上"时，**先 `cat` 该仓库的 CLAUDE.md / README.md / Dockerfile / run.sh / config.yaml**。很多仓库把踩过的坑沉淀在 CLAUDE.md 里，能直接定位根因（如 lxgxdx/ha-ai-designer 仓库的 CLAUDE.md 明确写过 GHCR 私有坑）。

---

## 常用实体 ID 参考

通过 `ha_list_entities` 查询，以下是常见类型：

| 类型 | domain |
|------|--------|
| 灯 | light |
| 开关 | switch |
| 传感器 | sensor |
| 气候/空调 | climate |
| 风扇 | fan |
| 摄像头 | camera |
| 人体感应 | binary_sensor |

---

## 设备状态速查（2026-05-09 更新）

| 设备 | 位置 | 状态 |
|------|------|------|
| **FP310**（人体存在传感器） | 西厨 | ✅ **已通过Z2M v2.10.0正式支持** — 无需再监控支持状态 |
| **FP2**（存在传感器） | 父母房 | ✅ 已接入 |
| 温湿度传感器 | 多房间 | ✅ 正常 |
| 空调中枢 QDHKL | — | ✅ 4台格力空调 |
| 窗帘电机 | 书房/客厅/主卧/儿童房 | ✅ 正常 |
| 无线开关 | 多处 | ✅ 正常 |

> ⚠️ **FP310监控cron可禁用**：每日20:00的`FP310 Support Monitor`任务（job ID: 8670107d659c）原为监控Z2M支持状态，现已确认v2.10.0支持，可删除该cron。
