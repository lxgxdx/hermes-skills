---
name: pptx-animation
description: Add click-triggered entrance animations to existing PPTX files via XML manipulation. Covers lxml namespace gotchas, EMU coordinate grouping, and animation XML structure for PowerPoint OOXML.
triggers:
  - 添加动画
  - PPTX动画
  - 添加点击动画
  - add animation to PPTX
  - 幻灯片动画
category: ppt-work
owner: hermes-agent
---

# PPTX 动画添加工具

向已有 PPTX 文件注入点击触发的入场动画（淡入、飞入等）。

## 核心流程

### 1. 解压 PPTX
PPTX 本质是 ZIP，直接解压操作 XML：
```python
import zipfile, shutil, os

PPTX = '/path/to/input.pptx'
EXTRACT = '/tmp/pptx_work'
OUTPUT  = '/path/to/output.pptx'

if os.path.exists(EXTRACT):
    shutil.rmtree(EXTRACT)
with zipfile.ZipFile(PPTX, 'r') as z:
    z.extractall(EXTRACT)
```

### 2. 找到 Shape 并提取 y 坐标（关键）
```python
from lxml import etree
import re

NS_P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS_A  = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS_P_URL = '{' + NS_P + '}'

slides_dir = os.path.join(EXTRACT, 'ppt/slides')
# slide_files = sorted(...)
```

**⚠️ 陷阱：Shape ID 路径是 `p:nvSpPr/p:cNvPr`，不是 `p:nvGrpSpPr/p:cNvPr`**

```python
shape_info = []
for sp in shapes:
    cNvPr = sp.find(f'{NS_P_URL}nvSpPr/{NS_P_URL}cNvPr')  # 正确路径
    if cNvPr is None:
        continue
    spid = cNvPr.get('id', '')
    
    # 用正则从 XML 字符串提取 y 坐标（更可靠）
    sp_xml = etree.tostring(sp, encoding='unicode')
    y_match = re.search(r'<a:off[^>]*y="(\d+)"', sp_xml)
    y_val = int(y_match.group(1)) if y_match else 0
    
    shape_info.append({'spid': spid, 'y': y_val})
```

### 3. 按 y 坐标分组（阈值：274320 EMU ≈ 0.3cm）

**⚠️ 陷阱：EMUs 单位很小！600 EMU = 0.00066cm，完全分不开行。正确阈值：274320 EMU = 0.3cm**

```python
THRESHOLD = 274320  # EMU ≈ 0.3cm

shape_info.sort(key=lambda x: x['y'])
groups = []
current_group = []
last_y = None
for si in shape_info:
    if last_y is None or abs(si['y'] - last_y) <= THRESHOLD:
        current_group.append(si)
    else:
        groups.append(current_group)
        current_group = [si]
    last_y = si['y']
if current_group:
    groups.append(current_group)
```

### 4. 生成动画 XML（正确方式）

**⚠️ 陷阱：不能用 `options.verb`** — 这是 OLE 动词触发，PowerPoint/WPS 不识别。必须用 `begin="indefinite"` + `p:sldTgt` 等待点击。

**正确触发结构：**
```python
def make_anim_par(spid, aid, direction='l'):
    dir_map = {
        'l': ('horz', 'left'),
        'r': ('horz', 'right'),
        't': ('vert', 'top'),
        'b': ('vert', 'bottom'),
        'c': ('center', 'center'),
    }
    d_key, d_val = dir_map.get(direction, ('horz', 'left'))

    return f'''<p:par>
            <p:cBhvr>
              <p:cTn id="{aid}" fill="hold" begin="indefinite" dur="1" autoRev="off">
                <p:stCondLst>
                  <p:cond delay="0">
                    <p:tgtEl>
                      <p:sldTgt/>
                    </p:tgtEl>
                  </p:cond>
                </p:stCondLst>
              </p:cTn>
              <p:tgtEl>
                <p:spTgt spid="{spid}"/>
              </p:tgtEl>
            </p:cBhvr>
            <p:anim calcmode="lin" fill="hold" presetID="1" presetClass="entr" presetSubtype="16" nodeType="clickEffect" ac="show">
              <p:stCondLst>
                <p:cond delay="0"/>
              </p:stCondLst>
              <p:strLst>
                <p:str>from ({d_key} {d_val} 914400 0)</p:str>
              </p:strLst>
            </p:anim>
          </p:par>'''
```

**timing 根节点正确结构（python-pptx 内部格式）：**
```python
def make_timing_xml(anims_xml):
    return f'''<p:timing xmlns:p="{NS_P}" xmlns:a="{NS_A}">
  <p:tnLst>
    <p:par>
      <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
        <p:childTnLst>
{anims_xml}
        </p:childTnLst>
      </p:cTn>
    </p:par>
  </p:tnLst>
</p:timing>'''
```
```

### 5. 组装 timing 节点并写入

```python
    timing_str = make_timing_xml('\n'.join(anim_parts))

    # 移除旧的 timing 块（直接字符串替换，不用 lxml）
    content = re.sub(r'<p:timing>.*?</p:timing>', '', content, flags=re.DOTALL)
    content = content.replace('</p:sld>', timing_str + '</p:sld>')

    with open(sf_path, 'w', encoding='utf-8') as f:
        f.write(content)
```

### 6. 重新打包为 PPTX

```python
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zout:
    for dirpath, dirnames, filenames in os.walk(EXTRACT):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            arcname = os.path.relpath(filepath, EXTRACT)
            zout.write(filepath, arcname)
```

## 关键参数速查

| 参数 | 值 | 说明 |
|------|-----|------|
| EMU 单位 | 914400 EMU = 1cm | PowerPoint 内部坐标单位 |
| 行分组阈值 | 274320 EMU | ≈ 0.3cm，适合大多数布局 |
| 点击触发 | `begin="indefinite"` + `p:sldTgt` | 等同于"点击幻灯片触发" |
| 动画类型 | `presetClass="entr"` + `presetSubtype="16"` | 16 = 飞入（Fly In） |
| 飞入距离 | `from (horz left 914400 0)` | 左侧飞入，914400 EMU = 1cm |
| 动画属性 | `ac="show"` | 显示动画（不是 `animate`） |
| 节点类型 | `nodeType="clickEffect"` | 点击触发效果 |

## ⚠️ 已知陷阱

1. **`options.verb` 是 OLE 动词，不是点击触发** — PowerPoint/WPS 不识别，必须用 `begin="indefinite"` + `p:sldTgt`
2. **Shape ID 路径是 `p:nvSpPr/p:cNvPr`**，不是 `p:nvGrpSpPr/p:cNvPr`
3. **EMU 阈值不能太小**（600 EMU 会把所有元素合为一组），正确阈值 274320 EMU
4. **lxml 不能用 `set()` 设置 xmlns 属性**，要字符串拼接后 `fromstring()` 解析
5. **直接 XML 注入的 `p:anim` 可能不被 WPS 兼容**（PowerPoint 通常正常）
6. **LibreOffice 无法加载 python-pptx 生成的 PPTX**（原文件和带动画文件都报错），不影响 PowerPoint 使用

## 参考脚本

- `scripts/add_pptx_animations.py` — 完整的可运行脚本，处理15页PPT，144组动画
