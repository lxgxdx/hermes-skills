---
name: ppt-master-usage
description: >
  Use ppt-master to generate natively-editable PPTX presentations from diverse input materials (PDF/DOCX/Markdown/text/URLs). Covers project initialization, SVG-based AI generation pipeline, post-processing, and export. Ideal for professional slide decks, reports, pitch decks, and educational materials that need polished, editable output.
  Use this skill whenever the user's request involves creating, generating, or assembling a PowerPoint/Keynote presentation, slide deck, or PPTX file — especially when they provide reference materials like PDFs, documents, or outlines.
  Not applicable: pure text-to-PPTX without visual structure (use simpler tools), editing existing PPTX templates manually, or non-presentation document generation.
tags: ["ppt", "powerpoint", "automation", "presentation", "slide-deck"]
category: productivity
---

# PPT Master — AI Presentation Engineer

> 官方 Skill（`ppt-master`）是核心工作流。本 skill 是包装指南，包含路径、快捷命令和设计原则。

---

## ⚡ QuickRef（必须记住，每次都用）

**路径：**
- `SKILL_DIR=~/.hermes/skills/ppt-work/ppt-master-repo/skills/ppt-master`
- `PROJECT_DIR=~/ppt-master/projects`
- ⚠️ 旧路径 `~/ppt-master/skills/ppt-master` 已废弃

**完整七步流程（必须按顺序执行，不得并行或跳步）：**

所有命令**必须** `cd ~/ppt-master` 后执行。

```bash
# Step 1: 内容转换（如有PDF/DOCX/Excel）
python "${SKILL_DIR}/scripts/source_to_md/pdf_to_md.py" <file>
python "${SKILL_DIR}/scripts/source_to_md/doc_to_md.py" <file>
python "${SKILL_DIR}/scripts/source_to_md/excel_to_md.py" <file>

# Step 2: 初始化项目
python "${SKILL_DIR}/scripts/project_manager.py" init <项目名> --format ppt169

# Step 3: 导入源文件
python "${SKILL_DIR}/scripts/project_manager.py" import-sources <项目路径> <源文件...> --move
```

⚠️ **import-sources 对含大量图片的DOCX转换会失败**（如演讲稿75MB含24张照片）：
- 手动解压DOCX的 `word/media/` 目录下所有图片到项目 `images/` 目录：
```python
import zipfile, os
with zipfile.ZipFile('xxx.docx', 'r') as z:
    for name in z.namelist():
        if name.startswith('word/media/') and not name.endswith('/'):
            fname = os.path.basename(name)
            with open(f'<项目>/images/{fname}', 'wb') as f:
                f.write(z.read(name))
```

# Step 4: ⛔ BLOCKING — Strategist Phase（八项确认）
向用户展示完整策划方案，等待明确确认后才能继续。
八项确认：a.画布尺寸 b.页面数量 c.受众定位 d.风格定位
　　　　　e.配色方案 f.图标方案 g.字体方案 h.图片方案

⚠️ **演讲稿类PPT的特殊处理**（含大量实拍活动照片）：
- 增加配图页/图片墙，每段内容对应1-2张照片展示
- 封面用深色渐变全幅背景，数据页用大数字排版
- 照片来自DOCX原稿，手工复制到项目images/目录

# Step 5: 图片获取（DOCX实拍照片优先，无需AI生成额外图片）

# Step 6: SVG生成（Executor Phase）
⚠️ **严格约束：必须由主agent连续逐页生成，不得委托子agent**

**Step 7: 后处理三步（必须顺序执行，每步确认无报错）**

⚠️ **在运行 Step 7.2 之前**，如果 SVG 文件在 `svg_output/` 子目录中，先修复图片路径：
```bash
cd <项目>/svg_output/
sed -i 's|images/|../images/|g' *.svg
```
然后再回到 ppt-master 根目录继续后处理。

