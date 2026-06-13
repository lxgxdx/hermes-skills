---
name: acfic-url-patterns
description: 中华全国工商业联合会 acfic.org.cn 抓取技术手册 — URL 模式、栏目结构、2026 政策速递文章批量提取、"原文不可得时用 2026 公开文件反推"策略（2026-06-14 P10 建设实践沉淀）
type: reference
---

# 中华全国工商业联合会 acfic.org.cn 抓取技术手册

> 适用场景：建设工商联所属商会改革、民营企业权益、光彩事业、商会调解等政策页时，从 acfic.org.cn 抓取原文、解读、案例。
> 与 references/neac-url-patterns.md 互补——neac 重点是民族工作；本文重点是**工商联/商会/光彩**。
> 价值等级：**金矿**——抓取简单 + 内容质量高（直接转载中央两办、中央社工部、国家网信办原文）+ URL 模式稳定。

---

## 一、URL 模式（2026-06-14 实测确认）

### 1.1 政策速递栏目（最重要）

```
https://www.acfic.org.cn/zcsd/{zy|bw|df|qggsl|jd}/YYYYMM/tYYYYMMDD_NNNNNN.html
```

| 子栏目 | 含义 | 价值 | URL 例子 |
|--------|------|------|----------|
| `zy/` | 重要（中央政策） | ⭐⭐⭐⭐⭐ 最高 | `/zcsd/zy/202606/t20260611_326872.html` |
| `jd/` | 解读（权威答记者问） | ⭐⭐⭐⭐⭐ 最高 | `/zcsd/jd/202604/t20260413_325578.html` |
| `bw/` | 部委文件 | ⭐⭐⭐⭐ 高 | `/zcsd/bw/202606/t20260612_326908.html` |
| `df/` | 地方文件 | ⭐⭐⭐ 中 | `/zcsd/df/202604/t20260413_325557.html` |
| `qggsl/` | 全国工商联 | ⭐⭐⭐ 中 | 内容少，仅头部 2-3 条 |

**关键发现**：
- `zy` 和 `jd` 栏目是**金矿**——`zy`转载中央文件（如 2026-05-20《关于用好乡镇履行职责事项清单》），`jd`转载中央两办答记者问（如 2026-04-13 行业协会商会深化改革）
- `bw` 转载国家网信办、市场监管总局等部委文件
- `df` 转载地方（省/市/县）民营经济政策

### 1.2 其他栏目

| 栏目 | URL | 价值 |
|------|-----|------|
| 新闻要闻 | `/szyw/` | ⭐⭐⭐ 工商联时政新闻 |
| 商协会调解 | `http://tiaojie.acfic.org.cn/` | ⭐⭐ 服务平台（需注册） |
| 商会服务信息化 | `https://yymhhw.acfic.org.cn/` | ⭐⭐ 信息化平台 |
| 工商联概况-章程 | `/bhjj/gk/zc/` | ⭐ 工商联章程转载 |
| 工商联概况-简介 | `/bhjj/gk/jj/` | ⭐ |
| 全国工商联两会专题 | `/ztzlhz/2hui2026/` | ⭐⭐⭐ 每年 3 月更新 |

### 1.3 ⚠️ 分页参数 `?pageNo=N` 对 ACFIC **不工作**（与 neac.gov.cn 相反）

- neac.gov.cn：`/seac/xxgk/zcjd/index_2.shtml` **真实可用**
- acfic.org.cn：`/zcsd/zy/?pageNo=2` **页面无效**（仍是首页 16 条）
- **应对**：依赖首页默认 16 条，**不依赖分页**——若需更多历史文章，可换中央两办或中社部官网

### 1.4 编码是 UTF-8（**无 GB2312 陷阱**）

acfic.org.cn 是 UTF-8 编码，**无需 iconv 转换**（与 zytzb.gov.cn 部分页面需 `iconv -f gb2312 -t utf-8//IGNORE` 相反）。

---

## 二、政策速递 listing 批量提取

### 2.1 抓首页 listing 的 4 行 curl + python3

