#!/usr/bin/env python3
"""
给 PPTX 添加点击触发的飞入+淡入动画
- 按行分组（阈值 274320 EMU ≈ 0.3cm）
- 点击一次 → 该行内容从不同方向飞入
- 不同页的行用不同的进入方向（左右交替 + 居中缩放）

用法：
    python3 add_pptx_animations.py /path/to/input.pptx /path/to/output.pptx
"""
import zipfile, os, shutil, re, sys
from collections import defaultdict

# ============================================================
# 配置（修改这两个路径即可）
# ============================================================
PPTX    = sys.argv[1] if len(sys.argv) > 1 else '/mnt/nfs/2026年统战工作/1.办公室/4.格式培训/AI浪潮下的机关工作变革（清新版·讲稿备注）.pptx'
OUTPUT  = sys.argv[2] if len(sys.argv) > 2 else '/mnt/nfs/2026年统战工作/1.办公室/4.格式培训/AI浪潮下的机关工作变革（清新版·讲稿备注·动画版）.pptx'
EXTRACT = '/tmp/pptx_anim_work'

# 命名空间
NS_P   = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS_A   = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS_R   = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

# 行分组阈值（274320 EMU ≈ 0.3cm）
THRESHOLD = 274320

# 相邻组延迟（秒）
GROUP_DELAY = 0.2

# 动画方向序列（循环使用）
DIRECTIONS = ['l', 'r', 'l', 'r', 'c', 'l', 'r', 'l', 'r', 'c']

# ============================================================
# 辅助函数
# ============================================================

def make_anim_par(spid, aid, direction='l'):
    """
    生成单个 shape 的点击触发动画 XML。

    关键：触发机制使用 begin="indefinite" + p:sldTgt（等待幻灯片点击），
    而非 options.verb（OLE 动词，PowerPoint 不识别）。
    """
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


def make_timing_xml(anims_xml):
    """
    生成 timing 根节点。

    正确结构（python-pptx 内部格式）：
      p:timing > p:tnLst > p:par > p:cTn(nodeType=tmRoot) > p:childTnLst > [动画组...]
    不使用 p:seq 包裹，p:seq 在自动播放序列中使用。
    """
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


# ============================================================
# 主流程
# ============================================================

if os.path.exists(EXTRACT):
    shutil.rmtree(EXTRACT)
with zipfile.ZipFile(PPTX, 'r') as z:
    z.extractall(EXTRACT)

slides_dir = os.path.join(EXTRACT, 'ppt/slides')
slide_files = sorted(
    [f for f in os.listdir(slides_dir) if f.startswith('slide') and f.endswith('.xml')],
    key=lambda x: int(x.replace('slide', '').replace('.xml', ''))
)

print(f"共{len(slide_files)}页，开始添加动画...")

total_groups = 0
for sf in slide_files:
    sf_path = os.path.join(slides_dir, sf)
    with open(sf_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 shape id 和 y 坐标
    shapes = re.findall(
        r'<p:sp>.*?<p:spPr>.*?<a:xfrm>(?:.*?<a:off x="\d+" y="(\d+)".*?)?</a:xfrm>.*?</p:spPr>.*?<p:nvSpPr>.*?<p:cNvPr id="(\d+)"',
        content, re.DOTALL
    )

    shape_info = []
    for match in shapes:
        y, sid = match
        shape_info.append({'spid': int(sid), 'y': int(y)})

    if not shape_info:
        print(f"  {sf}: 无法获取shape id，跳过")
        continue

    shape_info.sort(key=lambda x: x['y'])

    # 按 y 坐标分组
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

    # 构建动画 XML
    anim_parts = []
    anim_id = 2
    for gi, group in enumerate(groups):
        direction = DIRECTIONS[gi % len(DIRECTIONS)]
        for si in group:
            anim_parts.append(make_anim_par(si['spid'], anim_id, direction))
            anim_id += 1
        total_groups += 1

    timing_str = make_timing_xml('\n'.join(anim_parts))

    # 移除旧的 timing 块并追加新 timing
    content = re.sub(r'<p:timing>.*?</p:timing>', '', content, flags=re.DOTALL)
    content = content.replace('</p:sld>', timing_str + '</p:sld>')

    with open(sf_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  {sf}: {len(shape_info)}个shape → {len(groups)}组动画")

# 重新打包
if os.path.exists(OUTPUT):
    os.remove(OUTPUT)
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zout:
    for dirpath, dirnames, filenames in os.walk(EXTRACT):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            arcname = os.path.relpath(filepath, EXTRACT)
            zout.write(filepath, arcname)

print(f"\n✅ 完成！共{total_groups}组动画")
print(f"   保存至：{OUTPUT}")
print(f"   使用：幻灯片放映模式下按空格/点击逐组触发动画")