```bash
cd ~/ppt-master

# Step 7.1: 分割讲稿为分页备注
python skills/ppt-master/scripts/total_md_split.py <项目路径>
# ✅ 确认无报错再继续
# ⚠️ 如果报错 "No notes content found"，检查 total.md 格式：必须用 "# 01_封面" 顶级标题，页数要与SVG数量匹配

# Step 7.2: SVG后处理（图片嵌入+圆角转路径）
python skills/ppt-master/scripts/finalize_svg.py <项目路径>
# ✅ 确认无报错（图片应全部显示 [OK]），如全部 [FAIL] 检查图片路径

# Step 7.3: 导出PPTX
python skills/ppt-master/scripts/svg_to_pptx.py <项目路径> -s final
# 输出：exports/<项目名>_<时间戳>.pptx
```

**⚠️ 绝不能违反的规则：**
1. **Step 4（Strategist）— BLOCKING**: 必须等用户确认，确认前不能生成任何SVG
2. **finalize_svg.py** 绝对不能跳过
3. 后处理三步必须顺序执行不合并，每步确认无报错
4. **导出参数：必须用 `-s final`**（从 `svg_final/` 导出），**禁止用 `-s svg_output`**
5. SVG生成必须由主agent连续逐页完成，**禁止委托给子agent**

---

## 设计原则

### 用户配色偏好（见 references/color-schemes.md）
- 活力橙 `#FF6B35` + 深海蓝 `#1E3A5F` + 金黄 `#FFD23F`
- 适合：机关培训、科普演示（清新活力、不呆板）

### 避免 AI 生成PPT的套路
- 不要每次都用同样的蓝色主题
- 有意义的视觉 > 装饰性图标
- 数据完整：不编造数据，用占位符标注缺失数据
- 字体搭配要有变化，不要总是 Inter/Roboto

### 单页一个核心观点
- 一页一个主题，不要堆砌
- 视觉层级：标题 → 副标题 → 正文 → 标注

---

## 常见问题 / 避坑指南

**Q: 输出在哪里？**
A: `~/ppt-master/exports/<项目名>_<时间戳>.pptx`

**Q: 想加动画？**
A: `svg_to_pptx.py` 支持 `-t`（翻页效果）、`-a`（元素入场动画）等参数，详见官方 SKILL.md Step 7。**如需精细控制（如按行分组、点击触发、定向飞入），用 pptx-animation skill 的 XML 注入法。**

**Q: 想给已有 PPTX 添加动画？**
A: 用 `pptx-animation` skill — 直接操作 PPTX 内部 XML，按 y 坐标自动分组，点击触发飞入+淡入动画。不走 svg_to_pptx.py 的 `-a` 参数。

**Q: 已有PPT想改局部？**
A: 用 `visual-edit` 工作流（`workflows/visual-edit.md`），或直接描述修改内容（具体到"第X页副标题改32号字"则直接改SVG）

**Q: python-docx 读取中文 docx 全是乱码？**
A: 原始文档为OCR扫描件时，`python-docx` 解析有严重中文Unicode问题。解法：用 `zipfile` 直接读取 XML：
```python
import zipfile, re
with zipfile.ZipFile(doc_path, 'r') as z:
    xml = z.read('word/document.xml').decode('utf-8')
texts = re.findall(r'<w:t[^>]*>([^<]+)</w:t>', xml)
full_text = ''.join(texts)
```

**Q: SKILL_DIR 路径找不到？**
A: 用这个：`~/.hermes/skills/ppt-work/ppt-master-repo/skills/ppt-master`

**Q: Eight Confirmations 要等多久？**
A: ⛔ BLOCKING — 必须等用户确认后才能继续，不能自己猜着执行。
⚠️ **例外**：用户主动说"继续"或"继续ppt"，或之前已确认过同类任务时，可直接继续生成，无需重复确认。

**Q: finalize_svg 报 "Image not found" 但图片确实存在？**
A: SVG文件在 `svg_output/` 子目录中时，`<image href="images/...">` 路径相对于项目根目录，**不是**相对于SVG文件。解法：
```bash
cd <项目>/svg_output/
sed -i 's|images/|../images/|g' *.svg
```
然后再运行 `finalize_svg.py`。

