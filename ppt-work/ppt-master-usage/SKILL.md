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

```
SKILL_DIR=~/ppt-master/skills/ppt-master
PROJECT_DIR=~/ppt-master/projects   # 项目存放目录
```

**⚠️ 重要：SKILL_DIR 路径**
- 正确：`~/.hermes/skills/ppt-work/ppt-master-repo/skills/ppt-master`
- 错误：`~/.hermes/skills/ppt-master-repo/skills/ppt-master`（不存在）

**完整七步流程（必须按顺序执行）：**
```bash
# Step 1: 内容转换（如有PDF/DOCX/Excel）
${PYTHON} ${SKILL_DIR}/scripts/source_to_md/pdf_to_md.py <file>
${PYTHON} ${SKILL_DIR}/scripts/source_to_md/doc_to_md.py <file>
${PYTHON} ${SKILL_DIR}/scripts/source_to_md/excel_to_md.py <file>

# Step 2: 初始化项目（进入 ppt-master 目录执行）
cd ~/ppt-master
${PYTHON} ${SKILL_DIR}/scripts/project_manager.py init <项目名> --format ppt169

# Step 3: 导入源文件
${PYTHON} ${SKILL_DIR}/scripts/project_manager.py import-sources <项目路径> <源文件...> --move

# Step 4: ⛔ BLOCKING — Strategist Phase（八项确认）
#    必须先读取 ${SKILL_DIR}/SKILL.md 完整流程
#    向用户展示八项确认，等待明确确认后才能继续
#    八项确认内容：a.画布尺寸 b.页面数量 c.受众定位 d.风格定位
#                  e.配色方案 f.图标方案 g.字体方案 h.图片方案

# Step 5: 图片获取（如设计稿需要AI图片则执行，否则跳过）

# Step 6: SVG生成（Executor Phase — 严格按照 spec_lock.md 执行）

**Step 7: 后处理三步（必须顺序执行，不能跳过）**
```bash
# ⚠️ 先 cd 到 ppt-master 目录
cd ~/ppt-master

# Step 7.1: 分割讲稿为分页备注
python skills/ppt-master/scripts/total_md_split.py <项目路径>

# Step 7.2: SVG后处理（图标嵌入/图片裁剪/文字扁平化/圆角转路径）
python skills/ppt-master/scripts/finalize_svg.py <项目路径>

# Step 7.3: 导出PPTX
# ⚠️ 用 -s svg_output（从 svg_output/ 导出），不是 -s final
python skills/ppt-master/scripts/svg_to_pptx.py <项目路径> -s svg_output -o <输出路径>
```

**⚠️ 绝不能跳过的关键节点：**
1. **Step 4（Strategist）— BLOCKING**: 八项确认必须等用户确认，确认前不能生成任何SVG
2. **finalize_svg.py** 绝对不能跳过
3. 后处理三步必须顺序执行，不能合并
4. 导出用 `-s svg_output`（从 svg_output/ 而非 svg_final/，这是正确参数）
4. 导出必须用 `-s final`（从 svg_final/ 而非 svg_output/）

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
A: ⛔ BLOCKING — 必须等用户确认后才能继续，不能自己猜着执行

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

**布局多样化原则**：
| 页面类型 | 推荐布局 | 避免 |
|----------|----------|------|
| 封面/总结 | 深色全幅背景 + 居中标题 | 白色背景 |
| 数据展示 | 大数字(80-120px)+标签 + 深色背景 | 纯卡片网格 |
| 对比/并列 | 左右分栏 或 LLM vs Agent大字对比 | 每页相同的侧边条 |
| 流程/时间 | 横向时间线 + 节点标签 | 堆叠卡片 |
| 架构/体系 | 三列/四列并排特色卡片 | 单一模板重复 |

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

**Executor 快捷路径（内容结构已知时）：**
当PPT内容已经过充分整理（如已有完整讲稿/大纲），内容结构清晰，可直接写SVG而不走完整的Executor子代理流程：
1. 创建 `<项目>/svg_output/` 和 `<项目>/notes/` 目录
2. 通过 `execute_code` + `write_file` 直接生成每页SVG（顺序逐页，每页独立一个文件）
3. 将每页对应的演讲稿内容写入 `notes/<页码>_<slug>.md`（文件名需与SVG页码对应）
4. 执行 Step 7 后处理三步

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
