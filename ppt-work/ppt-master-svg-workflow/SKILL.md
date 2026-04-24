---
name: ppt-master-svg-workflow
description: 用 ppt-master 从 SVG 生成 PPTX 的完整流程，包括项目初始化、SVG生成规范、导出命令和常见错误处理
category: productivity
---

# ppt-master SVG Workflow Skill

## Trigger
用 ppt-master 做 PPT 时，从生成 SVG 页面到导出 PPTX 的完整流程。

## Workflow

### 1. 初始化项目
```bash
python3 ~/.hermes/skills/ppt-master/skills/ppt-master/scripts/project_manager.py init <项目名> --format ppt169
```

### 2. 写入内容文件
将文字稿内容写入 `sources/content.md`（ppt-master 会自动解析）
或直接写入 `svg_output/` 目录下的 SVG 文件

### 3. 生成 SVG 页面（手动生成，MiniMax-M2.7模型可用）
每个 SVG 文件命名：`NN_页面名称.svg`，放在项目目录的 `svg_output/` 下

**关键规则 — 避免 XML 解析错误：**
- SVG 内文本避免使用原始 `&` 字符，会导致 "not well-formed (invalid token)" 错误
- 用 `+` 替代 `&`（如 `PAGE SETUP + DOCUMENT GRID` 而非 `PAGE SETUP & DOCUMENT GRID`）
- 所有文本内容用双引号包围的属性

**SVG 设计规范（简约清新风格）：**
```
配色常量：
  RED    = #C0392B  (点缀)
  NAVY   = #1A3A5C  (主色)
  GOLD   = #B8860B  (点缀)
  WHITE  = #FFFFFF
  BG     = #F8FAFC  (背景)
  LGRAY  = #EEEEEE
  MGRAY  = #999999
  DARK   = #2D3A4A
  GREEN  = #276B4A
  TEAL   = #007A87
  PURPLE = #5C3D6E

画布：1280 × 720 px（16:9）
字体：中文 Microsoft YaHei，英文 Arial
布局：浅灰白底 + 蓝色主色 + 红色点缀，卡片式，大量留白
页码格式：<text x="1240" y="690" font-family="Arial" font-size="12" fill="#A0ADB8" text-anchor="end">NN / 24</text>
```

### 4. 导出 PPTX
```bash
cd <项目目录>
python3 ~/.hermes/skills/ppt-master/skills/ppt-master/scripts/svg_to_pptx.py . -s output -o <输出路径>
```
- `-s output` 指定读取 `svg_output/` 目录（不是 `svg_final/`）
- 生成两个文件：`<output>.pptx`（原生编辑版）+ `<output>_svg.pptx`（PNG+SVG兼容版）

### 5. 常见错误处理
- **"No SVG files found"** → 检查是否用了 `-s output`（不是 `-s final`）
- **"not well-formed (invalid token)"** → SVG 内文本含 `&` 字符，改用 `+`
- **SVG 解析失败但PPT仍生成** → 该页使用了 fallback 模式，效果可能不完美

## 输出路径
保存到 TZB 文件夹：`/mnt/nfs/2026年统战工作/1.办公室/4.格式培训/`

## Pexels 图片下载（如需配图）
```bash
curl -s "https://api.pexels.com/v1/search?query=<关键词>&per_page=5" \
  -H "Authorization: V1oT4JKRmTfy39ZAOF1Q0tg66g3lcj4JHUXGecatRutI8PJ2BdAablH0" | \
  python3 -c "
import json,sys,urllib.request
data=json.load(sys.stdin)
for p in data['photos'][:3]:
    url=p['src']['large']
    name=p['id']
    urllib.request.urlretrieve(url,f'/tmp/pexels_{name}.jpg')
    print(url)
"
```

## Verification
导出后检查：
```bash
ls -lh <输出文件>   # 确认文件大小 > 0
python3 -c "from pptx import Presentation; p=Presentation('<文件>'); print(len(p.slides),'slides')"
```