**Q: finalize_svg 报 "Image not found" 且图片路径已正确？**
A: 检查 finalize 命令是否从 ppt-master **根目录**执行（必须 `cd ~/ppt-master`）。

**Q: 用户上传了"定稿"、"最终版"、"附图"等文件，意味着什么？**
A: 当用户上传文件名含有 `定稿`、`最终版`、`附图`、`v2`、`final` 等关键词时，**这是优先级信号**：用户可能在使用更新后的内容替代旧版本。处理流程：
1. **不要只缓存文件就结束** — 必须主动向用户确认
2. 标准问法：「检测到您上传了【文件名】，这是最新版演讲稿吗？需要我用这个版本重新制作PPT吗？」
3. 如果用户说"是"或"重新制作"，立即用新文档重新走 SVG 生成流程
4. 典型案例（2026-05-22）：用户上传了 `定稿 - 附图.docx`（含24张照片最终版），AI 缓存后未确认，导致 PPT v2 仍基于旧版 `演讲稿_1_.docx` 生成

**Q: total_md_split 报 "No notes content found"？**
A: `total.md` 必须用 `# 01_封面` / `# 02_目录` 格式的顶级标题（与SVG文件名匹配），用 `---` 分隔的多文件合并方式不生效。
```markdown
# 01_封面
封面内容...

---

# 02_目录
目录内容...

---
```
每一页对应一个 `# NN_` 标题，不能把多页内容写成一个大块。

---

## 替代工具

## 视觉风格重设计路径（当用户反馈"太呆板"时）

用户明确要求"清新活力，不要太死板"时，说明标准Executor输出的SVG布局过于模板化（每页都是"顶部色条+左侧色条+卡片网格"的重复结构）。此时应走**视觉风格重设计路径**：

1. **重建SVG目录**：在项目下创建 `svg_v2/` 目录（保留原 `svg_output/` 作为备份）
2. **重新设计每页SVG**：每页采用**不同布局结构**，彻底打破模板重复感
   - 封面/章节页：深色渐变背景 + 装饰元素（神经网络线条/几何图形）
   - 内容页A：左右分栏 / 时间线 / 对比布局
   - 内容页B：大数字+标签 / 2x2网格 / 数据大字
   - 总结页：深色背景 + 核心要点
3. **保留讲稿备注**：通过XML层面直接替换PPT旧版中的notesSlide文件
4. **导出**：`python scripts/svg_to_pptx.py <项目路径> -s svg_v2 -o <输出路径>`

**布局多样化原则（核心：每页结构必须不同）**：

用户反馈"太板/太严肃"的根因：每页用同一套模板（统一侧边条+卡片网格），视觉上重复感强。v2成功经验：**彻底打破模板重复，每页完全不同结构**。

| 页面类型 | 推荐布局 | 避免重复 |
|----------|----------|----------|
| 封面 | 深色渐变背景 + 流动装饰线条/几何图形 + 圆形装饰叠加 | 白色背景 + 居中标题 |
| 目录 | 三列卡片**错落不等高**，每列不同配色 | 等高四格卡片 |
| 导语/引言 | 大引号 + 大字留白 + 右侧装饰圆形/流动曲线 | 白色背景 + 居中文字 |
| 人物/组织介绍 | **左右分栏**（一侧全幅照片 + 另一侧纵向内容/数据） | 卡片网格 |
| 数据成果 | **大数字瀑布流**（数字80-120px） + 深色背景 + 装饰圆形 | 纯卡片网格 |
| 活动图片展示 | **瀑布流不规则图片墙**，多列错落 | 整齐网格 |
| 结语/致谢 | 深色渐变 + 装饰图形（莲花/重叠半透明圆） + 重叠标题 | 白色背景 + 居中文字 |

**实用原则**：
- 连续生成SVG时，用 `execute_code` 逐页生成，确保每页都有不同视觉结构
- 背景不要全是白色，深色背景（`#1E3A5F` 深海蓝）配合亮色装饰更显活力
- 避免每页顶部都有"一条色带"的习惯——试试全幅背景、侧边装饰、或无色块

