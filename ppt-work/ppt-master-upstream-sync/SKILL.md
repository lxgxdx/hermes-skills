---
name: ppt-master-upstream-sync
description: >
  ppt-master 官方仓库同步与本地化纪律。当用户问"ppt-master 有更新吗"、
  "看一下 ppt-master 仓"、或需要确认本地工作树是否干净、是否落后官方时加载。
  包含：upstream URL / 本地路径 / 最近关键 commit / 严禁的本地化行为
  / 同步检查流程 / 关键运行参数。
---

# ppt-master 官方仓库同步与本地化纪律

> **铁律（2026-06-02 lxgxdx 明确）**：一切以官方为准，不打补丁。
> 用户原话："之前做的一直不好才会跟你强调，但是目前我觉得这个官方的skill已经做的很好了"。

## 触发场景

加载本 skill 当用户：
- 问"ppt-master 有更新吗" / "看一下 ppt-master 仓"
- 让你跑 `git status` / `git pull` / `git fetch` 在 ppt-master 目录
- 提到本地"ppt-master-usage"等历史 wrapper skill
- 让你判断"以官方为准"还是"打补丁"

## 关键速查

| 项目 | 值 |
|------|-----|
| 官方 upstream | https://github.com/hugohe3/ppt-master.git |
| 本地路径 | `~/.hermes/skills/ppt-work/ppt-master-repo/` |
| 当前 HEAD（截至 2026-06-02） | `eda1bd8` (2026-04-15) |
| 远端 origin | `https://github.com/hugohe3/ppt-master.git` |

## 严禁的本地化行为（来自本次复盘）

1. **不创建 `ppt-master-usage` 这类个人 skill** — 官方 SKILL.md 已经包含完整内容，会导致重复 `skill_view` 9 次
2. **不修改官方 SKILL.md / references/ 里的内容** — 用户偏好应通过 Strategist 八大确认流程表达（写到项目级 `design_spec.md`），而不是改 skill 源文件
3. **不创建 `references/lxgxdx-quickref.md` 这类未跟踪文件** — 仓内残留 = `git status` 长期显示。真正想留的偏好写到 `~/.hermes/memories/USER.md` 或项目级 `design_spec.md`

## 同步检查流程

```bash
cd ~/.hermes/skills/ppt-work/ppt-master-repo
git fetch origin
git log HEAD..origin/main --oneline   # 落后检查
git status --short                    # 工作树干净检查
```

## 关键运行参数（官方硬性要求）

| 参数 | 必用 | 禁用 |
|------|------|------|
| 导出 PPTX | `-s final`（从 `svg_final/`） | `-s svg_output`（旧版已废） |
| 后处理 | 三步分开跑 | 合并成一行 `&&` |
| 后处理入口 | `finalize_svg.py` | `cp` |
| 导出标志 | 不加 `--only` | 加 `--only` |

## 详细内容

详见 `references/upstream-sync-discipline.md`（最近 commit 详解 / 含图 DOCX 处理 / 反面案例）。
