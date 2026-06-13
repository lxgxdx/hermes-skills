---
name: home-assistant
description: Class-level guide to working with Home Assistant from Hermes — read-only operations boundary, REST API discovery, Lovelace card ecosystem (Bubble Card, Button Card, Mini Graph Card, Jinja2 templates), HACS plugin enumeration, Supervisor API / add-on debugging, and dashboard design patterns. Load when querying HA state, building Lovelace dashboards, debugging HACS cards, or troubleshooting add-on installs.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [home-assistant, ha, lovelace, bubble-card, button-card, hacs, jinja2, supervisor, read-only, smart-home, iot]
    related_skills: [openhue]
---

# Home Assistant — Class-Level Guide

This umbrella covers the read-only side of Home Assistant: querying state, discovering what's installed, building Lovelace dashboards, and debugging add-ons. It does NOT cover writing — by design.

> **Hard rule: read-only boundary.** This skill (and all its reference sections) enforces a strict no-write policy. No `turn_on`, `turn_off`, `toggle`, no service calls that mutate state, no `configuration.yaml` edits, no automation triggers. If a user asks for a write operation, decline and suggest the `openhue` skill (for direct Hue CLI control) or the HA UI directly.

## Sections

1. [Read-Only Operations & Safety Boundary](references/read-only-ops.md) — the original `home-assistant-ops` skill. The canonical read-only rule, API method reference, Add-on debugging (Supervisor API, GHCR private images, s6 restart loops, Ingress paths), and the current device inventory.
2. [API Discovery Patterns](references/api-discovery.md) — the original `homeassistant-discovery` skill. How to enumerate installed HACS cards via `update.*` entities, domain distribution, config/version discovery, and the fallback when `lovelace/config` returns 404.
3. [Lovelace Cards & Jinja2 Templates](references/lovelace-cards.md) — the original `homeassistant-lovelace-cards` skill. The full card ecosystem (Bubble, Button, Mini Graph, Bar, Plotly, Floor3D, Search, Card Mod, etc.) with examples, Jinja2 template reference, the 5-section dashboard layout, the 13-color palette, the 5 Bubble Card Popup gotchas, and the room-grouping algorithm.
4. [Supervisor API Reference](references/hassio-supervisor-api.md) — `/api/hassio/*` endpoint details, the HASS_TOKEN vs Supervisor token distinction, and add-on lifecycle.
5. [Dashboard Design Patterns](references/dashboard-design-patterns.md) — 4 design schools (Bubble minimalism, 3D digital twin, mixed, classic) with full YAML examples.
6. [Lovelace 设备速查 + Wiki index](references/lovelace-cards.md#相关资源) — the HA Wiki at `~/ha-wiki/` with Jinja2, Lovelace cards, automations, and entity lists.

## When to Load This Umbrella

- Querying HA state via REST API or `ha_*` MCP tools
- Discovering what's installed (cards, integrations, entities)
- Building a new Lovelace dashboard
- Debugging an add-on that won't start (GHCR private image, s6 loop, Ingress path)
- Reviewing or extending a Lovelace configuration
- Asking "what entities does HA have for X" or "what's the state of Y"

## Scripts

- `scripts/check-ha-addon.sh` — quick diagnostic for "add-on won't install / start" cases (Supervisor API, log grep, image visibility check).
- `scripts/scan_rooms.py` — scan all `entity_id`s and group by 拼音-prefix room (客厅/餐厅/主卧/etc.). Returns a per-room entity count.

## Templates

- `templates/dashboard-skeleton.yaml` — blank 5-section dashboard skeleton (场景栏 + 9 房间 grid + 全屋 + 环境条 + 搜索).
- `templates/bubble-popup-template.yaml` — minimal-working Bubble Card popup (single room).

## Hard Rule: Read-Only

**This entire umbrella is read-only by design.** No write operations, no service calls, no configuration edits. The user's HA is on `http://192.168.88.183:8123` and Hermes accesses it via `ha_*` MCP tools (which expose the read API only).

If the user wants to control devices:
- **Hue lights** → use the `openhue` skill (separate CLI, write-enabled)
- **Other devices** → suggest the HA UI directly, or `curl` with explicit user consent for one-off service calls

The hard boundary exists because the agent's job is information-gathering and analysis, not home automation. Write operations should be explicit, deliberate, and human-initiated.

## The HASS_TOKEN vs Supervisor Token Gotcha

The most common pitfall: the `HASS_TOKEN` in `~/.hermes/.env` is a **HA Core long-lived token** (user scope). It does NOT work for `/api/hassio/*` (Supervisor API) calls, which need a **hassio/admin-scope** token. Symptoms:

- Using `HASS_TOKEN` against `/api/hassio/addons` → `401 Unauthorized`
- Solution: create a separate Supervisor token via HA UI → User Avatar → Long-Lived Access Tokens, with the user being an admin

See `references/hassio-supervisor-api.md` for the full Supervisor API reference and the 3 most common add-on install failure modes (GHCR private ~60%, s6 restart loop ~30%, Ingress path wrong ~10%).

## When to Use Related Skills

- **`openhue`** — write-enabled CLI for Hue lights (the only write-enabled smart-home skill in the library). Use when the user wants to actually change lights, scenes, or brightness.
- **HA Wiki (`~/ha-wiki/`)** — the user's external Wiki with 19 pages of HA-specific notes (Jinja2, Lovelace, automations, entity lists). This umbrella cross-references but does not duplicate it.

## Related Skills

- `openhue` — Hue lights CLI (write-enabled, the one exception to the read-only rule for the smart-home category)