**配色方案（活力清新风格）**：
```
背景深色：#1A1A2E（科技深灰）
背景浅色：#F8FAFC（清新白）
主色蓝：#4A90D9（科技蓝）
活力橙：#FF6B35（点缀）
金黄：#FFD23F（点缀）
文字深：#1A1A2E
文字浅：#FFFFFF
```

**讲稿备注注入（XML替换法）**：
当需要保留旧版PPT中的备注内容到新版SVG导出的PPTX时，通过直接替换PPT内XML实现：
```python
import zipfile, shutil, re

def inject_notes_via_xml(output_pptx, source_pptx_with_notes):
    """将源PPTX的讲稿备注注入到输出PPTX对应页面"""
    with zipfile.ZipFile(source_pptx_with_notes, 'r') as src:
        src_names = src.namelist()
    with zipfile.ZipFile(output_pptx, 'r') as out:
        out_names = out.namelist()
    
    notes_map = {}
    for name in src_names:
        if name.startswith('ppt/notesSlides/notesSlide') and name.endswith('.xml'):
            num = re.search(r'notesSlide(\d+)\.xml', name).group(1)
            notes_map[num] = src.read(name)
    
    tmp = output_pptx + '.tmp'
    shutil.copy(output_pptx, tmp)
    with zipfile.ZipFile(tmp, 'r') as fin, zipfile.ZipFile(output_pptx, 'w', zipfile.ZIP_DEFLATED) as fout:
        for item in fin.infolist():
            num = re.search(r'notesSlide(\d+)\.xml', item.filename)
            if num and num.group(1) in notes_map:
                fout.writestr(item, notes_map[num.group(1)])
            else:
                fout.writestr(item, fin.read(item.filename))
```

## 替代工具

- **PPTAgent**（EMNLP 2025）：`uvx pptagent onboard` 初始化，`uvx pptagent generate "主题" -o output.pptx` 生成
  - GitHub: https://github.com/icip-cas/PPTAgent
  - 适合需要更高设计质量或作为对比参考

### SVG 生成最佳实践（execute_code 路径）

当内容已整理好时，用 `execute_code` 批量生成 SVG 更高效：

```python
svg_template = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <!-- SVG content -->
</svg>'''
with open('<项目>/svg_output/01_封面.svg', 'w') as f:
    f.write(svg_template)
```

- 每页一个SVG文件，文件名格式：`NN_标题.svg`（数字+下划线开头）
- viewBox 固定为 `0 0 1280 720`（16:9）
- 图片路径用相对路径 `../images/xxx.jpeg`（svg_output是子目录）
- 生成完所有SVG后再执行后处理三步

> ⚠️ 此路径适用于内容已充分整理的场景。若内容结构不清晰，需先通过 Strategist Phase + Executor Phase 的结构化流程生成设计规格和内容大纲。

**交付检查清单**

- [ ] PPTX 导出无报错
- [ ] 所有幻灯片可原生编辑（PowerPoint/Keynote中验证）
- [ ] 无文字溢出或截断
- [ ] 配色一致（活力橙 #FF6B35 + 深海蓝 #1E3A5F + 金黄 #FFD23F）
- [ ] 内容与用户原始材料一致（无编造数据）
- [ ] 演讲者备注已嵌入（每页均有对应备注内容）
- [ ] 文件名描述清晰

---

## 支持文件

| 文件 | 用途 |
|------|------|
| `references/color-schemes.md` | 用户配色偏好（活力橙+深海蓝+金黄体系），用于 Strategist Phase 配色确认 |
| `references/speaker-notes-embedding.md` | 讲稿备注注入的XML替换法，用于保留旧版PPT备注到新SVG导出版本 |
| `references/speech-docx-image-extraction.md` | 演讲稿DOCX图片提取+分配指南：zipfile提取图片、SVG路径修复、12页结构规划 |