```bash
curl -sL --max-time 30 -A "Mozilla/5.0" "https://www.acfic.org.cn/zcsd/zy/" > /tmp/acfic_zy.html
python3 -c "
import re
with open('/tmp/acfic_zy.html') as f:
    html = f.read()
pattern = r'<a[^>]+href=\"(\./[0-9]+/[0-9]+/t[0-9]+_[0-9]+\.html)\"[^>]*>([^<]+)</a>'
for url, title in re.findall(pattern, html)[:30]:
    print(f'{url}\t{title[:80]}')
"
```

**输出样例**（2026-06-14 实测）：
```
./202606/t20260611_326872.html	国务院关于对外投资的规定
./202606/t20260601_326519.html	关于开展"清朗·优化营商网络环境 整治恶意炒作涉企信息"专项行动的通知
./202605/t20260520_326236.html	中共中央办公厅、国务院办公厅印发《关于用好乡镇（街道）履行职责事项清单的具体措施》
./202605/t20260508_325982.html	中共中央办公厅 国务院办公厅印发《美丽中国建设成效考核办法》
```

**注意**：URL 是**相对路径**（`./202606/...`）——使用前需补 `https://www.acfic.org.cn/zcsd/zy/` 前缀。

### 2.2 找"商会"主题文章的精准策略

```bash
# 步骤 1: 抓所有 4 个政策速递子栏目
for sub in zy bw df jd; do
  curl -sL --max-time 30 -A "Mozilla/5.0" "https://www.acfic.org.cn/zcsd/${sub}/" > /tmp/acfic_${sub}.html
done

# 步骤 2: 提取 + 筛"商会"关键词 + 取标题
python3 << 'EOF'
import re, glob
for f in sorted(glob.glob('/tmp/acfic_*.html')):
    with open(f) as fh: html = fh.read()
    pattern = r'<a[^>]+href="(\./[0-9]+/[0-9]+/t[0-9]+_[0-9]+\.html)"[^>]*>([^<]+)</a>'
    for url, title in re.findall(pattern, html):
        if '商会' in title or '工商联' in title or '民营' in title:
            print(f'{f}\t{url}\t{title[:80]}')
EOF
```

### 2.3 验证 URL 真实性（避免 404 写入 sources）

```bash
# 批量 HEAD 验证
for url in \
  "https://www.acfic.org.cn/zcsd/jd/202604/t20260413_325578.html" \
  "https://www.acfic.org.cn/zcsd/bw/202606/t20260612_326908.html"; do
  code=$(curl -sL -A "Mozilla/5.0" -o /dev/null -w "%{http_code}" --max-time 15 "$url")
  echo "$code $url"
done
# 全部 200 才写入 sources
```

---

## 三、文章正文提取（python3 脚本）

### 3.1 ACFIC 文章页结构

ACFIC 文章页是模板化的——`<div class="content">` 包含正文，**没有 JS 渲染**（**与 neac.gov.cn 一样是静态 HTML**），可 curl 拿到全部正文。

```python
# /tmp/extract_acfic.py
import re, sys
fname = sys.argv[1]
with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()
# Strip scripts and styles
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.S)

# ACFIC 模式
patterns = [
    r'<div[^>]+class="content"[^>]*>(.*)',  # 最常见
    r'<div[^>]+class="public_content"[^>]*>(.*)',
    r'<div[^>]+id="content"[^>]*>(.*)',
]
for p in patterns:
    m = re.search(p, html, re.S)
    if m:
        body = m.group(1)
        # 截断到 相关链接/附件下载
        body = re.split(r'(?:相关链接|附件下载|关于我们|ICP)', body, maxsplit=1)[0]
        txt = re.sub(r'<[^>]+>', '\n', body)
        txt = re.sub(r'\n+', '\n', txt)
        txt = re.sub(r'&nbsp;', ' ', txt)
        txt = re.sub(r'&ldquo;|&rdquo;', '"', txt)
        txt = re.sub(r'&mdash;', '—', txt)
        sys.stdout.write(txt.strip())
        sys.exit(0)
print('[ERROR] no content div found')
```

### 3.2 使用方法

```bash
curl -sL --max-time 30 -A "Mozilla/5.0" "https://www.acfic.org.cn/zcsd/jd/202604/t20260413_325578.html" > /tmp/jd.html
python3 /tmp/extract_acfic.py /tmp/jd.html > /tmp/jd.txt
wc -c /tmp/jd.txt
# 7000+ 字
```

