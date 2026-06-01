#!/usr/bin/env bash
# Dream Cycle Wiki→Brain Bridge (2026-06-02)
# Finds recently-modified wiki entity pages not yet in gbrain vector DB
# and imports them via the safe `gbrain import` method.
#
# Usage:  ./dream-cycle-wiki-bridge.sh [--days N] [--dry-run]
#         ./dream-cycle-wiki-bridge.sh           # default: last 2 days
#         ./dream-cycle-wiki-bridge.sh --days 7  # look back 7 days
#
# Re-runnable: gbrain import is idempotent (skips already-imported pages).

set -euo pipefail

DAYS=2
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --days) DAYS="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Env setup (cron-safe)
export HOME=/home/lxgxdx
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

WIKI_DIR="$HOME/wiki/entities"
STAGING_DIR="/tmp/gbrain-dream-$(date +%F)"
DATE_STAMP=$(date +%F)

echo "=== Dream Cycle Wiki→Brain Bridge ==="
echo "Date: $DATE_STAMP"
echo "Looking back: $DAYS day(s)"
echo "Wiki dir:   $WIKI_DIR"
echo

# 1. List all wiki entity pages modified in the last N days
mapfile -t RECENT_PAGES < <(find "$WIKI_DIR" -maxdepth 1 -name "*.md" -mtime "-$DAYS" 2>/dev/null)
echo "Recently-modified wiki pages: ${#RECENT_PAGES[@]}"
for p in "${RECENT_PAGES[@]}"; do echo "  - $(basename "$p")"; done
echo

# 2. Get gbrain slug list (one slug per line)
echo "Fetching gbrain slug list..."
GBRAIN_SLUGS=$(cd "$HOME/brain" && ~/.bun/bin/bun run "$HOME/gbrain/src/cli.ts" list --limit 500 2>/dev/null | cut -f1)
echo

# 3. For each recent wiki page, check if it's already in gbrain
MISSING=()
for page in "${RECENT_PAGES[@]}"; do
  base=$(basename "$page" .md)
  # gbrain list slugs use the pattern: entities/<base>/page
  if echo "$GBRAIN_SLUGS" | grep -q "entities/$base/page$"; then
    echo "  ✓ already in gbrain: $base"
  else
    echo "  ✗ MISSING from gbrain: $base"
    MISSING+=("$base")
  fi
done
echo

if [[ ${#MISSING[@]} -eq 0 ]]; then
  echo "No new wiki pages to bridge. Done."
  exit 0
fi

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[DRY RUN] Would import ${#MISSING[@]} page(s):"
  printf '  - %s\n' "${MISSING[@]}"
  exit 0
fi

# 4. Stage pages and import
echo "Staging ${#MISSING[@]} page(s) for import..."
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

for base in "${MISSING[@]}"; do
  src="$WIKI_DIR/$base.md"
  dst="$STAGING_DIR/entities/$base/page.md"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  echo "  staged: entities/$base/page.md"
done

echo
echo "Importing via gbrain..."
cd "$HOME/brain" && ~/.bun/bin/bun run "$HOME/gbrain/src/cli.ts" import "$STAGING_DIR"

echo
echo "Verifying with gbrain stats..."
~/.bun/bin/bun run "$HOME/gbrain/src/cli.ts" stats

echo
echo "=== Bridge complete ==="
