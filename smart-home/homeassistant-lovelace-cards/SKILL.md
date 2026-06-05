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

---

## 仪表板设计模式（Design Patterns）

> 卡片文档告诉你"每张卡怎么用"，这一节告诉你"怎么把它们组成漂亮的仪表板"。
> 详细可复制的样板见 `references/dashboard-design-patterns.md`，空白起步模板见 `templates/dashboard-skeleton.yaml`。

### 四大设计流派（HA 社区 2025-2026 主流）

| 流派 | 代表卡片 | 适合 | 工时 | 视觉 |
|------|---------|------|------|------|
| **A. Bubble Card 极简风** | `bubble-card` + `card-mod` | 苹果/米家风，手机+平板 | 中 | ⭐⭐⭐⭐ |
| **B. 3D 房型数字孪生** | `floor3d-card` | 桌面/iPad 大屏 | 中（需画 3D 房型） | ⭐⭐⭐⭐⭐ |
| **C. 三件套混搭** | `floor3d + bubble + bar` | 兼顾多设备 | 高 | ⭐⭐⭐⭐⭐ |
| **D. 经典 entities/glance** | 内置卡 + `mini-graph` | 简单粗暴 | 低 | ⭐⭐ |

> **决策捷径**：用户已装 22 个 HACS 卡片（包括 bubble_card + floor3d）→ 优先方案 A 或 C。
> 如果只是想看，开内置 `entities` 卡片就够；**别上来就堆 custom card**。

### 核心 5 段式布局（任何方案都适用）

```
┌─────────────────────────────────────┐
│ 第1段：场景栏（4个一键场景按钮）       │   ← button-card
│ 回家/睡眠/影院/全关                   │
├─────────────────────────────────────┤
│ 第2段：房间入口（grid 3列）           │   ← bubble-card pop-up
│ 客厅/餐厅/主卧...                     │
├─────────────────────────────────────┤
│ 第3段：全屋入口（grid 2列）           │   ← bubble-card pop-up
│ 阳台/全屋空调/浴室/摄像头             │
├─────────────────────────────────────┤
│ 第4段：实时环境条                     │   ← bar-card / mini-graph
│ 温湿度/电量/统计                      │
├─────────────────────────────────────┤
│ 第5段：搜索 + 自动化入口              │   ← search-card
└─────────────────────────────────────┘
```

### 调色板规则（必读）

每房间一个**主色**，统一公式：

```yaml
styles:
  card:
    - background: rgba(主色, 0.08)    # 8% 不透明背景
  icon:
    - color: 主色                     # 100% 饱和图标
  name:
    - color: 文字主色
    - font-weight: bold
```

参考 13 色调色板：`#FF6B35` 客厅橙 / `#FF922B` 餐厅 / `#6366F1` 主卧紫蓝 / `#EC4899` 儿童粉 / `#22C55E` 父母绿 / `#0EA5E9` 书房蓝 / `#A855F7` 衣帽间紫 / `#6B7280` 玄关灰 / `#78716C` 走廊暖灰 / `#3B82F6` 全屋蓝 / `#6366F1` 浴室 / `#EF4444` 摄像头红 / `#22C55E` 阳台绿。

---

## ⚠️ Bubble Card Popup 必踩的 5 个坑

1. **必须用 storage 模式建仪表板**（不是 YAML 模式）— 否则 hash 跳转 100% 失败，且无报错
2. **Bubble Card Tools 必须独立装**（不在 Bubble Card 自动依赖里）— 装好后**重启 HA**
3. **主入口的 `hash: '#xxx'` 和 popup 卡片的 `hash: '#xxx'` 必须一字不差** — 大小写、连字符、特殊字符都要核对
4. **popup 卡片也算"一张卡片"** — 添加到仪表板，**不要点它**，它只在 hash 被触发时显示
5. **iPad 宽度要写 `width: 95vw; max-width: 500px`** — 不写 popup 会占满整屏，iPad 看不清

```yaml
# ✅ 正确：主入口
- type: custom:bubble-card
  card_type: pop-up
  hash: '#popup-ke_ting'   # ← 这个
  name: 客厅
  icon: mdi:sofa

# ✅ 正确：popup 卡片（独立一张卡）
- type: custom:bubble-card
  card_type: pop-up
  hash: '#popup-ke_ting'   # ← 和上面一字不差
  cards:
    - ...  # popup 内的子卡片
```

### 调试 popup 不弹

1. 打开浏览器 F12 → Console，看是否有红字
2. 90% 情况是 hash 不一致 → 复制粘贴两边对照
3. 9% 情况是 Bubble Card Tools 没装 → HACS 重装 + 重启 HA
4. 1% 情况是 YAML 模式仪表板 → 新建一个 storage 模式的

---

## 中文环境特殊技巧（拼音前缀房间归类）

> 用户的实体 ID 拼音前缀是金矿，entity_id 命名规则暴露了**房间归属**。用 Python 脚本一次扫出所有归类。

```python
# 核心逻辑
ROOM_MAP = {
    "ke_ting": "客厅", "can_ting": "餐厅",
    "zhu_wo": "主卧", "er_tong_fang": "儿童房",
    "fu_mu_fang": "父母房", "shu_fang": "书房",
    # ...
}

def room_of(eid):
    base = eid.split(".",1)[1]
    parts = base.split("_")
    for i in range(min(3, len(parts))):
        p = "_".join(parts[:i+1])
        if p in ROOM_MAP: return ROOM_MAP[p]
    return "其他"
```

**跳过元数据**（重要 — 否则卡片会塞满）：
```python
SKIP_SUFFIX = ("_power_outage_memory", "_flip_indicator_light",
               "_led_disabled_night", "_vertical_swing", "_alarm",
               "_blow", "_heating", "_ventilation", "_child_lock",
               "_status_indicator_light", "_dnd_switch",
               "_valley_electricity_switch", "_zone_enable",
               "_zout1_enable", "_illuminance_fast_update",
               "_ai_interference_source_selfidentification",
               "_ai_sensitivity_adaptive", "_uv", "_switch_status")
SKIP_KEYWORDS = ["_use_listen_light", "dahua_", "frigate_card",
                 "_zigbee_permit", "permit_join", "0x", "32c3",
                 "electricity_meter_", "qdhkl_ac_",
                 "keting_detect", "keting_motion",  # Frigate 派生
                 "keting_recordings", "keting_snapshots",
                 "keting_review", "keting_audio", "keting_ptz",
                 "d14feb", "0e949f", "screen",  # 摄像头 ID
                 "apple_tv", "qbittorrent",
                 "indicator_light"]
```

---

## 相关资源

- `references/dashboard-design-patterns.md` — 4 大流派详细对比 + 完整 13 房间 popup YAML 样板（碧桂园案例）
- `templates/dashboard-skeleton.yaml` — 空白起步骨架（场景栏 + 9 房间 grid + 环境条）
- `templates/bubble-popup-template.yaml` — 单个房间 popup 的最小可工作模板
- `scripts/scan_rooms.py` — 拼音前缀房间归类扫描脚本

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
