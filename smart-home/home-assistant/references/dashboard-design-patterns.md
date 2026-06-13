# Dashboard 设计模式详解（碧桂园案例）

> 2026-06-05 实测：HA 2026.6.0 / 1499 实体 / 48 灯 / 11 窗帘 / 6 空调+浴霸 / 22 HACS 卡片已装
> 用户在 4 个方案中选了 **方案 A：纯 Bubble Card 极简风**
> 完整方案文档：`~/ha-wiki/solutions/lovelace-minimalist-bubble-card.md`（32.5KB）

## 4 大流派横向对比

| 维度 | A. Bubble 极简 | B. 3D 房型 | C. 三件套 | D. 经典 entities |
|------|----------------|------------|----------|------------------|
| 工时 | 1-2 天 | 1-2 天（画 3D）| 4-6 天 | 1 小时 |
| 视觉冲击 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 实用性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 手机体验 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| iPad 体验 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 已装卡片复用 | 80% | 70% | **100%** | 30% |

## 已装卡片盘点（2026-06 碧桂园）

```
bar_card v3.2.0
battery_state_card_entity_row v4.2.0
bubble_card v3.2.2
button_card v7.0.1
card_mod v4.2.1
card_tools v11
colorfulclouds_weather_card v2.0.0
decluttering_card v1.0.0
floor3d_card v1.5.3              ← 极少数人装的高阶卡
frigate_card v7.27.4
hue_like_light_card v1.11.0
layout_card v2.4.7
mini_graph_card v0.13.0
plotly_graph_card v3.3.5
search_card efd0c2c
simple_weather_card v0.8.5
stack_in_card v0.2.0
swipe_card v5.0.0
vertical_stack_in_card v1.0.1
xiaomi_vacuum_map_card v2.3.2
your_ha_digital_twin_floor3d_card v1.5.3
```

## 方案 A 完整结构（碧桂园落地版）

### 主仪表板 5 段式

1. **场景栏**（horizontal-stack，4 个 button-card）：回家/睡眠/影院/全关
2. **房间网格**（grid columns:3）：9 个 bubble-card pop-up 入口
3. **全屋入口**（grid columns:2）：阳台/全屋空调/浴室/摄像头
4. **环境条**：bar-card（温湿度横向条）+ mini-graph-card（24h 温度曲线）
5. **搜索 + 自动化**：search-card + button-card（导航到 /config/automation）

### 13 个房间 popup hash 映射

| 房间 | hash | 内部卡组合 |
|------|------|-----------|
| 客厅 | `#popup-ke_ting` | 灯组 + 5 单灯 grid + 窗帘 + 窗纱 + 空调 + 排风扇 |
| 餐厅 | `#popup-can_ting` | 6 灯 grid |
| 主卧 | `#popup-zhu_wo` | 6 灯 grid + 窗帘 + 窗纱 + 空调 + 浴霸 |
| 儿童房 | `#popup-er_tong_fang` | 3 灯 grid + 窗帘 + 窗纱 + 空调 |
| 父母房 | `#popup-fu_mu_fang` | 4 灯 grid + 窗帘 + 窗纱 + 空调 |
| 书房 | `#popup-shu_fang` | 2 灯 grid + 窗帘 + 窗纱 |
| 衣帽间 | `#popup-yi_mao_jian` | 1 灯 |
| 玄关 | `#popup-xuan_guan` | 1 灯 + 2 夜灯 grid |
| 走廊 | `#popup-zou_lang` | 2 灯 grid |
| 阳台 | `#popup-yang_tai` | 3 灯 grid + UV + 晾衣架 cover |
| 全屋空调 | `#popup-kong_tiao` | 4 空调 grid |
| 浴室 | `#popup-yu_shi` | 2 浴霸 climate + 换气 + 暖风 button |
| 摄像头 | `#popup-she_xiang_tou` | 4 picture-entity grid + 2 扫地机地图 |

## 13 色调色板（已应用于每个房间）

```yaml
PALETTE = {
    "客厅":   "#FF6B35",  # 活力橙
    "餐厅":   "#FF922B",  # 橘黄
    "主卧":   "#6366F1",  # 紫蓝
    "儿童房": "#EC4899",  # 粉
    "父母房": "#22C55E",  # 绿
    "书房":   "#0EA5E9",  # 天蓝
    "衣帽间": "#A855F7",  # 紫
    "玄关":   "#6B7280",  # 灰
    "走廊":   "#78716C",  # 暖灰
    "阳台":   "#22C55E",  # 绿（合并阳台）
    "全屋空调": "#3B82F6",  # 蓝
    "浴室":   "#6366F1",  # 紫蓝
    "摄像头": "#EF4444",  # 红
}
```

## 场景脚本（影院模式）

> 文件 `/config/scripts/dian_ying_yuan.yaml`

```yaml
dian_ying_yuan:
  alias: 影院模式
  sequence:
    - service: light.turn_off
      target:
        entity_id: [客厅主灯组, 吊灯, 壁灯, 灯带, 轨道灯]
    - service: cover.close_cover
      target:
        entity_id: [cover.ke_ting_chuang_lian, cover.ke_ting_chuang_sha]
    - service: switch.turn_on
      target:
        entity_id: switch.ji_jia_cha_pai_p2_bei_jing_deng
    - service: light.turn_on
      target:
        entity_id: light.ke_ting_bi_deng_deng_dai_right
      data:
        brightness_pct: 20
        rgb_color: [255, 100, 50]
```

## HA 已有统计实体（直接用，不用新建）

| 实体 | 用途 | 在仪表板引用 |
|------|------|-------------|
| `sensor.kai_deng_shu_liang` | 实时开灯数 | 显示"X 灯开" |
| `sensor.iphone_battery_level` | iPhone 电量 | 个人卡片 |
| `sensor.electricity_meter_*_da_zong_gong_lu` | 总功率 | 能耗监控 |
| `sensor.electricity_maps_co2_intensity` | 碳强度 | 环保仪表 |
| `sensor.sun_next_setting` | 日落时间 | 自动化条件 |

## 用户实际反馈（下一步建议）

1. 影院场景尚未提供所有 script YAML（仅给了骨架），需要逐一补全
2. 夜间模式（深色 popup 背景）尚未实现
3. 天气/日历/清扫卡片未集成到首屏
4. 自动化"人在家自动开灯"（配合 FP310 传感器）待做

## 相关页面

- `~/ha-wiki/solutions/lovelace-minimalist-bubble-card.md` — 完整 32.5KB 方案文档（可粘即用）
- `~/ha-wiki/scan_rooms.py` — 房间归类扫描（生成此方案时使用）
- `~/ha-wiki/ha-rooms.json` — 9 房间 + 设备清单 dump
