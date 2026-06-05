# Cron 写入验证 — 防"成功幻觉"模式

> **场景**：cron 任务里 agent 汇报"已创建 N 个文件"或"已完成 4 个页面"，但实际 `ls` / `stat` 显示文件不存在，或 size = 0KB。这是 cron 任务的**高发 failure pattern**，已多次复现。
>
> **真实案例（2026-06-05 PVE Wiki cron）**：
> - cron session `cron_0abf80bf4d_20260606_020012` 最后一条 asst 汇报：
>   > "PVE Wiki 构建完成，已创建 4 个核心页面：`proxmox-ve-install.md` / `gpu-passthrough.md` / `frigate-on-pve.md` / `pve-network-storage.md`"
> - 实际上 `ls ~/wiki/concepts/` 下这 4 个文件**全部不存在**
> - GBrain 搜索"Proxmox VE 安装 / GPU 直通 / Frigate PVE"也搜不到
> - **汇报与现实完全脱节**
>
> **真实案例（2026-06-05 问题类选题 cron）**：
> - cron session `cron_68a578b26b6c_20260605_010021` 48 msgs，最后一条 asst 长度为 0 chars
> - 应输出的 `问题类选题_20260605.md` **未生成**
> - 但 agent 在 asst[10] 已完成"5 个选题组合策略"，asst[14] 已确认排重
> - 离成功只差最后一步 write_file，但 last asst 突然变空 → **任务中断，未落地**

---

## 根因分析

cron 任务里 agent "成功幻觉" 的 4 种典型路径：

| # | 路径 | 触发条件 |
|---|------|----------|
| 1 | **write_file 之前的 asst 误判** | agent 在最后一轮 asst 写了"已完成报告"作为总结，但 write_file 实际未执行或被中断（context 满 / 工具 quota 用完 / 网络错误） |
| 2 | **write_file 路径错误** | agent 写到了相对路径 `~/wiki/...` 但实际 cwd 不是 home，文件落到了错误目录 |
| 3 | **write_file 内容为空** | agent 调用了 write_file 但 content 是空字符串（典型：模型把"已完成"当成"已写入"） |
| 4 | **write_file 之后被 rollback** | 落盘成功但后续 cleanup / git reset 误操作 / 容器重启丢失 |

---

## 防御策略（三层）

### 第一层：write_file 后立即 stat 验证

任何"创建文件 / 写报告 / 落库"的 cron 任务，**write_file 之后必须立即 stat**：

```python
# ✅ 标准收尾模式
import os
target = '/home/lxgxdx/wiki/concepts/proxmox-ve-install.md'
size = os.path.getsize(target) if os.path.exists(target) else 0
assert size > 1024, f"❌ {target} 未落地或 size={size} < 1KB"
print(f"✅ {target} = $size B")
```

### 第二层：批量任务用循环 + 报告

```python
# 写 4 个 PVE Wiki 页面时的标准模式
created = []
for name, content in [
    ('proxmox-ve-install.md', pve_install_md),
    ('gpu-passthrough.md', gpu_md),
    ('frigate-on-pve.md', frigate_pve_md),
    ('pve-network-storage.md', pve_net_md),
]:
    path = f'/home/lxgxdx/wiki/concepts/{name}'
    write_file(path, content)
    if os.path.getsize(path) > 1024:
        created.append(name)
    else:
        print(f"❌ {name} 写盘失败")
print(f"✅ 实际创建 {len(created)}/4: {created}")
```

### 第三层：cron 任务汇报里必须带"stat 证据"

最后一轮 asst 汇报**必须**包含：

```markdown
# ✅ 任务完成报告

**实际产出**（stat 验证后）：
- `~/wiki/entities/policy-x.md` (15,266 B)
- `~/wiki/entities/policy-y.md` (12,103 B)
- `~/wiki/raw/x-summary.md` (2,553 B)

**未落地/失败**（如有）：
- ⚠️ `~/wiki/concepts/proxmox-ve-install.md` 写入失败（write_file 后 stat = 0）
```

**不要**写："已创建 4 个核心页面" — 这种汇报在 cron 模式下几乎一定是幻觉。

---

## 已知受影响的 Skill

凡是 cron 任务里涉及 write_file 的 skill 都需要这个防御：

| Skill | cron 任务名 | 现状 |
|-------|-----------|------|
| `productivity/tongzhan-wiki-policy-builder` | 01:30 cron | ⚠️ 缺少 stat 验证 |
| `productivity/llm-wiki-build` | 02:00 cron | ⚠️ 缺少 stat 验证（PVE Wiki 案例） |
| `productivity/tongzhan-info-workflow` | 01:00 cron | ⚠️ 缺少 stat 验证（问题类选题中断案例） |
| `productivity/daily-work-log` | 00:00 cron | ✅ 已有"asst last 0 chars"检测 |
| `productivity/user-profile-curation` | 02:00 cron | ✅ 已有 3 文件 + GBrain stats 验证 |

---

## 自动化检测脚本

`scripts/verify-cron-writes.sh` —— 可被任意 cron skill 调用的验证脚本：

```bash
#!/bin/bash
# 验证指定路径列表中每个文件存在且 size > 1KB
# Usage: verify-cron-writes.sh <path1> <path2> ...
# Exit 0 = all pass, 1 = at least one missing or empty

THRESHOLD=1024
FAILED=()
for path in "$@"; do
    if [ ! -f "$path" ]; then
        FAILED+=("$path (missing)")
        continue
    fi
    SIZE=$(stat -c%s "$path" 2>/dev/null || stat -f%z "$path" 2>/dev/null)
    if [ "$SIZE" -lt "$THRESHOLD" ]; then
        FAILED+=("$path ($SIZE B < $THRESHOLD)")
    else
        echo "✅ $path = $SIZE B"
    fi
done

if [ ${#FAILED[@]} -gt 0 ]; then
    echo "❌ FAILED: ${FAILED[@]}"
    exit 1
fi
echo "✅ All ${#@} files pass"
```

---

## 长期修复路径（已提议但未落地）

> 见 `user-profile-curation` v5/v6 "待用户决策" 第 9 项：
> "cron '成功幻觉' 防护 — 是否在 tongzhan-wiki-policy-builder skill 加 `stat > 1KB` 强制校验"

建议把所有 cron 写盘 skill 的最后一步统一改成：

```bash
bash ~/.hermes/skills/productivity/user-profile-curation/scripts/verify-cron-writes.sh \
    ~/wiki/entities/policy-1.md \
    ~/wiki/entities/policy-2.md \
    ~/wiki/concepts/pve-page-1.md
```

如果脚本 exit 1，cron 任务必须输出 `[SILENT]` 之外的实际失败报告（不要假装成功）。

---

## 历史失败记录

| 日期 | skill | 失败模式 | agent 汇报 | 实际 |
|------|-------|---------|-----------|------|
| 2026-06-05 | llm-wiki-build (PVE) | 4 页面未真实写入 | "已创建 4 个核心页面" | 文件均不存在 |
| 2026-06-05 | tongzhan-info-workflow (问题类) | write_file 之前中断 | asst last 0 chars | `问题类选题_20260605.md` 未生成 |
| 2026-06-03 | dream-cycle (累计统计) | 读了 log.md 累计行 | "Wiki 14 个新页面" | 实际只新增 1 个 |

*更新日期：2026-06-06 / 触发会话：cron_2f03227164de_20260606_020040 (user-profile-curation v6)*
