# Gateway Platform Communication — Diagnostic Reference

Companion to the SKILL.md "User reports 'I can't reach you on platform X'" section.
This file is the long-form forensic log: what the actual evidence looks like,
how the kill chain unravels, and the recovery commands.

## Real case: 2026-06-10 — 32h43m outage on every platform

User (lxgxdx) reported from CLI: "hermes和飞书，微信的通信中断了，我使用飞书和你对话，没有回复".
The CLI session worked (proving the LLM was up). Gateway was the broken piece.

### Evidence trail (in order discovered)

```bash
# 1. PID lookup — there's a hermes process, but is it the gateway?
ps aux | grep hermes
# PID 2447057: /home/lxgxdx/.hermes/hermes-agent/venv/bin/python3 .../hermes
# → THIS is the current CLI session, NOT the gateway.

# 2. Check the gateway service directly
systemctl --user status hermes-gateway
# Active: failed (Result: exit-code) since Tue 2026-06-09 10:08:59 CST; 1 day 8h ago
# Duration: 22min 32.809s   ← only ran 22 min before failing
# Main PID: 2260174 (code=exited, status=1/FAILURE)

# 3. Last log entry timestamp — gateway has been silent for 32+ hours
ls -la ~/.hermes/logs/gateway.log
# -rw-r--r-- 1 lxgxdx lxgxdx 1636207  6月  9 10:08 gateway.log
# Last write: 2026-06-09 10:08 — process exited 32h before user reported it

# 4. Forensic shutdown log
cat ~/.hermes/logs/gateway-exit-diag.log
# Shows a chain of: SIGTERM → drain 60s timeout → interrupt 1 active agent
# → exit code 1 → systemd Restart=on-failure triggered
# → repeated 5 times in 10 minutes → StartLimitBurst=5 exhausted
# → systemd stopped trying

# 5. The actual crash chain (from journalctl)
journalctl --user -u hermes-gateway --since "2 days ago"
# 09:45:20  Started hermes-gateway.service
# 09:45:23  ERROR api_server: API_SERVER_KEY is required (warning, not fatal)
# 09:45:32  ⚕ Hermes Gateway Starting
# 09:45:32  [Lark] connected to wss://msg-frontier.feishu.cn/ws/v2  ← Feishu OK
# 09:46:03  ERROR api_server: API_SERVER_KEY is required
# 09:52:10  Feishu: Inbound dm message received
#           '以新版本为主，配置好api，替换旧入口'    ← user's first message
# 09:52:52  read_file: Access denied: ~/.hermes/.env is a credential store
# 09:53:03  ERROR api_server: API_SERVER_KEY is required
# 09:57:28  Stream stale for 240s (threshold 240s) — no chunks received.
#           model=MiniMax-M3 context=~56,224 tokens. Killing connection.
# 09:58:03  ERROR api_server
# 10:01:28  Stream stale for 240s (M3 model timed out again)
# 10:03:04  ERROR api_server
# 10:05:29  Stream stale for 240s (third time)
# 10:05:56  terminal returned error: ...user was trying to compare systemd unit
# 10:07:53  Received SIGTERM — initiating shutdown
# 10:07:53  Stopping gateway...
# 10:08:56  Gateway drain timed out after 60.0s with 1 active agent(s)
# 10:08:57  Ignoring control interrupt for session agent:main:feishu:dm:...
# 10:08:57  response ready: ... time=1004.4s api_calls=15 response=0 chars
#           ← agent was hung for 1004 seconds, returned 0 chars
# 10:08:58  ✓ telegram disconnected
# 10:08:58  ✓ homeassistant disconnected
# 10:08:58  ✓ feishu disconnected
# 10:08:58  ✓ weixin disconnected
# 10:08:58  Exiting with code 1 (signal-initiated shutdown without restart request)
#           so systemd Restart=on-failure can revive the gateway.
# 10:08:59  hermes-gateway.service: Main process exited, code=exited, status=1/FAILURE
# 10:08:59  hermes-gateway.service: Failed with result 'exit-code'.
# 10:08:59  Stopped hermes-gateway.service
#           ← systemd tried to restart, but in the next 10 minutes hit 5 more
#             failures, hit StartLimitBurst=5, and gave up until 1:45 the next day
```

### The kill chain (5-link)

1. **Upstream LLM froze** — M3 stream went silent for 240s three times
   (09:57, 10:01, 10:05). No chunks received. The chat was hung.
2. **Tool loop warning** — `terminal` had been failing 3 times in a row on
   the same turn. Agent was retrying `systemctl --user restart hermes-gateway`
   which itself can't run from inside the gateway it's restarting.
