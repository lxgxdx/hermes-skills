---
name: neac-url-patterns
description: 国家民委 neac.gov.cn 抓取技术手册 — URL 模式、article ID 批量提取、policy interpretation 分页（2026-06-12 P16 建设实践沉淀）
type: reference
---

# 国家民委 neac.gov.cn 抓取技术手册

> 适用场景：建设民族团结、民族工作相关政策页时，从 neac.gov.cn 抓取原文、解读、案例。
> 与 references/stable-sources.md 互补——stable-sources 重点是 URL 备查表；本文重点是**抓取技术**。

---

## 一、URL 模式（2026-06-12 实测确认）

### 1.1 新闻动态类

```
https://www.neac.gov.cn/seac/xwzx/YYYYMM/NNNNNNN.shtml
```

- **YYYYMM**：6 位数字年月（如 `202605` = 2026-05）
- **NNNNNNN**：7 位数字 article ID（如 `1190361`）
- **完整例子**：
  - `https://www.neac.gov.cn/seac/xwzx/202606/1191242.shtml` — 云南红河元阳深化纪实
  - `https://www.neac.gov.cn/seac/xwzx/202605/1190361.shtml` — 第五届成都论坛
  - `https://www.neac.gov.cn/seac/xwzx/202601/1186767.shtml` — 全国民委主任会议

### 1.2 政策文件类

```
https://www.neac.gov.cn/seac/xxgk/YYYYMM/NNNNNNN.shtml
```

- 与新闻动态同模式，但位于 `/xxgk/`（公开）栏目
- **完整例子**：
  - `https://www.neac.gov.cn/seac/xxgk/202604/1189386.shtml` — 民族团结，为何需要"促进法"？
  - `https://www.neac.gov.cn/seac/xxgk/202403/1171604.shtml` — 严庆专家解读
  - `https://www.neac.gov.cn/seac/xxgk/202403/1171603.shtml` — 李安辉专家解读

### 1.3 列表栏目

| 栏目 | URL 模式 | 默认条数 | 分页参数 |
|------|----------|----------|----------|
| 新闻中心首页 | `/seac/xwzx/index.shtml` | 约 10 条最新 | 无（需 JS 翻页） |
| 公开首页 | `/seac/xxgk/index.shtml` | 约 10 条最新 | 无（需 JS 翻页） |
| **政策解读** | `/seac/xxgk/zcjd/index.shtml` | 约 10 条 | **`index_2.shtml`**（真实可用） |
| 民委动态 | `/seac/xwzx/mwdt/index.shtml` | 约 10 条 | 需 JS 翻页 |
| 地方动态 | `/seac/xwzx/dfdt/index.shtml` | 约 10 条 | 需 JS 翻页 |
| 铸牢教育 | `/seac/xxgk/2024*/...` | — | 栏目内嵌于公开首页 |

**关键发现**：**`zcjd/index_2.shtml` 真实可用**（返回历史解读）——这与 zytzb.gov.cn 统战时讯使用 `?pageNo=N` 不同的分页机制。

---

## 二、article ID 批量提取（首页 listing）

国家民委首页的 listing **是 HTML 静态渲染的**——文章链接是 `<a href="/seac/xwzx/YYYYMM/NNNNNNN.shtml">`——**用 curl + python3 一行命令即可批量提取**。

### 2.1 提取命令（python3 one-liner）

```bash
curl -sL --max-time 20 -A "Mozilla/5.0" "https://www.neac.gov.cn/seac/xwzx/index.shtml" > /tmp/neac_news.html
python3 -c "
import re
with open('/tmp/neac_news.html') as f:
    html = f.read()
pattern = r'<a[^>]+href=\"(/seac/xwzx/\d{6}/\d+\.shtml)\"[^>]*>([^<]+)</a>'
matches = re.findall(pattern, html)
for url, title in matches[:30]:
    print(f'{url}\t{title[:80]}')
"
```

**输出样例**（2026-06-12 实测）：
```
/seac/xwzx/202605/1190361.shtml	第五届铸牢中华民族共同体意识研究论坛在成都举行
/seac/xwzx/202605/1189805.shtml	"中华民族共有精神家园建设主题文化活动·河南篇"在安阳启动
/seac/xwzx/202601/1186813.shtml	第五届全国民委系统先进集体和先进个人表彰会议在京召开
/seac/xwzx/202601/1186767.shtml	全国民委主任会议在京召开
...
```

