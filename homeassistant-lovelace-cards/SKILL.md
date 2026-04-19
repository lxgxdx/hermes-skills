---
name: homeassistant-lovelace-cards
description: Home Assistant Lovelace UI 卡片定制技能 — REST API 发现已装卡片、Jinja2 模板、Bubble Card、Button Card、Mini Graph Card 等主流自定义卡片的用法和示例。
category: smart-home
tags: [home-assistant, lovelace, bubble-card, button-card, mini-graph-card, template, jinja2, bar-card, card-tools, hacs]
---

# Home Assistant Lovelace Cards & Templates

## 通过 REST API 发现已装卡片

通过 `api/states` 枚举 `update.*_card_update` 实体，可以查所有通过 HACS 安装的卡片插件及其版本：

```bash
curl -s "http://HA地址:8123/api/states" \
  -H "Authorization: Bearer TOKEN" | python3 -c "
import sys,json
states=json.load(sys.stdin)
cards=[s for s in states if 'update' in s['entity_id']
       and ('card' in s['entity_id'].lower()
            or 'bubble' in s['entity_id'].lower()
            or 'layout' in s['entity_id'].lower()
            or 'swipe' in s['entity_id'].lower()
            or 'declutter' in s['entity_id'].lower()
            or 'frigate' in s['entity_id'].lower()
            or 'plotly' in s['entity_id'].lower()
            or 'bar_card' in s['entity_id'].lower()
            or 'search_card' in s['entity_id'].lower()
            or 'mini_graph' in s['entity_id'].lower()
            or 'floor3d' in s['entity_id'].lower()
            or 'vacuum' in s['entity_id'].lower()
            or 'card_tools' in s['entity_id'].lower()
            or 'card_mod' in s['entity_id'].lower()
            or 'weather_card' in s['entity_id'].lower()
            or 'battery' in s['entity_id'].lower())]
for c in sorted(cards, key=lambda x: x['entity_id']):
    v = c['attributes'].get('installed_version','?')
    n = c['entity_id'].replace('update.','').replace('_update','')
    print(f'{n} | {v}')
"
```

**已发现的卡片**（2026-04实测）：bar_card, battery_state_card_entity_row, bubble_card, button_card, card_mod, card_tools, colorfulclouds_weather_card, decluttering_card, floor3d_card, frigate_card, hue_like_light_card, layout_card, mini_graph_card, plotly_graph_card, search_card, simple_weather_card, stack_in_card, swipe_card, vertical_stack_in_card, xiaomi_vacuum_map_card, your_ha_digital_twin_floor3d_card

## 常用链接

- Button Card 文档：https://custom-cards.github.io/button-card/stable/
- Bubble Card（GitHub）：https://github.com/Clooos/Bubble-Card
- Bubble Card Tools（GitHub）：https://github.com/Clooos/Bubble-Card-Tools
- Mini Graph Card（GitHub）：https://github.com/kalkih/mini-graph-card
- HA 模板文档：https://www.home-assistant.io/docs/templating/
- HA 模板模式：https://www.home-assistant.io/docs/templating/patterns/

## 安装方式（HACS）

推荐通过 HACS 安装：
- 搜索 `button-card`
- 搜索 `Bubble Card`（同时需要装 `Bubble Card Tools`）
- 搜索 `mini-graph-card`

手动安装需要在 `configuration.yaml` 的 `lovelace.resources` 下添加：

```yaml
lovelace:
  resources:
    - url: /local/community/button-card/button-card.js
      type: module
    - url: /local/community/bubble-card/bubble-card.js
      type: module
    - url: /local/community/mini-graph-card/mini-graph-card.js
      type: module
```

---

## HA 模板基础（Jinja2）

### 三个定界符

```
{{ ... }}   输出表达式结果（最常用）
{% ... %}   逻辑控制（if/for，不输出）
{# ... #}   注释
```

### 常用函数

| 函数 | 说明 |
|------|------|
| `states('entity_id')` | 获取状态字符串 |
| `state_attr('entity_id', 'attr')` | 获取属性值 |
| `is_state('entity_id', 'state')` | 判断状态是否等于某值 |
| `has_value(entity_id)` | 检查是否有效值（排除 unknown/unavailable）|
| `float(val, default)` / `int(val, default)` | 类型转换，带默认值 |
| `now()` | 当前时间 |

### Filter 示例

```jinja2
# 计数：开了多少灯
{{ states.light | selectattr('state', 'eq', 'on') | list | count }}

# 最低电量
{{ states.sensor | selectattr('attributes.device_class', 'eq', 'battery')
   | selectattr('entity_id', 'has_value')
   | map(attribute='state') | map('float') | min | round(0) }}%

# 条件文本
{% if is_state('device_tracker.frenck', 'home') %}
  Frenck is home.
{% else %}
  Frenck is at {{ states('device_tracker.frenck') }}.
{% endif %}

# 安全数值（防止 unknown 造成错误）
{% set temp = states('sensor.temperature') | float(0) %}
温度: {{ temp | round(1) }}°C
```

### 遍历循环

```jinja2
{% for light in states.light %}
  {% if light.state == 'on' %}{{ light.name }}{% endif %}
{% endfor %}
```

---

## Button Card（custom-cards/button-card）

Stars: 2.4k | 版本: v7.0.1

### 基础按钮

```yaml
type: custom:button-card
entity: light.living_room
icon: mdi:lightbulb
name: Living Room
show_state: true
tap_action:
  action: toggle
```

### 带状态的按钮（不同状态不同颜色/图标）

