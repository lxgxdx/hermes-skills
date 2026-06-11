# HA Supervisor API & Add-on 调试参考

> 本节从 lxgxdx/ha-ai-designer Add-on 调试事故（2026-06-11）沉淀。
> 适用：HA OS / HA Supervised 上部署第三方 / 自建 Add-on 时遇到
> "装不上" / "打不开 web" / "容器反复重启" 类问题。

---

## 1. 鉴权模型（最容易踩的坑）

HA 有**两套 API、两套 token**：

| API | 路径前缀 | 鉴权 | Token 来源 |
|---|---|---|---|
| HA Core API | `/api/` | Bearer long-lived token | HA UI → 用户头像 → 长期访问令牌 |
| **Supervisor API** | `/api/hassio/` | Bearer long-lived token（必须 admin / hassio scope） | 同上，但**用户必须在 admin 组** |
| Supervisor 内部 | `http://supervisor/core` | `SUPERVISOR_TOKEN` 环境变量 | Add-on 容器内自动注入 |

**`~/.hermes/.env` 里的 HASS_TOKEN 是 Core API 的**，**不能直接调 `/api/hassio/*`**。首次 401 时就是这个原因。

获取 Supervisor scope token：
- 路径：HA UI → 头像 → 我的账户（最下面"长期访问令牌"）→ 创建
- **重要**：创建该 token 的用户必须**是 admin 组**（HA 默认第一个用户是 admin）
- 命名建议：`hassio-debug` 之类的标识，方便日后撤销

测试 token 是否够格：
```bash
curl -sS -H "Authorization: Bearer *** "http://192.168.88.183:8123/api/hassio/addons" | head -c 200
# 期待: 一段 JSON 数组，而不是 401
```

---

## 2. 诊断 Add-on 状态

### 2.1 列表 / 详情

```bash
SUP=*** admin long-lived token>"
BASE=192.168.88.183:8123

# 列出所有已装 Add-on
curl -sS -H "Authorization: Bearer *** "http://$BASE/api/hassio/addons" \
  | python3 -c "import sys,json;[print(a['slug'], a.get('state'), a.get('installed'), a.get('available')) for a in json.load(sys.stdin)['addons']]"

# 单个 Add-on 详情（包含网络、ingress URL、health）
curl -sS -H "Authorization: Bearer *** "http://$BASE/api/hassio/addon/<slug>/info" \
  | python3 -m json.tool
```

### 2.2 日志

```bash
# 最近日志
curl -sS -H "Authorization: Bearer *** "http://$BASE/api/hassio/addon/<slug>/logs"
```

日志里重点看：

- `bashio::` 开头的行 → 配置/选项解析错误
- `legacy-services stopping` / `legacy-services stopped` → **s6 重启循环**
- `EACCESS` / `ENOENT` → 路径权限/挂载问题
- `Cannot find image` / `pull access denied` → 镜像拉取失败（见 §3.1）

### 2.3 Ingress 入口

`config.yaml: ingress: true` 时：

| 入口 | URL | 说明 |
|---|---|---|
| 侧边栏图标 | （自动出现） | 最稳，HA 自动反代 |
| 显式 URL | `/api/hassio/ingress/<slug>/` | 等价于侧边栏，CLI/脚本测试用 |
| 直接 host 端口 | `http://<ha_ip>:<port>` | **不通**——`ports: <port>/tcp: null` 表示不映射 |

测试 ingress：
```bash
curl -sS -H "Authorization: Bearer *** "http://$BASE/api/hassio/ingress/<slug>/" | head -c 300
# 期待：HTML 头（<html>...）或 200 + 非空 body
# 404 = ingress 未注册；502 = 容器内部服务没起；401 = token 问题
```

---

## 3. 装不上 / 容器不启动：三大根因

### 3.1 GHCR 镜像私有（最常见，~60%）

**症状**：Add-on Store 显示已添加仓库，但装时直接失败；或在 "Rebuild" 时报 `pull access denied` / `unauthorized`。

**原因**：GHCR（`ghcr.io`）package 默认私有，HA 装 Add-on 走**匿名 pull**，私有包直接 401。

**诊断**（最快 5 秒）：
```bash
# 把 <owner>/<image> 替换成仓库的 slug
curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
  "https://ghcr.io/v2/<owner>/<image>/manifests/latest"
# 200 = 公开 ✅
# 401 authentication required = 私有 ❌
```

**修复**（手动，**GitHub API 不支持改 visibility**）：
1. 打开 https://github.com/users/<owner>/packages/container/<image>/settings
2. 滚到底部 **Danger Zone** → **Change package visibility** → **Public** → 确认
3. HA 端：在 Add-on 页面 → ⋮ → **Rebuild**（重新拉镜像）

**CI 自动化建议**：CI push 完镜像后，仓库的 `CLAUDE.md` / `README.md` 应该写明"维护者必须**手动**改 public"——别浪费时间在 CI 里尝试 PATCH（API 不支持）。

### 3.2 s6 重启循环（~30%）

**症状**：Add-on 状态在 "Starting" / "Stopped" 间反复横跳；日志里看到：
```
[s6-init] ensuring user-provided files have correct perms...
[cont-init.d] executing container initialization scripts...
[cont-finish.d] executing container finish scripts...
[s6-finish] syncing disks.
[s6-finish] sending all processes the TERM signal.
[s6-finish] sending all processes the KILL signal and exiting...
[s6-init] making user provided files available at /var/run/s6/etc...: exited 0.
[s6-init] ensuring user-provided files have correct perms...: exited 0.
[cont-init.d] done.
[services.d] starting services
[services.d] starting services: exited 0.
[cmd] exited 1
[legacy-services] stopping legacy services
[legacy-services] stopped
```

**根因**：`run.sh` 用了：
- `set -e`（任一命令失败 → 整个脚本退出 → s6 报"未运行"）
- `nohup ... &`（进程脱离 s6 进程组，s6 看不到 pid）
- `bashio::config` 取不到选项时直接 exit

**修复模式**：把 daemon / web 拆成**独立的 s6 service**：

```
/etc/s6-overlay/s6-rc.d/
├── daemon/
│   ├── run          # `node /opt/.../daemon/dist/server.js`
│   └── type         # `longrun`
├── web/
│   ├── run          # `next start`
│   └── type         # `longrun`
└── user/contents.d/   # 软链接启动 daemon + web
```

`run.sh` 只做初始化（读 bashio 选项、生成 config.json、设权限），不再 `nohup`。

如果不想大改，**最小修复**：去掉 `set -e`、给 `bashio::config` 加默认值、nohup 后 `disown` 或写 pid 到 s6 期望的位置。

### 3.3 Ingress 路径/端口错（~10%）

**症状**：容器明明跑起来了（`stats` 报 running），但浏览器打不开。

**诊断**：
- `config.yaml: ports` 段写了 `3000/tcp: null`？→ 正常，**不要**直接访问 host:3000
- `config.yaml: ingress: true`？→ 用侧边栏入口或 `/api/hassio/ingress/<slug>/`
- `ingress_port` 选项的值（如 3000）必须和 Add-on 内部 web 进程监听的端口一致

---

## 4. 信息源速查

- HA 官方 Add-on 文档：https://developers.home-assistant.io/docs/add-ons/
- Supervisor API 端点参考：https://developers.home-assistant.io/docs/api/supervisor/endpoints
- GHCR package visibility 限制：https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility
- s6-overlay 多服务模式：https://github.com/just-containers/s6-overlay (建议改成 s6-rc)