### 3.3 ⚠️ 输出到文件而非 stdout 的小技巧

某些 Python 输出通过 stdout 在 cron 环境可能被截断或吞掉——**先 `> file.txt` 再 `cat` 或 `head`** 比 `python3 script.py` 直接打印更稳。

```bash
python3 /tmp/extract_acfic.py /tmp/jd.html > /tmp/jd.txt 2>&1
head -50 /tmp/jd.txt
```

---

## 四、"原文不可得时用 2026 公开文件反推"策略（2026-06-14 P10 实践沉淀）

> **适用场景**：要建设的政策是 2018 或更早文件，**原 URL 在 zytzb.gov.cn 等旧站点 404**，**Bing CN 搜索对历史长尾关键词失效**，但**有 2026 年后继文件**。

### 4.1 策略核心

不直接抓历史原文——**抓 2026 后继/相关文件的权威解读**，从解读中**反推历史文件**的：

1. **政策谱系**（"党的十八届三中全会-二十大-二十届三中-二十届四中"）
2. **历史问题**（"老问题、新挑战""亟需结合新形势新任务加以健全完善"）
3. **新增条款对应的历史空白**（8 大新增对应 8 大执行空白）
4. **直接引用的历史文件片段**（如"机构、职能、资产财务、人员管理、党建、涉外交流与合作"6 类事项）

### 4.2 真实案例：P10（2018）→ 2026-04-13 解读

**P10（2018）《关于促进工商联所属商会改革和发展的实施意见》原文不可得**：
- zytzb.gov.cn 旧 URL 全部 404
- Bing CN 搜索"工商联 商会改革 实施意见 2018"返回 404/无关注册局链接

**找到的反推材料**：
- **2026-04-13 中央两办《关于推动行业协会商会深化改革的意见》答记者问**（acfic.org.cn `/zcsd/jd/202604/t20260413_325578.html`）
- 9 问 9 答全文 7000+ 字，**100% 抓取成功**

**反推出的 P10 关键信息**：
1. **政策定位**："行业协会商会" 是 P10（"工商联所属商会"）的**覆盖范围升级版**——P10 仅覆盖 5 万家，2026 新版覆盖 70+ 万家
2. **历史问题官方承认**："仍处于脱钩改革后的转型调整期……在党建引领、综合监管、内部治理、结构布局、作用发挥等方面还存在不少老问题、新挑战"
3. **P10 14 大执行空白** = 2026 新版 14 大新增条款（管行业也要管党建/5 环节人事制度/行业管理部门明确/分类管理/退出制度/第三方监督/分支管理/收费规范/资产管理/国际合作/从业人员培养评价等）
4. **P10 体系性缺位** = 8 年后被中央两办意见替代（部门级 → 中央级）

### 4.3 策略的 3 步操作

```bash
# 步骤 1: 找后继/相关 2026 解读文件
# 在 acfic.org.cn/zcsd/{zy,jd,bw}/ 找 2026 答记者问
# 关键词：与目标政策同一领域 + 2026 + "答记者问" / "解读"

# 步骤 2: 抓取 + 提取全文（用 3.1 的 python3 脚本）

# 步骤 3: 从解读中提取 5 类信息
# (a) 政策谱系（"党的XX大-XX届X中全会"系列）
# (b) "老问题/新挑战" 段（直接引用 = 历史问题证据）
# (c) "亟需/亟待/应当/新增/健全/完善" 动词后面的内容（= 补漏方向）
# (d) 新旧对比表（"原 P10 4 部分 → 2026 新版 7 部分 18 条"）
# (e) 政策评价（"是 P10 的升级版" 之类官方表述）
```

### 4.4 适用边界

- ✅ **适合**：有 2026 后继/相关文件，**P10 等 2018 老政策**
- ✅ **适合**：政策在脱钩改革、双碳、营商环境、共同富裕等 2026 重点议题中
- ❌ **不适合**：纯学术性历史文件（无 2026 后继）
- ❌ **不适合**：试行版/暂行版（< 2 年前生效），**直接抓原文** 即可

---