### 2.2 用于政策解读栏目

```bash
curl -sL --max-time 20 -A "Mozilla/5.0" "https://www.neac.gov.cn/seac/xxgk/zcjd/index.shtml" > /tmp/zcjd.html
python3 -c "
import re
with open('/tmp/zcjd.html') as f:
    html = f.read()
pattern = r'<a[^>]+href=\"(/seac/xxgk/[^\"]+\.shtml)\"[^>]*>([^<]+)</a>'
for url, title in re.findall(pattern, html)[:30]:
    print(f'{url}\t{title[:80]}')
"
```

### 2.3 用于政策解读分页 2

```bash
curl -sL --max-time 20 -A "Mozilla/5.0" "https://www.neac.gov.cn/seac/xxgk/zcjd/index_2.shtml" > /tmp/zcjd2.html
# 同上 python3 命令
```

**为什么这一招必学**：
- 浏览器访问 → 看到 listing → **再点击每一篇** → 太慢
- Bing 搜索 "民族团结" 返回 90% 不相关结果 → 浪费
- **curl 首页 → grep ID → 批量验证** → 5 分钟内得到 30 条高质量原文链接

---

## 三、文章正文提取（python3 脚本）

### 3.1 通用提取器

国家民委文章页是模板化的——`<div class="content">` 或类似 class 包含正文。**用正则匹配 + 多种 fallback**：

```python
# /tmp/extract_article.py
import re, sys
fname = sys.argv[1]
with open(fname) as f:
    html = f.read()
# Strip scripts and styles
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.S)

# 多种 selector 模式 fallback
patterns = [
    r'<div[^>]+class="content"[^>]*>(.*?)</div>\s*<div[^>]*footer',
    r'public_content[^>]*>(.*?)</div>\s*</div>\s*</div>\s*<div[^>]*class="footer',
    r'<div[^>]*id="content"[^>]*>(.*?)</div>\s*<div[^>]*id="footer"',
    r'<div[^>]*class="article-content"[^>]*>(.*?)</div>\s*<div',
    r'<div[^>]*class="TRS_Editor"[^>]*>(.*?)</div>\s*</div>',
    r'<div[^>]*class="main_content"[^>]*>(.*?)</div>\s*<div',
]
for p in patterns:
    m = re.search(p, html, re.S)
    if m:
        body = m.group(1)
        # Stop at related links
        body = re.split(r'(?:相关阅读|相关链接|上一篇|下一篇|编辑本段)', body, maxsplit=1)[0]
        txt = re.sub(r'<[^>]+>', ' ', body)
        txt = re.sub(r'&ensp;|&nbsp;', ' ', txt)
        txt = re.sub(r'&ldquo;|&rdquo;', '"', txt)
        txt = re.sub(r'&mdash;', '—', txt)
        txt = re.sub(r'\s+', ' ', txt).strip()
        print(txt[:8000])
        sys.exit(0)
# Fallback: find text after date marker
txt = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S)
txt = re.sub(r'<[^>]+>', ' ', txt)
txt = re.sub(r'&[a-z]+;', ' ', txt)
txt = re.sub(r'\s+', ' ', txt).strip()
# Trim to article body
m = re.search(r'\d{4}-\d{2}-\d{2}', txt)
if m:
    txt = txt[m.start():]
txt = re.split(r'(?:版权所有|相关阅读|网站地图|ICP|主办单位)', txt, maxsplit=1)[0]
print(txt[:8000])
```

### 3.2 使用方法

```bash
curl -sL --max-time 20 -A "Mozilla/5.0" "https://www.neac.gov.cn/seac/xwzx/202606/1191242.shtml" > /tmp/article1.html
python3 /tmp/extract_article.py /tmp/article1.html
# 输出 8000 字正文
```

---

## 四、3 个反爬/坑模式

### 4.1 未知 URL 默认跳首页（不要猜 URL）

```
URL: https://www.neac.gov.cn/seac/xxgk/zewj/202601/1170c0a5e7f04b1f8e0bd1c8e6b3a02e.shtml
结果: 跳转首页（title="国家民族事务委员会"）
```

**原因**：article ID 必须真实存在于数据库。**不要靠哈希/UUID 猜 URL**。

**应对**：
- 必须用第二节的"curl 首页 + grep ID"得到真实 ID
- ID 不可预测（不像 zytzb.gov.cn 旧文章 ID 连续）
- ID 范围观察：`/seac/xwzx/202601/1186813.shtml` —— 7 位数字，2026 年在 1180000-1190000 区间

