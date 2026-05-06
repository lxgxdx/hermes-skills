# PPTX 动画注入 — 调试过程记录

## 问题：分组总是变成1组

### 错误尝试

用 `600 EMU` 作为行分组阈值，结果每页所有 shape 都挤成一组。

原因：600 EMU = 0.00066cm，阈值太小，无法分开任何元素。

### 根因分析

slide2.xml 的 y 坐标分布：
```
y=0       (0.00cm) — 背景矩形
y=847249  (0.93cm) — 第一个文本框
y=1168718 (1.28cm)
y=1219200 (1.33cm)
y=1619250 (1.77cm)
... (共36个唯一值，分布在0~7.5cm)
```

最小相邻间距 847249 EMU（0.93cm），最大间距达 2000000+ EMU。

### 正确阈值

| 阈值 | EMU值 | 相当于 | slide2分组数 |
|------|-------|--------|------------|
| 600 EMU | 600 | 0.00066cm | 1（全部合一）|
| 250000 EMU | 250000 | 0.27cm | 9 |
| 274320 EMU | 274320 | 0.30cm | 9 |
| 300000 EMU | 300000 | 0.33cm | 9 |

**最终选 274320 EMU（0.3cm）**，经验证可正确分组 15 页共 144 组动画。

## 其他陷阱

### lxml 不能设置 xmlns 属性
```python
# 错误
timing.set('xmlns:a', NS_A)  # ValueError: Invalid attribute name 'xmlns:a'

# 正确：用字符串拼接 XML
timing_str = f'''<p:timing xmlns:p="{NS_P}" ...>...</p:timing>'''
timing_tree = etree.fromstring(timing_str)
```

### shape ID 路径
```python
# 错误
cNvPr = sp.find(f'{NS_P_URL}nvGrpSpPr/{NS_P_URL}cNvPr')

# 正确（sp 的 cNvPr 在 nvSpPr 下）
cNvPr = sp.find(f'{NS_P_URL}nvSpPr/{NS_P_URL}cNvPr')
```

### XML 命名空间查找
```python
# ElementTree 的 find() 对带前缀的命名空间必须用完整 URI
sp_tree = root.find(f'.//{NS_P_URL}spTree')  # 正确
sp_tree = root.find('.//spTree')              # 找不到

# 或者注册命名空间
ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}
sp_tree = root.find('.//p:spTree', ns)        # 也正确
```

### y 坐标提取
从 `<a:off x="..." y="..."/>` 中提取时，直接用正则比 XPath 更可靠：
```python
sp_xml = etree.tostring(sp, encoding='unicode')
y_match = re.search(r'<a:off[^>]*y="(\d+)"', sp_xml)
y_val = int(y_match.group(1)) if y_match else 0
```

## 验证方法

```bash
# 检查分组数（提前预测动画组数）
python3 -c "
import zipfile, re
from lxml import etree
PPTX = '/path/to/file.pptx'
NS = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
THRESHOLD = 274320
with zipfile.ZipFile(PPTX) as z:
    for i in range(1, 16):
        with z.open(f'ppt/slides/slide{i}.xml') as f:
            tree = etree.parse(f)
        root = tree.getroot()
        sp_tree = root.find(f'.//{NS}spTree')
        shapes = sp_tree.findall(f'{NS}sp')
        ys = []
        for sp in shapes:
            cNvPr = sp.find(f'{NS}nvSpPr/{NS}cNvPr')
            if cNvPr is None: continue
            sp_xml = etree.tostring(sp, encoding='unicode')
            m = re.search(r'<a:off[^>]*y=\"(\d+)\"', sp_xml)
            if m: ys.append(int(m.group(1)))
        ys.sort()
        groups = 0; last = None; g = 0
        for y in ys:
            if last is None or (y-last) > THRESHOLD:
                groups += 1
            last = y
        print(f'slide{i}: {len(shapes)}shapes -> {groups}groups')
"
```
