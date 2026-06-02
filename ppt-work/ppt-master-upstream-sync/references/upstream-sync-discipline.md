# ppt-master 官方仓库同步与本地化纪律（详情）

> 配套主 SKILL.md 的详细参考资料。包含：upstream 信息、最近 4 个关键 commit 详解、
> 同步检查流程、含图 DOCX 处理、反面案例。

## 1. 仓库基本信息

| 项目 | 值 |
|------|-----|
| 官方 upstream | https://github.com/hugohe3/ppt-master.git |
| 本地路径 | `~/.hermes/skills/ppt-work/ppt-master-repo/` |
| 当前 HEAD（截至 2026-06-02） | `eda1bd8` (2026-04-15) |
| 远端 origin | `https://github.com/hugohe3/ppt-master.git` |
| 分支跟踪 | main |

## 2. 最近 4 个关键 commit 详解

### 2.1 `8f85fee feat(web_to_md): use curl_cffi for TLS-fingerprint impersonation`
- **影响**：以前爬不动微信公众号等高防护站点，现在用 `curl_cffi` 模拟真实浏览器 TLS 指纹
- **触发条件**：用户提供微信公众号、知乎等高安全站 URL
- **判断脚本选择**：直接用 `web_to_md.py` 即可（已内置 curl_cffi）；老 `web_to_md.cjs` Node 兜底只在 `curl_cffi` 未装时启动

### 2.2 `a40d68e feat(doc_to_md): native Python paths for docx/html/epub/ipynb`
- **影响**：DOCX/HTML/EPUB/IPYNB 不再走 pandoc，原生 Python 路径更快更稳
- **支持的格式扩展**：`.docx` `.html` `.epub` `.ipynb` 原生；`.doc` `.odt` `.rtf` `.tex` `.rst` `.org` `.typ` 走 pandoc 兜底
- **新增**：`scripts/source_to_md/excel_to_md.py`（.xlsx/.xlsm 转换）

### 2.3 `b1e901c docs(skill): clarify template vs free design framing in Step 3`
- **行为变化**：Step 3 模板选择**默认走自由设计**，不再问用户 A/B
- **触发模板的 3 个明确信号**（必须命中其一才走模板分支）：
  1. 用户直接说"用 mckinsey 模板" / "use the academic_defense template" — 命名了具体模板
  2. 用户引用风格名（"McKinsey 那种" / "Google style" / "学术答辩样式"）— 风格品牌映射
  3. 用户主动问"有哪些模板可以用"
- **软提示（非阻塞）**：内容明显匹配某模板时给一句话提示，但不阻塞
- **判断要点**：没命中以上 3 个触发词时，**直接走 Step 4 不要问**

### 2.4 `eda1bd8 docs(readme_cn): remove stray empty table header in prerequisites`
- 文档微调，不影响行为

## 3. 严禁行为（来自本次复盘）

### 3.1 不创建 `ppt-master-usage` 这类个人 skill
- 历史：曾创建过个人速查 wrapper skill，但**官方 SKILL.md 已经包含完整内容**
- 后果：导致重复 `skill_view`（用户反馈"调用后 9 次重复 skill_view，不记住流程"）

### 3.2 不修改官方 SKILL.md / references/ 里的内容
- 历史：曾给 `executor-general.md` 加过 `USER STYLE REQUIREMENTS` 整段、给 `strategist.md` 加过 `lxgxdx 配色例外` 段
- **为什么错**：用户偏好应通过 Strategist 八大确认流程表达（`design_spec.md` 是用户和 AI 的契约文件），而不是改 skill 源文件
- **后果**：本地工作树污染、`git status` 长期显示 modified、`git pull` 拉官方更新时必然冲突
- **正确做法**：用户偏好写到项目级 `design_spec.md` / `spec_lock.md`，不污染 skill 源

### 3.3 不创建 `references/lxgxdx-quickref.md` 这类未跟踪文件
- 仓内残留未跟踪文件 = 以后 `git status` 一直显示
- 真正想留的偏好应写到 `~/.hermes/memories/USER.md` 或项目级 `design_spec.md`

## 4. 同步检查流程

### 4.1 检查是否落后官方
```bash
cd ~/.hermes/skills/ppt-work/ppt-master-repo
git fetch origin
git log HEAD..origin/main --oneline
```
- 输出空 = 已同步
- 有新 commit = 看 commit message 判断是否要 pull（一般**接受官方改动**）

### 4.2 检查本地是否有未提交修改
```bash
git status --short
```
- 输出空 = 工作树干净
- 有 modified / untracked = 检查是否必要；按 §3 原则**默认应该丢弃**

### 4.3 还原本地污染
```bash
# 还原 3 个常被污染的官方文件
git checkout -- skills/ppt-master/SKILL.md
git checkout -- skills/ppt-master/references/executor-general.md
git checkout -- skills/ppt-master/references/strategist.md

# 删除任何 untracked 的本地 wrapper 文件
rm skills/ppt-master/references/lxgxdx-quickref.md
```

## 5. 关键运行参数（官方 SKILL.md 里的硬性要求）

| 参数 | 必用 | 禁用 |
|------|------|------|
| 导出 PPTX | `-s final`（从 `svg_final/` 导出） | `-s svg_output`（旧版已废） |
| 后处理 | `total_md_split.py` → `finalize_svg.py` → `svg_to_pptx.py` 三步**分开跑** | 合并成一行 `&&` |
| 后处理入口 | `finalize_svg.py` | `cp` |
| 导出标志 | 不加 `--only` | 加 `--only`（会少一个输出文件） |

## 6. 含图 DOCX 来源材料处理（与官方一致）

用户提供含图片的 DOCX 培训教材时：
1. `doc_to_md.py` 转 MD
2. **手动**复制 `word/media/*.{png,jpg,jpeg,webp}` 到 `<project>/images/`
3. `analyze_images.py <project>/images` 让 AI 描述每张图
4. Strategist 在 `design_spec.md` 的"图片资源清单"段列清楚
5. Executor 生成时按 `image_prompts.md` / `image_sources.json` 引用

(避免依赖 `doc_to_md` 自动提取漏图)

## 7. 反面案例（不该再犯的）

| 时间 | 错误 | 正确做法 |
|------|------|---------|
| 2026 早期 | 创建 `ppt-master-usage` skill，导致重复 skill_view | 不创建个人 wrapper |
| 2026 早期 | 给官方 SKILL.md 加 USER STYLE REQUIREMENTS 段 | 用户偏好写到 design_spec.md |
| 2026 早期 | 给 references/ 加 `lxgxdx-quickref.md` | 写到 `~/.hermes/memories/USER.md` |
| 2026 早期 | 导出时用 `-s svg_output` | 用 `-s final` |

---

*本文件由 lxgxdx 2026-06-02 复盘后建立。后续如发现更多同步/污染问题，追加到本文件。*