```yaml
type: custom:button-card
entity: light.living_room
icon: mdi:lightbulb
state:
  - value: 'on'
    color: yellow
    icon: mdi:lightbulb
  - value: 'off'
    color: grey
    icon: mdi:lightbulb-off
styles:
  icon:
    - color: >-
        {% if is_state(config.entity, 'on') %} yellow
        {% else %} grey
        {% endif %}
```

### 滑动面板（hold 显示 more-info）

```yaml
type: custom:button-card
entity: climate.ac_unit
icon: mdi:air-conditioner
name: AC
tap_action:
  action: toggle
hold_action:
  action: more-info
```

### 长按/双击不同动作

```yaml
type: custom:button-card
entity: light.fan
icon: mdi:fan
tap_action:
  action: toggle
hold_action:
  action: call-service
  service: fan.set_speed
  data:
    speed: high
double_tap_action:
  action: call-service
  service: fan.set_speed
  data:
    speed: low
```

### 样式定制

```yaml
styles:
  card:
    - border-radius: 16px
    - box-shadow: 0 4px 8px rgba(0,0,0,0.3)
    - padding: 8px
  icon:
    - width: 48px
    - color: auto   # 根据 state 自动变色
  name:
    - font-size: 14px
    - color: white
  state:
    - font-size: 12px
    - color: '#aaa'
```

### 关键配置项

| 配置 | 说明 |
|------|------|
| `color_type` | `icon`（仅图标）或 `card`（整个卡片）|
| `show_state` | 是否显示状态值 |
| `lock` / `pin` | 锁定/密码保护 |
| `momentary` | 按下后自动恢复 |
| `extra_styles` | 额外 CSS 样式 |

---

## Bubble Card（Clooos/Bubble-Card）

Stars: 4.1k | 需要同时安装 Bubble Card Tools

气泡弹出式卡片，带 Module Store 功能。

### 1. Pop-up Card（弹出面板）

```yaml
type: custom:bubble-card
card_type: popup
entity: climate.ac_unit
icon: mdi:air-conditioner
name: AC Unit
```

### 2. Slider Card（滑块卡）

```yaml
type: custom:bubble-card
card_type: slider
entity: light.living_room
icon: mdi:lightbulb
```

### 3. Button Card（气泡按钮）

```yaml
type: custom:bubble-card
card_type: button
entity: switch.fan
icon: mdi:fan
name: Fan
```

### 4. Cover Card（窗帘/卷帘门）

```yaml
type: custom:bubble-card
card_type: cover
entity: cover.garage_door
```

### 5. Climate Card（空调卡）

```yaml
type: custom:bubble-card
card_type: climate
entity: climate.ac_unit
```

### 6. Notification Card（通知卡）

```yaml
type: custom:bubble-card
card_type: notification
icon: mdi:alert
title: Doorbell
content: Someone is at the door!
```

---

## Mini Graph Card（kalkih/mini-graph-card）

Stars: 3.8k | 传感器历史曲线图

### 基础图

```yaml
type: custom:mini-graph-card
entities:
  - sensor.temperature
  - sensor.humidity
hours_to_show: 24
line_width: 2
font_size: 75
```

### 多实体 + 样式

```yaml
type: custom:mini-graph-card
entities:
  - entity: sensor.indoor_temp
    name: Indoor
    color: '#ff9800'
    show_fill: true
    smooth: true
  - entity: sensor.outdoor_temp
    name: Outdoor
    color: '#2196f3'
hours_to_show: 48
line_width: 3
points_per_hour: 0.5
animate: true
show:
  labels: true
  legend: true
```

### 关键配置

| 配置 | 说明 |
|------|------|
| `hours_to_show` | 显示多少小时历史 |
| `line_width` / `line_color` | 线条粗细/颜色 |
| `fill` / `show_fill` | 填充曲线下方区域 |
| `smooth` | 平滑曲线 |
| `points_per_hour` | 数据点密度，越小越平滑 |
| `state_map` | 状态映射（如 0→Closed，100→Open）|
| `show.legend` / `show.labels` | 显示图例/标签 |

---

## Stack 卡片组合布局

用 `horizontal-stack` / `vertical-stack` 组合多个卡片：

```yaml
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: custom:button-card
        entity: light.living_room
        name: Living
      - type: custom:button-card
        entity: light.bedroom
        name: Bedroom
      - type: custom:button-card
        entity: light.kitchen
        name: Kitchen
  - type: custom:mini-graph-card
    entities:
      - sensor.temperature
    hours_to_show: 6
```

---

## 调试技巧

- **模板调试**：HA 开发者工具 → 模板，可实时预览模板输出
- **Card 调试**：在 Lovelace 右上角点 ⋮ → 编辑仪表板 → 检查卡片 YAML
- **实体状态**：开发者工具 → 状态，可查看所有实体当前状态和属性

## 更多卡片

以下卡片用法详见 HA Wiki（~/ha-wiki/）：

| 卡片 | 版本 | 说明 |
|------|------|------|
| bar_card | v3.2.0 | 条形图展示数值/百分比 |
| plotly_graph_card | v3.3.5 | 交互式图表（折线/柱状/饼图） |
| battery_state_card_entity_row | v4.2.0 | Entities行内电池进度条 |
| hue_like_light_card | v1.9.0 | Hue风格圆形色相环控制盘 |
| xiaomi_vacuum_map_card | v2.3.2 | 扫地机地图可视化控制 |
| floor3d_card | v.1.5.3 | 3D数字孪生楼层平面图 |
| search_card | efd0c2c | 仪表板全局搜索框 |
| card_tools | v11 | 多个卡片依赖的基础工具库 |
| simple_weather_card | v0.8.5 | 轻量天气卡片 |
| colorfulclouds_weather_card | v2.0.0 | 彩云天气卡片 |
