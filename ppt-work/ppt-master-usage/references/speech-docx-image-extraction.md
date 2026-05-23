# 演讲稿 DOCX 图片提取与 PPT 分配指南

## 从 DOCX 中提取所有图片

当演讲稿 DOCX 含有大量实拍活动照片（24张、75MB等），直接用 `import-sources` 会失败，必须手动提取：

```python
import zipfile, os

doc_path = "xxx.docx"
out_dir = "<项目>/images"
os.makedirs(out_dir, exist_ok=True)

with zipfile.ZipFile(doc_path, 'r') as z:
    for name in z.namelist():
        if name.startswith('word/media/') and not name.endswith('/'):
            fname = os.path.basename(name)
            data = z.read(name)
            with open(os.path.join(out_dir, fname), 'wb') as f:
                f.write(data)
            print(f"Extracted: {fname} ({len(data)//1024}KB)")
```

## 提取文档文字内容

```python
import zipfile, re

with zipfile.ZipFile(doc_path, 'r') as z:
    xml = z.read('word/document.xml').decode('utf-8')
texts = re.findall(r'<w:t[^>]*>([^<]+)</w:t>', xml)
full_text = ''.join(texts)
print(full_text)  # 全文
```

## 图片与文档叙事顺序的对应关系（关键！）

**必须通过 rId 映射确定图片真实顺序**，不能按文件名数字大小猜测：

```python
import zipfile, re

doc_path = "xxx.docx"

with zipfile.ZipFile(doc_path, 'r') as z:
    xml = z.read('word/document.xml').decode('utf-8')
    rels = z.read('word/_rels/document.xml.rels').decode('utf-8')

# 1. 建立 rId → 图片名 映射
rid_to_img = {}
for m in re.finditer(r'Id="(rId\d+)"[^>]+Target="media/(image\d+\.jpeg)"', rels):
    rid_to_img[m.group(1)] = m.group(2)

# 2. 按图片在 document.xml 中出现的顺序（rId出现顺序）确定叙事顺序
img_positions = []
for rid, img in rid_to_img.items():
    pos = xml.find(f'r:embed="{rid}"')
    if pos >= 0:
        img_positions.append((pos, img))

img_positions.sort()
ordered_images = [img for _, img in img_positions]
print(f"图片叙事顺序: {ordered_images}")
```

**分配原则**：图片顺序 = 文档叙事顺序。封面用 image1，第三章内容用第三章附近的图片，不要打乱顺序。

## SVG 图片路径修复

如果 SVG 文件在 `svg_output/` 子目录中，`<image href="images/...">` 路径相对于**项目根目录**，而不是 SVG 文件本身：

```python
import os
svg_dir = '<项目>/svg_output'
for fname in os.listdir(svg_dir):
    if fname.endswith('.svg'):
        path = f'{svg_dir}/{fname}'
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        fixed = content.replace('href="images/', 'href="../images/')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fixed)
```

## 演讲背景PPT的图片布局原则

1. **统一尺寸**：所有图片指定 `width`/`height` + `preserveAspectRatio="xMidYMid slice"` + `rx="10"` 圆角
2. **瀑布流错落**：不同行可用不同高度，但同列宽度要协调
3. **数据页叙事**：大数字旁必须跟叙事文字（如 "协调贷款" → "8亿元"），数字用大字号，叙事用小号字在下方说明
4. **全幅背景**：封面/故事/结语页用 `preserveAspectRatio="xMidYMid slice"` 撑满全屏
5. **并排展示**：同一主题的多张图片用相同尺寸并排

## 典型12页演讲稿PPT结构

```
01 封面         — 深色渐变背景 + 演讲标题
02 目录         — 三篇章彩色卡片
03 导语         — 深色背景 + 大引号装饰
04 民主党派工作  — 左侧数据 + 右侧义诊照片
05 无党派人士工作 — 四格数据卡片 + 活动图组
06 党外知识分子  — 左侧文字 + 右侧专家合影
07 成果数据总览  — 深色背景 + 大数字网格
08 活动写真      — 2×4图片墙
09 结语          — 三色方块 + 核心金句
10 一路同行      — 全幅照片背景 + 文字叠加
11 感谢聆听      — 深色背景居中
12 尾页          — 标题 + 装饰莲花
```
