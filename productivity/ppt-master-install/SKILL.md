---
name: ppt-master-install
description: 安装 ppt-master 技能及其依赖（GitHub 5.4k stars 的 AI PPT 生成工具）
triggers:
  - "装 ppt-master"
  - "安装 ppt-master"
  - "ppt-master 依赖"
  - "pip install svgelement 失败"
  - "cairosvg 安装失败"
---

# ppt-master 安装手册

## 技能简介

ppt-master（GitHub: hugohe3/ppt-master）是 AI 驱动的 PPT 生成工具，输入 PDF/DOCX/URL/Markdown，输出原生可编辑的 .pptx 文件（真正的 PowerPoint 形状，不是图片）。

## 安装步骤

### 第一步：克隆仓库

```bash
cd ~/.hermes/skills
git clone https://github.com/hugohe3/ppt-master.git ppt-master
# 注意：默认超时 30s 会失败，需要 timeout>=120s
```

克隆结果路径：`~/.hermes/skills/ppt-master/`
技能入口：`~/.hermes/skills/ppt-master/skills/ppt-master/SKILL.md`

### 第二步：创建独立 venv

```bash
cd ~/.hermes/hermes-agent
uv venv          # 创建 .venv
source .venv/bin/activate
```

### 第三步：安装依赖（分步安装，避免 pycairo 系统依赖问题）

```bash
# 核心依赖（不含 pycairo）
uv pip install reportlab PyMuPDF mammoth markdownify ebooklib nbconvert requests beautifulsoup4 pillow numpy

# svglib 1.5.1（不需要 pycairo，比 1.6+ 轻量）
uv pip install "svglib<1.6"

# cairosvg（自己带了 cairocffi，不需要系统 cairo）
uv pip install cairosvg

# AI 图片生成（可选，按需）
uv pip install curl_cffi
uv pip install google-genai
uv pip install openai

# python-pptx（最后装）
uv pip install python-pptx
```

### 第四步：验证

```bash
source .venv/bin/activate
python3 -c "
import pptx, svglib, reportlab, fitz, mammoth, markdownify
import ebooklib, nbconvert, requests, bs4, PIL, numpy, cairosvg
import curl_cffi, google.genai as genai, openai
print('All 16 deps OK')
"
```

## 已知坑（按时间排序）

| 问题 | 原因 | 解法 |
|------|------|------|
| `git clone` 超时 | 默认 30s 不够 | 加 timeout 或后台运行 |
| `pip install svgelement` 失败 | 包名写错 | 正确名字是 `svglib` |
| `svglib>=1.6` 编译失败 | 依赖 pycairo，需要系统 `libcairo2-dev`（需要 root） | 用 `svglib<1.6`（1.5.1 版本无 C 扩展）|
| `cairosvg` 装不上 | 依赖 pycairo | cairosvg 自己带了 cairocffi，可以单独装，跳过 pycairo 编译 |
| `import genai` 失败 | 包名是 `google-genai`，import 路径是 `google.genai` | `import google.genai as genai` |
| python-pptx 已有但找不到 | 原 venv 里版本不对 | 用新建的 .venv 里的版本 |

## 运行 PPT 生成（完整工作流见 SKILL.md）

```bash
# 激活环境
source ~/.hermes/hermes-agent/.venv/bin/activate

# 示例：初始化项目
python3 ~/.hermes/skills/ppt-master/skills/ppt-master/scripts/project_manager.py init my-ppt --format ppt169
```

## 技能文件结构

```
~/.hermes/skills/ppt-master/
├── SKILL.md                      # 主入口（仓库根）
├── skills/ppt-master/
│   ├── SKILL.md                  # AI Agent 技能定义（使用这个！）
│   ├── scripts/                  # 所有脚本
│   │   ├── project_manager.py    # 项目管理
│   │   ├── svg_to_pptx.py        # SVG → PPTX 导出
│   │   ├── total_md_split.py     # 拆分 speaker notes
│   │   ├── finalize_svg.py       # SVG 后处理
│   │   └── source_to_md/         # 各类文档转 Markdown
│   │       ├── pdf_to_md.py
│   │       ├── doc_to_md.py
│   │       ├── web_to_md.py
│   │       └── ppt_to_md.py
│   ├── templates/                # 布局/图表/图标模板
│   ├── references/               # 角色定义和技术规范
│   └── workflows/                # 模板创建流程
```
