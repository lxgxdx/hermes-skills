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

## SVG 图片路径修复

如果 SVG 文件在 `svg_output/` 子目录中，`<image href="images/...">` 路径相对于**项目根目录**，而不是 SVG 文件本身。需要先修复路径再运行 `finalize_svg.py`：

```bash
cd <项目>/svg_output/
sed -i 's|images/|../images/|g' *.svg
```

## 图片与页面的分配原则

演讲稿 PPT 中，图片按以下规律分配到各页：

| 主题段落 | 对应图片编号（参考） | 页面类型 |
|----------|---------------------|----------|
| 封面 | 可用LOGO或主题图 | 封面 |
| 民主党派·义诊 | image5.jpeg, image6.jpeg | 内容页 |
| 无党派人士·文化活动 | image11/13/14.jpeg | 内容页 |
| 党外知识分子·联百企 | image12.png（专家合影）| 内容页 |
| 活动写真汇总 | image1/2/7/8/9/17/19/21 | 图片墙 |

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
