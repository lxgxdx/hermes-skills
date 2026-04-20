---
name: obsidian-webdav-sync
description: Set up WebDAV server for Obsidian mobile sync on Linux/Unraid. Supports anonymous or authenticated access, multiple wiki directories, and iOS/Android Obsidian integration.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [obsidian, webdav, sync, mobile, productivity, wiki]
    related_skills: [webdav-server-setup, llm-wiki]
---

# Obsidian WebDAV Sync Setup

Set up a WebDAV server to sync LLM Wiki knowledge bases with Obsidian mobile app. This enables viewing and editing wiki files on iOS/Android Obsidian via WebDAV protocol.

## Prerequisites

- Python 3.10+
- Obsidian mobile app installed on phone
- Wiki directories already created (e.g., `~/wiki`, `~/klipper-wiki`)

## Installation

```bash
# Install wsgidav
python3 -m venv ~/.hermes/webdav-venv
~/.hermes/webdav-venv/bin/pip install wsgidav cheroot
```

## Configuration Options

### Option 1: Simple Anonymous Access (Recommended for LAN)

```bash
# Start server with anonymous access
~/.hermes/webdav-venv/bin/wsgidav \
  --port=8080 \
  --host=0.0.0.0 \
  --root=/home/lxgxdx/wiki \
  --auth=anonymous \
  --browse \
  -v
```

### Option 2: Multiple Directories with Authentication

Create config file `~/.hermes/webdav.yaml`:
```yaml
host: 0.0.0.0
port: 8080

provider_mapping:
  "/wiki": /home/lxgxdx/wiki
  "/klipper-wiki": /home/lxgxdx/klipper-wiki

simple_dc:
  user_mapping:
    "*": true  # Allow anonymous access

http_authenticator:
  enable: false

verbose: 1
```

Start server:
```bash
~/.hermes/webdav-venv/bin/wsgidav -c ~/.hermes/webdav.yaml
```

### Option 3: With Authentication

For authenticated access (recommended if exposed to internet):
```yaml
host: 0.0.0.0
port: 8080

provider_mapping:
  "/wiki": /home/lxgxdx/wiki

simple_dc:
  user_mapping:
    "*":
      accept: true
      credentials:
        - user: hermes
          password: hermes123

verbose: 1
```

## Starting the Server

### One-time Start
```bash
nohup ~/.hermes/webdav-venv/bin/wsgidav \
  --port=8080 \
  --host=0.0.0.0 \
  --root=/home/lxgxdx/wiki \
  --auth=anonymous \
  --browse \
  -v > /tmp/webdav.log 2>&1 &
```

### Systemd Service (Auto-start on boot)
Create `~/.config/systemd/user/webdav.service`:
```ini
[Unit]
Description=Hermes WebDAV Server
After=network.target

[Service]
Type=simple
User=lxgxdx
ExecStart=/home/lxgxdx/.hermes/webdav-venv/bin/wsgidav --port=8080 --host=0.0.0.0 --root=/home/lxgxdx/wiki --auth=anonymous --browse -v
Restart=on-failure
RestartSec=5
StandardOutput=append:/tmp/webdav.log
StandardError=append:/tmp/webdav.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl --user daemon-reload
systemctl --user enable webdav
systemctl --user start webdav
```

## Testing

Check if server is running:
```bash
# Get local IP
hostname -I | awk '{print $1}'

# Test access (anonymous)
curl -s http://192.168.88.213:8080/

# Test with authentication
curl -s -u hermes:hermes123 http://192.168.88.213:8080/
```

## Obsidian Mobile Configuration

### iOS/Android Setup
1. Open Obsidian → Settings → Sync
2. Select **WebDAV**
3. Configure:
   - **Folder**: Local folder name (e.g., `hermes-wiki`)
   - **WebDAV URL**: `http://192.168.88.213:8080/`
   - **Username**: (leave empty for anonymous)
   - **Password**: (leave empty for anonymous)

### Multiple Wikis Setup
Since Obsidian can only sync one vault at a time via WebDAV:

1. **Option A**: Create separate Obsidian vaults for each wiki
   - Vault 1: `http://192.168.88.213:8080/wiki`
   - Vault 2: `http://192.168.88.213:8080/klipper-wiki`

2. **Option B**: Run separate WebDAV servers on different ports
   ```bash
   # Wiki 1 on port 8080
   ~/.hermes/webdav-venv/bin/wsgidav --port=8080 --root=/home/lxgxdx/wiki --auth=anonymous
   
   # Wiki 2 on port 8081  
   ~/.hermes/webdav-venv/bin/wsgidav --port=8081 --root=/home/lxgxdx/klipper-wiki --auth=anonymous
   ```

## Troubleshooting

### Common Issues

1. **401 Access not authorized**
   - Check authentication configuration
   - Try `--auth=anonymous` flag
   - Ensure `simple_dc.user_mapping["*"]: true` in config

2. **Server not starting**
   - Check if port is already in use: `netstat -tlnp | grep :8080`
   - Ensure cheroot is installed: `pip install cheroot`

3. **Obsidian connection fails**
   - Verify server is accessible from phone's network
   - Check firewall rules: `sudo ufw allow 8080/tcp`
   - Try accessing URL in phone's browser first

4. **Multiple directory configuration fails**
   - wsgidav command-line only supports single `--root`
   - Use config file with `provider_mapping` for multiple directories

### Logs
```bash
# View server logs
tail -f /tmp/webdav.log

# Check process status
ps aux | grep wsgidav
```

## Security Considerations

1. **LAN-only**: Use anonymous access only on trusted local networks
2. **Authentication**: Enable auth if exposing to internet
3. **HTTPS**: Consider reverse proxy with SSL for external access
4. **Firewall**: Restrict access to local network IPs only

## Performance Notes

- wsgidav is lightweight, uses minimal resources
- Supports concurrent connections for multiple devices
- File transfers are efficient for Markdown files
- Consider memory usage for very large wikis (>10,000 files)

## Integration with LLM Wiki

This setup works with LLM Wiki knowledge bases:
- `~/wiki` - AI/ML knowledge base
- `~/klipper-wiki` - 3D printer knowledge base
- Any other Markdown-based wiki structure

Files remain in standard Obsidian format with `[[wikilinks]]` and can be edited on mobile, then synced back to server.