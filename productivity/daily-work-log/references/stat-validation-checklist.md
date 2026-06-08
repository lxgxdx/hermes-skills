# Cron 汇报 stat 验证 checklist（2026-06-08 起强制执行）

> 起源：2026-06-08 全 cron 日 12 session 中，02:00 经验类选题 cron（`59f917bbc534`）asst last 看似完整（4 本地选题 + 4 外地借鉴 + 收尾冒号），但 `ls -la /mnt/nfs/.../经验类选题_20260608.md` 报"没有那个文件或目录"，整段会话 0 个 write_file 调用才暴露。这是 §11c 第五种截断模式的首次发现。
>
> 推广：自 6/8 起，daily-work-log 必须对**所有** cron session 汇报的关键文件做**无差别** stat 验证（不再"怀疑时"才做），不论该 session 是否像成功幻觉 / 半截过渡句 / SILENT。

## 验证范围（按 cron session 类别）

| Cron session | 必须 stat 验证的文件 | 不验证的 |
|--------------|----------------------|----------|
| `tongzhan-info-workflow` | `/mnt/nfs/2026年统战工作/8.信息工作/选题库/问题类选题_YYYYMMDD.md` 和 `经验类选题_YYYYMMDD.md` | - |
| `tongzhan-wiki-build` | `~/wiki/entities/policy-*.md`（全部）和 `~/wiki/comparisons/*.md`（如存在） | `~/wiki/index.md` / `~/wiki/log.md`（这些永远存在） |
| `user-profile-curation` | `~/.hermes/memories/USER.md` 和 `~/.hermes/memories/user_model_report_YYYYMMDD.md` | `USER.md.bak.vN_*`（备份文件，stat 出大小即可确认） |
| `llm-wiki-build` (PVE) | `~/pve-wiki/concepts/{proxmox-ve-install,gpu-passthrough,frigate-on-pve,pve-network-storage}.md`（4 文件清单） | - |
| `dream-cycle` | `~/.hermes/skills/productivity/gbrain-ops/references/dream-cycle-YYYY-MM-DD.md` | - |
| `skills sync` | git commit + remote push（`git log -1` + `git status`） | - |
| `hermes-backup` | `/mnt/hermes/hermes_backup_YYYYMMDD_HHMMSS.tar.gz` 大小 > 1GB | - |
| `frigate-wiki-updater` | （仅信 TG 通知，不 stat） | - |
| `home-assistant-ops` | （只读 HA，无文件产出；只检查是否 SILENT） | - |
| `check-wechat-issue` | （只查 GitHub，无文件产出；只检查是否 SILENT） | - |
| `daily-work-log` | `~/.hermes/memories/daily/YYYY-MM-DD.md` 落库后 | - |

## 标准验证脚本片段（每日复用）

```bash
# 全 cron 日典型 stat 验证套件（按需删减）
echo "=== 选题 ==="
ls -la "/mnt/nfs/2026年统战工作/8.信息工作/选题库/问题类选题_$(date -d yesterday +%Y%m%d).md" 2>&1
ls -la "/mnt/nfs/2026年统战工作/8.信息工作/选题库/经验类选题_$(date -d yesterday +%Y%m%d).md" 2>&1

echo "=== Wiki ==="
ls -la ~/wiki/entities/policy-*.md 2>&1 | tail -5
ls -la ~/wiki/comparisons/ 2>&1
ls -la ~/pve-wiki/concepts/ 2>&1

echo "=== USER.md ==="
ls -la ~/.hermes/memories/USER.md 2>&1
ls -la ~/.hermes/memories/user_model_report_$(date -d yesterday +%Y%m%d).md 2>&1

echo "=== 备份 ==="
ls -la /mnt/hermes/hermes_backup_$(date -d yesterday +%Y%m%d)_*.tar.gz 2>&1

echo "=== Dream cycle reference ==="
ls -la ~/.hermes/skills/productivity/gbrain-ops/references/dream-cycle-$(date -d yesterday +%Y-%m-%d).md 2>&1
```

## 验证结果判读

- **文件存在 + 大小 > 1KB** → ✅ 真完成
- **文件不存在** → ❌ §5b 成功幻觉 / §11b 半截过渡句 / §11c 完整规划-未落盘 三选一（看 asst last 形态）
- **文件存在但 < 200B** → ⚠️ 可能是占位 / 空文件，需 cat 验证内容
- **文件大小与 asst last 汇报不一致**（如汇报 26.6KB 实际 1KB）→ ⚠️ 写入失败或被截断

## §11c 完整规划-未落盘识别速查

asst last 包含以下任一信号 + `write_file=0` + stat 验证文件不存在 = §11c：

1. 列出具体内容项编号（`1. xxx` / `2. xxx` / `3. xxx` / `4. xxx`）
2. 收尾冒号（`现在生成今日选题文件:` / `即将创建...:`）
3. 用将来时（"现在生成" / "即将生成" / "马上写"）而非完成时（"已生成" / "已写入"）
4. 整段从未出现"已完成" / "✅" / "落盘" 等汇报完成信号

## 跨日应用记录

- 2026-06-08：12 cron session 全 stat 验证，戳穿 1 个 §11c（02:00 经验类），验证 11 个真完成（含 §5b 历史 PVE wiki 4 文件、§5c 历史 USER.md v8 18.4KB）
- 2026-06-09+：每日 cron 必跑，预期 §11c 仍会出现（信息稿 cron 时间窗结构性不足未解决）