### 4.2 完整文章页含大量 footer 链接（要 trim）

文章页 footer 含**所有**国务院部门、所有地方政府、所有直属单位的链接——**约 200 个链接**。如果不做 trim，python3 输出会混入这些 footer。

**应对**：用 extract_article.py 第 3 步的 `re.split(r'(?:版权所有|相关阅读|网站地图|ICP|主办单位)', txt, maxsplit=1)[0]` 截断。

### 4.3 encoding 是 UTF-8（无 GB2312 陷阱）

neac.gov.cn 是 UTF-8 编码，**无需 iconv 转换**（对比 zytzb.gov.cn 部分页面用 GB2312 需要 `iconv -f gb2312 -t utf-8//IGNORE`）。

---

## 五、与其他站点的对比（neac 的"友好度"）

| 站点 | URL 可预测 | 抓取难度 | 文章质量 | 总结 |
|------|-----------|---------|---------|------|
| **neac.gov.cn** | ✅ 模式固定 | ⭐⭐ 简单 | ⭐⭐⭐⭐ 高 | **首选**（民族工作、创建工作） |
| zytzb.gov.cn | ⚠️ 部分可预测 | ⭐⭐⭐⭐ 难 | ⭐⭐⭐⭐ 高 | 兜底用（统战综合） |
| gwytb.gov.cn | ✅ URL `t2026MM_NNN.htm` | ⭐⭐ 简单 | ⭐⭐⭐ 中 | **首选**（台湾、对台） |
| sara.gov.cn | ⚠️ 改版后 URL 不稳 | ⭐⭐⭐ 中 | ⭐⭐⭐ 中 | 宗教领域 |
| flk.npc.gov.cn | ❌ Vue SPA 渲染 | ⭐⭐⭐⭐⭐ 难 | ⭐⭐⭐⭐⭐ 极高 | **最后用**（但需 browser） |

**结论**：**neac.gov.cn 是民族工作领域的"金矿"**——抓取简单 + 内容质量高 + URL 模式稳定，**远超 Bing 搜索结果质量**。

---

## 六、cron run 中的标准动作流程

```bash
# === 步骤 1: 抓首页 listing ===
curl -sL --max-time 20 -A "Mozilla/5.0" "https://www.neac.gov.cn/seac/xwzx/index.shtml" > /tmp/neac_news.html
python3 -c "
import re
with open('/tmp/neac_news.html') as f:
    html = f.read()
pattern = r'<a[^>]+href=\"(/seac/xwzx/\d{6}/\d+\.shtml)\"[^>]*>([^<]+)</a>'
for url, title in re.findall(pattern, html)[:30]:
    print(f'{url}\t{title[:80]}')
"

# === 步骤 2: 抓政策解读 listing ===
curl -sL --max-time 20 -A "Mozilla/5.0" "https://www.neac.gov.cn/seac/xxgk/zcjd/index.shtml" > /tmp/zcjd.html
# 同上 python3 提取
curl -sL --max-time 20 -A "Mozilla/5.0" "https://www.neac.gov.cn/seac/xxgk/zcjd/index_2.shtml" > /tmp/zcjd2.html
# 同上

# === 步骤 3: 按需 curl 选中的文章 ===
for url in $(grep -oE '/seac/(xwzx|xxgk)/20[0-9]+/[0-9]+\.shtml' /tmp/neac_news.html | head -5); do
  full="https://www.neac.gov.cn$url"
  curl -sL --max-time 20 -A "Mozilla/5.0" "$full" > /tmp/article_tmp.html
  python3 /tmp/extract_article.py /tmp/article_tmp.html
  echo "---END---"
done

# === 步骤 4: 验证 URL 真实性（避免 404 写入 sources） ===
curl -sLI --max-time 5 -A "Mozilla/5.0" "https://www.neac.gov.cn/seac/xwzx/202606/1191242.shtml" | head -1
# 期望: HTTP/1.1 200 OK
```

---

## 七、与其他技能的衔接

- **references/stable-sources.md** — 互补（stable-sources 重点 URL 备查表；本文重点抓取技术）
- **references/deepen-shallow-page.md** — P16 案例就是用本文技术深化
- **references/issued-but-uninterpreted.md** — 用本文技术发现"P16 2026-01-08 印发版" 解读未发布
