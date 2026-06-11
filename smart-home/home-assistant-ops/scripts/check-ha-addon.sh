#!/usr/bin/env bash
# ==============================================================================
# check-ha-addon.sh — HA Add-on 装不上 / 打不开 web 的快速诊断
# ==============================================================================
# 用法:
#   ./check-ha-addon.sh <github_owner> <image_name> [addon_slug]
#
# 例:
#   ./check-ha-addon.sh lxgxdx ha-ai-designer ha_ai_designer
#
# 检查项:
#   1) GHCR 镜像是否公开（匿名 pull）  ← 60% 装不上的根因
#   2) HA Supervisor API 是否可达
#   3) Add-on 是否已注册
#   4) Add-on 容器是否 running
#   5) Ingress 路径是否返回 HTML
#
# 不做写操作，纯只读。
# ==============================================================================

set -u

OWNER="${1:-}"
IMAGE="${2:-}"
SLUG="${3:-}"
HA_URL="${HA_URL:-http://192.168.88.183:8123}"

# 优先用 SUPERVISOR_TOKEN（admin scope），其次用 HASS_TOKEN
TOKEN=*** SUPERVISOR_TOKEN*** "*** "***HASS_TOKEN***" "*** "*** HOMERMS/.env" 2>/dev/null

if [ -z "$OWNER" ] || [ -z "$IMAGE" ]; then
  echo "用法: $0 <github_owner> <image_name> [addon_slug]"
  echo "  例: $0 lxgxdx ha-ai-designer ha_ai_designer"
  exit 1
fi

if [ -z "$TOKEN" ]; then
  echo "❌ 找不到 token。需 SUPERVISOR_TOKEN 或 HASS_TOKEN 环境变量，或 ~/.hermes/.env"
  echo "   注意: HASS_TOKEN 是 Core API 的，/api/hassio/* 需要 admin scope token"
  exit 1
fi

AUTHORIZATION=*** Bearer ***"

green() { printf "\033[32m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*"; }
yel()   { printf "\033[33m%s\033[0m\n" "$*"; }
bold()  { printf "\033[1m%s\033[0m\n" "$*"; }

bold "=== HA Add-on 快速诊断 ==="
echo "HA:        $HA_URL"
echo "Owner:     $OWNER"
echo "Image:     $IMAGE"
[ -n "$SLUG" ] && echo "Slug:      $SLUG"
echo ""

# 1) GHCR 镜像公开性
bold "[1] GHCR 镜像可见性（匿名 pull）"
GHCR_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" \
  "https://ghcr.io/v2/${OWNER}/${IMAGE}/manifests/latest" \
  -H "Accept: application/vnd.docker.distribution.manifest.v2+json")
case "$GHCR_HTTP" in
  200) green "  ✅ ghcr.io/${OWNER}/${IMAGE} 公开 OK" ;;
  401) red   "  ❌ ghcr.io/${OWNER}/${IMAGE} 私有（401）" 
       echo "     → 修复: https://github.com/users/${OWNER}/packages/container/${IMAGE}/settings"
       echo "            → Danger Zone → Change package visibility → Public" ;;
  404) red   "  ❌ 镜像不存在（404）。检查 owner/image 名是否正确，或 CI 是否真把镜像推上去" ;;
  *)  red   "  ⚠️  HTTP $GHCR_HTTP（未知状态）" ;;
esac
echo ""

# 2) Supervisor API 可达性
bold "[2] Supervisor API 可达性"
SUP_HTTP=$(curl -sS -o /dev/null -w "%{http_code}" -H "$AUTHORIZATION" \
  "${HA_URL}/api/hassio/addons")
case "$SUP_HTTP" in
  200) green "  ✅ /api/hassio/addons 200 OK（token 有效）" ;;
  401) red   "  ❌ 401 Unauthorized。HASS_TOKEN 不能调 Supervisor API"
       echo "     → 修复: HA UI → 头像 → 长期访问令牌 → 创建（用户必须 admin 组）"
       echo "            然后 SUPERVISOR_TOKEN=<新token> $0 $@" ;;
  *)  red   "  ⚠️  HTTP $SUP_HTTP" ;;
esac
echo ""

