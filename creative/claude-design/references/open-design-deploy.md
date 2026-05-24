# Open Design Deployment Reference

## TL;DR — What Works

**For Hermes support: must run natively (not Docker).** Docker containers are Node-only and cannot run Hermes (Python CLI).

| Method | Hermes Support | Port | Status |
|--------|---------------|------|--------|
| Docker `vanjayak/open-design:latest` | ❌ | :7456 | Works but Hermes not detected |
| Native `pnpm tools-dev run web` | ✅ | :7456 (daemon) + :3000 (web) | **Recommended** |

## Native Deployment (Hermes-capable)

### Prerequisites

```bash
# Node 24 required — install via n
which n || npm install -g n
n 24
export PATH=$HOME/.n/bin:$PATH
node --version  # should print v24.x
```

### Clone and Install

```bash
git clone https://github.com/nexu-io/open-design.git /tmp/open-design
cd /tmp/open-design
corepack enable
pnpm install   # ~2 min
```

### Increase inotify Limit (Linux)

Turbopack needs more watches than default 65536:

```bash
echo 524288 | sudo tee /proc/sys/fs/inotify/max_user_watches
```

### Start Services

Daemon (port 7457) and Web (port 3000):

```bash
cd /tmp/open-design
export PATH=$HOME/.n/bin:$PATH
export OD_DATA_DIR=/tmp/open-design/.od

# Terminal 1: Daemon
node ./apps/daemon/dist/cli.js --no-open &
# Wait for: [od] daemon listening on http://127.0.0.1:7456

# Terminal 2: Web (or run in background)
OD_DAEMON_URL=http://127.0.0.1:7457 pnpm --filter @open-design/web dev --port 3000 &
```

Or use `tools-dev` to orchestrate:

```bash
OD_DATA_DIR=/tmp/open-design/.od OD_DAEMON_URL=http://127.0.0.1:7457 pnpm tools-dev run web
# Web: http://localhost:3000  |  Daemon: http://localhost:7457
```

### Verify Hermes Detection

```bash
curl -s http://127.0.0.1:7457/api/agents | grep '"id":"hermes"'
# Should show: "available":true, "version":"Hermes Agent v..."
# And model list includes your configured models (e.g. MiniMax-M2.7-highspeed)
```

### Access

- **Web UI:** http://localhost:3000 (or http://192.168.88.213:3000 for LAN)
- **Daemon API:** http://127.0.0.1:7457

## Docker Deployment (No Hermes)

If Hermes is not needed, Docker is simpler:

```bash
docker run -d --name open-design \
  -p 7456:7456 \
  -v open_design_data:/app/.od \
  -e NODE_ENV=production \
  -e OD_BIND_HOST=0.0.0.0 \
  -e OD_PORT=7456 \
  --restart always \
  --memory=384m \
  vanjayak/open-design:latest

# Access: http://127.0.0.1:7456
```

Note: Docker container is Node-only. Hermes binary (Python) cannot run inside it.

## Hermes Detection Details

Open Design detects Hermes by running `hermes --version` and parsing stdout. Requirements:

- `hermes` must be on PATH
- `hermes --version` must exit 0 with non-empty stdout
- Version string is parsed for display in the agent picker

Hermes uses `acp-json-rpc` stream format — the same ACP protocol Hermes uses for its own subagent communication.

## Fixing Common Issues

### Turbopack "OS file watch limit reached"

Increase inotify watches:
```bash
echo 524288 | sudo tee /proc/sys/fs/inotify/max_user_watches
```

### Node version too low

Open Design requires Node 24. Install:
```bash
npm install -g n
n 24
export PATH=$HOME/.n/bin:$PATH
```

### Snap Docker permission denied

On systems with Snap Docker, use:
```bash
sudo docker <command>
```
Or add user to docker group and re-login.

### Port already in use

Use different ports:
```bash
OD_PORT=7457 OD_WEB_PORT=3000 node ./apps/daemon/dist/cli.js --no-open
```

## Architecture

```
Browser (Next.js 16 on :3000)
    ↓ HTTP/SSE
Daemon (Express + SQLite on :7457)
    ↓ spawn CLI
Hermes / Claude Code / OpenCode / ... (on PATH)
```

The daemon scans PATH for agent binaries, runs version probes, fetches model lists via each agent's native protocol, then presents a unified picker UI.

## What Open Design Adds Over claude-design Skill

| Capability | claude-design skill | Open Design |
|------------|---------------------|-------------|
| Interactive skill picker | ❌ | ✅ |
| 149+ design systems | ❌ | ✅ |
| Sandboxed iframe preview | ❌ | ✅ |
| Magazine PPT decks (guizang-ppt) | ❌ | ✅ |
| BYOK proxy for any LLM API | ❌ | ✅ |
| Project persistence (SQLite) | ❌ | ✅ |
| Image/video generation integration | ❌ | ✅ |

Use claude-design for quick one-off HTML artifacts generated directly in the current repo. Use Open Design for structured design sessions with brand-grade design systems, skill workflows, and sandboxed previews.
