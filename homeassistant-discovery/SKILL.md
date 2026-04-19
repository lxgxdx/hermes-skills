---
name: homeassistant-discovery
description: 通过 HA REST API 发现已安装集成、卡片插件、实体分布的方法。适用于无法访问 lovelace/config 端点时的替代方案。
category: smart-home
tags: [home-assistant, rest-api, hacs, cards, discovery]
---

# Home Assistant API 探测技巧

## 发现 HACS 安装的卡片插件

HA 的 `api/lovelace/config` 和 `api/lovelace/dashboards` 在某些配置下返回 404，但所有通过 HACS 安装的卡片/插件都会注册为 `update.*` 实体。查询所有状态并过滤即可枚举：

```bash
curl -s "http://HA地址:8123/api/states" \
  -H "Authorization: Bearer $HASS_TOKEN" | python3 -c "
import sys,json
states=json.load(sys.stdin)
# 找 update.* 实体（包含所有 HACS 卡片的更新检测）
for s in states:
    eid=s['entity_id']
    if eid.startswith('update.') and any(k in eid for k in [
        'card','bubble','bar','plotly','swipe','frigate','mini_graph',
        'declutter','layout','card_mod','battery','weather','vacuum',
        'search','card_tools','floor3d','stack'
    ]):
        attrs=s.get('attributes',{})
        print(eid, '|', attrs.get('installed_version','?'), '|', attrs.get('latest_version','?'))
"
```

**原理**：HACS 安装的每个卡片插件都会注册一个 `update.<plugin_name>_update` 实体，实体名即插件名。

## 实体域分布统计

```bash
curl -s "http://HA地址:8123/api/states" \
  -H "Authorization: Bearer $HASS_TOKEN" | python3 -c "
import sys,json
states=json.load(sys.stdin)
domains={}
for s in states:
    d=s['entity_id'].split('.')[0]
    domains[d]=domains.get(d,0)+1
for k,v in sorted(domains.items(),key=lambda x:-x[1]):
    print(f'{k}: {v}')
print(f'Total: {len(states)}')
"
```

## HA 基本信息

```bash
curl -s "http://HA地址:8123/api/config" \
  -H "Authorization: Bearer $HASS_TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('version:', d.get('version'))
print('location:', d.get('location_name'))
print('unit_system:', d.get('unit_system'))
print('language:', d.get('language'))
"
```

## 常见 API 端点

| 端点 | 说明 |
|------|------|
| `/api/states` | 所有实体状态 |
| `/api/config` | HA 基本配置 |
| `/api/lovelace/config` | Lovelace 配置（可能404）|
| `/api/lovelace/dashboards` | 仪表板列表（可能404）|
| `/api/services` | 所有可用的 service |
| `/api/events` | 事件类型列表 |
| `/api/history/period?filter_entity_id=light.xxx` | 实体历史 |

## 环境变量

```
HASS_URL=http://192.168.88.183:8123
HASS_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 已知限制

- `api/lovelace/config` 返回 404 时，用 `update.*` 实体枚举卡片
- Token 需要 Long-Lived Access Token（在 HA Profile 页面创建）
- 只读操作（GET），不涉及 service call

## 权限约定（重要）

连接 HA 前必须明确权限边界：**只读**。
- ✅ 可以：读取实体状态、配置信息、版本、设备列表
- ❌ 禁止：开灯/关灯、修改配置、触发自动化、send service

## HA Wiki 知识库

- 路径：`~/ha-wiki/`（独立于 Frigate `~/wiki/`）
- Wiki 页面总数：19（截至 2026-04-20）
- 内容：Jinja2 模板、Lovelace 卡片（18种）、自动化模板
- 发现：卡片插件通过 `update.*` 实体枚举，共发现 22 个已安装卡片
