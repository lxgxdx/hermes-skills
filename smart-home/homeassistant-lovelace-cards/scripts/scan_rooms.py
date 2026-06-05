#!/usr/bin/env python3
"""
扫描 HA 实体，按拼音前缀归类到房间，过滤掉 zigbee 元数据。
输出：可读的文本报告 + JSON dump（供后续生成 dashboard YAML）。

用法：
    HASS_TOKEN=xxx python3 scan_rooms.py
    # 或先 source ~/.hermes/.env，再 python3 scan_rooms.py
"""
import json, urllib.request, os, sys

# ============================================================
# 配置
# ============================================================

# 房间拼音前缀 → 显示名（按你的 entity_id 实际命名调整）
ROOM_MAP = {
    "ke_ting": "客厅", "can_ting": "餐厅",
    "zhu_wo": "主卧", "er_tong_fang": "儿童房",
    "fu_mu_fang": "父母房", "shu_fang": "书房",
    "yi_mao_jian": "衣帽间", "xuan_guan": "玄关",
    "zou_lang": "走廊", "bei_yang_tai": "北阳台",
    "zhu_yang_tai": "主阳台", "qdhkl": "全屋空调",
    "yeelink": "浴室", "chuangmi": "客厅",
    "mrbond": "主阳台", "m5stack": "客厅",
    "leshi": "书房", "aqara": "玄关",
    "shi_tou": "扫地机", "g20s": "扫地机",
    "qian_zhi": "洗衣机", "dahua": "大华",
    "zigbee2mqtt": "Z2M", "zgw1bbc": "Z2M",
}

# 跳过 zigbee 元数据后缀（这些不是主控实体）
SKIP_SUFFIX = (
    "_power_outage_memory", "_flip_indicator_light", "_led_disabled_night",
    "_single_target", "_bluetooth", "_vertical_swing", "_alarm", "_blow",
    "_heating", "_ventilation", "_child_lock", "_status_indicator_light",
    "_dnd_switch", "_valley_electricity_switch", "_zone_enable",
    "_zout1_enable", "_illuminance_fast_update",
    "_ai_interference_source_selfidentification", "_ai_sensitivity_adaptive",
    "_uv", "_switch_status",
)

# 跳过这些子串的实体
SKIP_KEYWORDS = [
    "_use_listen_light", "dahua_", "frigate_card", "frigate_server",
    "_zigbee_permit", "_zigbee2mqtt_", "permit_join", "0x", "32c3",
    "electricity_meter_", "qdhkl_ac_", "electricity-meter",
    "keting_detect", "keting_motion", "keting_recordings", "keting_snapshots",
    "keting_review", "keting_audio", "keting_ptz", "keting_3",
    "apple_tv", "d14feb", "0e949f", "screen",
    "qbittorrent", "auto_focus", "wiper", "ir_lamp",
    "indicator_light",
]

EMOJI = {
    "light": "💡", "cover": "🪟", "climate": "❄️",
    "switch": "🔌", "sensor": "🔋", "binary_sensor": "👤",
    "vacuum": "🤖", "media_player": "🎵",
}

# ============================================================
# HA API
# ============================================================

def get_token():
    """从 ~/.hermes/.env 读 HASS_TOKEN；或从环境变量"""
    token = os.environ.get("HASS_TOKEN")
    if token:
        return token
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("HASS_TOKEN="):
                    return line.split("=", 1)[1].strip()
    print("ERROR: 请先 source ~/.hermes/.env 或设 HASS_TOKEN", file=sys.stderr)
    sys.exit(1)

def api(path, token, base="http://192.168.88.183:8123"):
    req = urllib.request.Request(
        f"{base}{path}",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# ============================================================
# 核心逻辑
# ============================================================

def room_of(eid):
    """根据 entity_id 拼音前缀判断房间"""
    base = eid.split(".", 1)[1]
    parts = base.split("_")
    for i in range(min(3, len(parts))):
        p = "_".join(parts[:i+1])
        if p in ROOM_MAP:
            return ROOM_MAP[p]
    return "其他"

def is_meta(eid):
    """是否 zigbee 元数据（要跳过）"""
    base = eid.split(".", 1)[1].lower()
    if any(base.endswith(s) for s in SKIP_SUFFIX):
        return True
    if any(k in base for k in SKIP_KEYWORDS):
        return True
    return False

def scan(token):
    states = api("/api/states", token)
    by_room = {}
    for s in states:
        eid = s["entity_id"]
        if is_meta(eid):
            continue
        dom = eid.split(".")[0]
        if dom not in EMOJI:
            continue
        room = room_of(eid)
        by_room.setdefault(room, {}).setdefault(dom, []).append({
            "eid": eid,
            "name": s.get("attributes", {}).get("friendly_name", eid),
            "state": s["state"],
        })
    return by_room

# ============================================================
# 输出
# ============================================================

def print_report(by_room):
    for room in sorted(by_room.keys()):
        g = by_room[room]
        total = sum(len(v) for v in g.values())
        if total == 0:
            continue
        print(f"\n===== {room} ({total}) =====")
        for dom in ("light", "cover", "climate", "switch",
                    "binary_sensor", "media_player", "vacuum", "sensor"):
            if dom in g:
                print(f"  {EMOJI[dom]} {dom} ({len(g[dom])}):")
                for x in g[dom][:15]:
                    print(f"     {x['eid']:62s} {x['name']} [{x['state'][:15]}]")

def dump_json(by_room, path="/tmp/ha-rooms.json"):
    out = {}
    for room, cats in by_room.items():
        out[room] = {}
        for dom, items in cats.items():
            out[room][dom] = [{"eid": x["eid"], "name": x["name"]} for x in items]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n\nDUMPED → {path} ({len(out)} rooms)")

# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    token = get_token()
    by_room = scan(token)
    print_report(by_room)
    dump_json(by_room)
