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
