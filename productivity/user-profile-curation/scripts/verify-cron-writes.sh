#!/bin/bash
# verify-cron-writes.sh
# 验证指定路径列表中每个文件存在且 size > 1KB
# 用于 cron 任务的"防成功幻觉"防御
#
# Usage: verify-cron-writes.sh <path1> <path2> ...
# Exit 0 = all pass, 1 = at least one missing or empty
#
# 适用场景：所有写盘的 cron skill
#   - tongzhan-wiki-policy-builder
#   - llm-wiki-build
#   - tongzhan-info-workflow
#   - daily-work-log
#   - user-profile-curation
#   - meeting-minutes-generator
#   - 任何未来涉及 write_file 的 cron 任务
#
# 推荐用法（写在 cron skill 的最后一步）：
#   bash ~/.hermes/skills/productivity/user-profile-curation/scripts/verify-cron-writes.sh \
#       ~/wiki/entities/policy-1.md \
#       ~/wiki/entities/policy-2.md

set -e
THRESHOLD=${THRESHOLD:-1024}
FAILED=()
PASSED=()

for path in "$@"; do
    if [ ! -f "$path" ]; then
        FAILED+=("MISSING: $path")
        continue
    fi
    # 跨平台 stat（Linux / macOS）
    SIZE=$(stat -c%s "$path" 2>/dev/null || stat -f%z "$path" 2>/dev/null)
    if [ -z "$SIZE" ] || [ "$SIZE" -lt "$THRESHOLD" ]; then
        FAILED+=("TOO_SMALL: $path ($SIZE B < $THRESHOLD)")
    else
        echo "✅ $path = $SIZE B"
        PASSED+=("$path")
    fi
done

echo ""
echo "=== 验证结果 ==="
echo "通过: ${#PASSED[@]} 个"
echo "失败: ${#FAILED[@]} 个"
for f in "${FAILED[@]}"; do
    echo "  ❌ $f"
done

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "❌ Cron 任务存在'成功幻觉'风险 — 文件未真实落地"
    echo "   建议：手动检查 write_file 调用 + cron 环境"
    exit 1
fi

echo "✅ All ${#PASSED[@]} files passed (>= $THRESHOLD B)"
exit 0