## 五、与其他站点的对比（ACFIC 的"金矿"地位）

| 站点 | URL 可预测 | 抓取难度 | 文章质量 | 2026 后继文件 | 总结 |
|------|-----------|---------|---------|-------------|------|
| **acfic.org.cn** | ✅ 模式固定 | ⭐⭐ 简单 | ⭐⭐⭐⭐⭐ 极高 | ✅ 中央两办意见多转载 | **金矿**（工商联/商会/光彩首选） |
| neac.gov.cn | ✅ 模式固定 | ⭐⭐ 简单 | ⭐⭐⭐⭐ 高 | ⚠️ 部分转载 | 民族工作首选 |
| zytzb.gov.cn | ⚠️ 部分可预测 | ⭐⭐⭐⭐ 难 | ⭐⭐⭐⭐ 高 | ⚠️ JS 渲染 | 统战综合兜底 |
| gwytb.gov.cn | ✅ URL `t2026MM_NNN.htm` | ⭐⭐ 简单 | ⭐⭐⭐ 中 | ✅ 地方动态 | 台湾/对台首选 |
| sara.gov.cn | ⚠️ 改版后 URL 不稳 | ⭐⭐⭐ 中 | ⭐⭐⭐ 中 | ❌ | 宗教领域 |
| flk.npc.gov.cn | ❌ Vue SPA 渲染 | ⭐⭐⭐⭐⭐ 难 | ⭐⭐⭐⭐⭐ 极高 | ✅ | 法律法规全文（最后用） |

**结论**：**acfic.org.cn 是工商联/商会/光彩领域的"金矿"**——抓取简单 + 内容质量极高（直接转载中央两办原文） + URL 模式稳定 + 2026 后继文件覆盖全。

---

## 六、cron run 中的标准动作流程

```bash
# === 步骤 1: 抓 4 个政策速递子栏目 ===
for sub in zy bw df jd; do
  curl -sL --max-time 30 -A "Mozilla/5.0" "https://www.acfic.org.cn/zcsd/${sub}/" > /tmp/acfic_${sub}.html
done

# === 步骤 2: 批量提取 + 关键词筛选 ===
python3 << 'EOF'
import re, glob
for f in sorted(glob.glob('/tmp/acfic_*.html')):
    with open(f) as fh: html = fh.read()
    pattern = r'<a[^>]+href="(\./[0-9]+/[0-9]+/t[0-9]+_[0-9]+\.html)"[^>]*>([^<]+)</a>'
    for url, title in re.findall(pattern, html):
        # 替换 . 为完整 URL
        full_url = f.replace('/tmp/acfic_', 'https://www.acfic.org.cn/zcsd/').replace('.html', '/') + url.lstrip('./')
        print(f'{full_url}\t{title[:80]}')
EOF

# === 步骤 3: 按需 curl 选中的文章 + 提取正文 ===
for url in $(... 筛选出的 URL 列表 ...); do
  fname="/tmp/art_$(basename $url)"
  curl -sL --max-time 30 -A "Mozilla/5.0" "$url" > "$fname"
  python3 /tmp/extract_acfic.py "$fname" > "${fname%.html}.txt"
done

# === 步骤 4: 验证 URL 真实性（避免 404 写入 sources） ===
for url in $(... 候选 URL ...); do
  code=$(curl -sL -A "Mozilla/5.0" -o /dev/null -w "%{http_code}" --max-time 15 "$url")
  [ "$code" = "200" ] && echo "OK $url" || echo "FAIL $code $url"
done
```

---

## 七、与其他技能的衔接

- **references/neac-url-patterns.md** — 镜像结构（民族工作领域）；acfic 与 neac 的对比见第 5 节
- **references/stable-sources.md** — 互补（stable-sources 重点 URL 备查表；本文重点抓取技术）
- **references/deepen-shallow-page.md** — P10 案例就是用本文技术深化（"2026 反推" 策略详见第四节）
- **references/non-public-inner-party-docs.md** — "原文不可得" 的另一条处理路径（中央两办 / 中办文件路径）
- **本 skill 主体 SKILL.md** — ACFIC 应加入第 2 步的"来源优先级"表（参考 SKILL.md 第 33 行表格）
