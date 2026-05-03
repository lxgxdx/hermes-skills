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
SKILL_DIR=~/.hermes/skills/ppt-master-repo/skills/ppt-master
PYTHON=~/.hermes/hermes-agent/.venv/bin/python3
```

**标准流程（永远按这个顺序）：**
```bash
# 1. 内容转换（如有PDF/DOCX/Excel）
${PYTHON} ${SKILL_DIR}/scripts/source_to_md/pdf_to_md.py <file>
${PYTHON} ${SKILL_DIR}/scripts/source_to_md/doc_to_md.py <file>
${PYTHON} ${SKILL_DIR}/scripts/source_to_md/excel_to_md.py <file>

# 2. 初始化项目
${PYTHON} ${SKILL_DIR}/scripts/project_manager.py init <项目名> --format ppt169

# 3. 导入源文件
${PYTHON} ${SKILL_DIR}/scripts/project_manager.py import-sources <项目路径> <源文件...> --move

# 4. 后处理三步（必须顺序执行，不能跳过）
${PYTHON} ${SKILL_DIR}/scripts/total_md_split.py <项目路径>
${PYTHON} ${SKILL_DIR}/scripts/finalize_svg.py <项目路径>
${PYTHON} ${SKILL_DIR}/scripts/svg_to_pptx.py <项目路径> -s final
```

**三条铁律（永不违反）：**
1. finalize_svg.py 绝对不能跳过
2. 后处理三步必须顺序执行，不能合并
3. 导出必须用 `-s final`（从 svg_final/ 而非 svg_output/）

---

## 设计原则

### 避免 AI 生成PPT的套路
- 不要每次都用同样的蓝色主题
- 有意义的视觉 > 装饰性图标
- 数据完整：不编造数据，用占位符标注缺失数据
- 字体搭配要有变化，不要总是 Inter/Roboto

### 单页一个核心观点
- 一页一个主题，不要堆砌
- 视觉层级：标题 → 副标题 → 正文 → 标注

---

## 常见问题

**Q: 输出在哪里？**
A: `exports/<项目名>_<时间戳>.pptx`

**Q: 想加动画？**
A: `svg_to_pptx.py` 支持 `-t`（翻页效果）、`-a`（元素入场动画）等参数，详见官方 SKILL.md Step 7

**Q: 已有PPT想改局部？**
A: 用 `visual-edit` 工作流（`workflows/visual-edit.md`），或直接描述修改内容（具体到"第X页副标题改32号字"则直接改SVG）

---

## 替代工具

- **PPTAgent**（EMNLP 2025）：`uvx pptagent onboard` 初始化，`uvx pptagent generate "主题" -o output.pptx` 生成
  - GitHub: https://github.com/icip-cas/PPTAgent
  - 适合需要更高设计质量或作为对比参考

---

## 交付检查清单

- [ ] PPTX 导出无报错
- [ ] 所有幻灯片可原生编辑（PowerPoint/Keynote中验证）
- [ ] 无文字溢出或截断
- [ ] 配色一致
- [ ] 内容与用户原始材料一致（无编造数据）
- [ ] 文件名描述清晰