# 3) Add-on 注册情况
bold "[3] Add-on 注册情况"
ADDONS=$(curl -sS -H "$AUTHORIZATION" "${HA_URL}/api/hassio/addons")
if echo "$ADDONS" | python3 -c "import json,sys;d=json.load(sys.stdin);exit(0 if d.get('addons') is not None else 1)" 2>/dev/null; then
  if [ -n "$SLUG" ]; then
    STATE=$(echo "$ADDONS" | python3 -c "
import json,sys
try:
  d=json.load(sys.stdin)
  for a in d.get('addons',[]):
    if a['slug']=='$SLUG':
      print(f\"installed={a.get('installed')}  state={a.get('state')}  version={a.get('version')}\")
      break
  else:
    print('NOT_FOUND')
except Exception as e:
  print(f'PARSE_ERR:{e}')
")
    if [ "$STATE" = "NOT_FOUND" ]; then
      red "  ❌ $SLUG 未在已装 Add-on 列表里"
      echo "     → HA UI → Settings → Add-ons → Add-on Store → ⋮ → Repositories"
      echo "            添加 https://github.com/${OWNER}/ha-ai-designer 后刷新"
    else
      green "  ✅ $SLUG: $STATE"
    fi
  else
    echo "$ADDONS" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for a in d.get('addons',[])[:20]:
  print(f\"  {a.get('slug'):35s}  installed={a.get('installed')}  state={a.get('state')}\")
"
  fi
else
  red "  ❌ 返回不是合法 JSON: $ADDONS"
fi
echo ""

# 4) Add-on 容器状态
if [ -n "$SLUG" ]; then
  bold "[4] Add-on 容器状态"
  INFO=$(curl -sS -H "$AUTHORIZATION" "${HA_URL}/api/hassio/addon/${SLUG}/info")
  if echo "$INFO" | python3 -c "import json,sys;d=json.load(sys.stdin);exit(0 if 'state' in d else 1)" 2>/dev/null; then
    RUNNING=$(echo "$INFO" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('state','unknown'))")
    case "$RUNNING" in
      started) green "  ✅ 状态: started" ;;
      stopped) red   "  ❌ 状态: stopped（容器没起来）"
                echo "     → HA UI → Add-on 详情 → Log 标签看启动报错"
                echo "     → 常见: bashio::config 失败、nohup 进程脱离 s6 进程组" ;;
      starting) yel "  ⏳ 状态: starting（首次启动或刚 Rebuild，等 30-60s）" ;;
      *)        yel "  ⚠️  状态: $RUNNING" ;;
    fi
  else
    red "  ❌ 拿不到 $SLUG info（可能未安装）"
  fi
  echo ""

  # 5) Ingress 路径
  bold "[5] Ingress 路径"
  ING_HTTP=$(curl -sS -o /tmp/ingress_body.html -w "%{http_code}" -H "$AUTHORIZATION" \
    "${HA_URL}/api/hassio/ingress/${SLUG}/")
  ING_SIZE=$(wc -c < /tmp/ingress_body.html)
  case "$ING_HTTP" in
    200) green "  ✅ /api/hassio/ingress/${SLUG}/ 200 OK（body $ING_SIZE bytes）"
         echo "     → 浏览器打开: ${HA_URL}/api/hassio/ingress/${SLUG}/"
         echo "     → 或 HA 侧边栏找 Add-on 入口" ;;
    404) red   "  ❌ 404: ingress 未注册（config.yaml 里 ingress: true 才有此路径）" ;;
    502) red   "  ❌ 502: 容器内部服务没起（daemon/web 进程崩了）" ;;
    401) red   "  ❌ 401: token 失效" ;;
    *)  red   "  ⚠️  HTTP $ING_HTTP (body $ING_SIZE bytes)" ;;
  esac
  echo ""
fi

bold "=== 诊断完成 ==="
echo "三大常见根因速查:"
echo "  1) GHCR 镜像私有（~60%）：看 [1]"
echo "  2) s6 重启循环（~30%）：  看 [4] + HA Add-on Log 标签"
echo "  3) Ingress 路径错（~10%）：看 [5]"
echo ""
echo "详细诊断方法见 ~/ha-wiki/ 下的 references/hassio-supervisor-api.md"