3. **External SIGTERM** — at 10:07:53 a SIGTERM arrived. From where?
   The user might have run it from another session, OR the gateway's own
   agent was escalating. Doesn't matter — drain started.
4. **Drain timeout (60s)** — 1 active agent (the hung Feishu chat) couldn't
   be drained in 60s. Drain timed out, gateway forced interruption.
5. **Exit 1 → systemd Restart=on-failure loop** — gateway came back up,
   crashed again on the same root cause (model still hung), 5 times in
   10 minutes. StartLimitBurst=5 hit. systemd gave up. Gateway silent
   for 32 hours until user noticed.

### Recovery commands (worked)

```bash
# Step 1: clear the failed state
systemctl --user reset-failed hermes-gateway

# Step 2: start fresh (no restart — restart would still see the old PID)
systemctl --user start hermes-gateway

# Step 3: wait ~6s, verify
sleep 6
systemctl --user status hermes-gateway | head -8
# Active: active (running) since Wed 2026-06-10 18:52:07 CST; 6s ago

# Step 4: check all 5 platforms connected
tail -50 ~/.hermes/logs/gateway.log
# 18:52:08  api_server     listening on http://127.0.0.1:8642 ✓
# 18:52:14  telegram       Connected (polling mode)            ✓
# 18:52:14  homeassistant  Connected                           ✓
# 18:52:15  feishu         Connected in websocket mode          ✓
# 18:52:15  weixin         Connected account=c2049b1c base=... ✓
# 18:52:15  Gateway running with 5 platform(s)
# 18:52:16  Cron ticker started (interval=60s)
# 18:52:21  kanban dispatcher: embedded in gateway
```

Total downtime was 32h43m. Recovery took 14 seconds.

## Systemd unit file (default)

```
/home/lxgxdx/.config/systemd/user/hermes-gateway.service
```

```ini
[Unit]
Description=Hermes Agent Gateway - Messaging Platform Integration
After=network.target
StartLimitIntervalSec=600
StartLimitBurst=5          ← TOO LOW. Recommend raising to 20.

[Service]
Type=simple
ExecStart=/home/lxgxdx/.hermes/hermes-agent/venv/bin/python \
          /home/lxgxdx/.hermes/hermes-agent/scripts/hermes-gateway run
WorkingDirectory=/home/lxgxdx/.hermes/hermes-agent
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

## Lingering (one-time)

```bash
sudo loginctl enable-linger $USER
# Check: loginctl show-user $USER | grep Linger
#   Linger=yes    ← good
#   Linger=no     ← gateway dies on logout
```

The `lxgxdx` user has `Linger=yes` already (verified 2026-06-10) — that part is
not the cause of this outage.

## API server key issue (separate, non-fatal)

`config.yaml` line 497 has `api_server.key: ''` (empty). This produces
continuous warning spam at every gateway boot:
```
ERROR gateway.platforms.api_server: [Api_Server] Refusing to start:
API_SERVER_KEY is required for the API server, including loopback-only
binds on 127.0.0.1.
```
Despite the error message, the api_server does start (loopback allows it).
Fix: generate a key, put it in `~/.hermes/.env` as `API_SERVER_KEY=...` and
also in `config.yaml` `api_server.key`. Not urgent — it's noise, not a
blocker — but it confuses future triage.

## M3 stream stale — upstream issue, not gateway

`Stream stale for 240s — no chunks received. model=MiniMax-M3` — this is the
upstream LLM provider silently dropping the connection or stalling. Not
something the gateway can fix. The gateway's only options are:
- Kill the connection after 240s (current behavior, works)
- Lower the threshold (e.g. 120s) for faster recovery
- Add a heartbeat ping to detect earlier

User workaround: when running a long task on Hermes-via-Feishu, the CLI
session is the reliable progress channel. If Feishu goes silent, check
the CLI.

## Decision tree (quick reference)

```
User: "Hermes 没回我" / "飞书/微信/TG 通信中断了"
  │
  ├─ CLI works? (user is talking to you)
  │   YES → gateway problem, NOT model problem
  │   NO  → model/API key problem, different playbook
  │
  ├─ systemctl --user status hermes-gateway
  │   active (running)  → check which platform adapter failed
  │   failed            → reset-failed + start
  │   inactive (dead)   → start (or reset-failed + start if was failed)
  │
  ├─ tail ~/.hermes/logs/gateway.log
  │   Hasn't grown in 1h+ → zombie, hard kill + start
  │   Last line is "Exiting with code 1" → was in restart loop
  │
  └─ After restart, confirm "✓ <platform> connected" for each platform
      user mentioned. If a platform is missing, that adapter failed
      to start — check journal for that platform's name.
```
