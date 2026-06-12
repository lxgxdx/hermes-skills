---
title: urllib + HTMLParser 抓取 JS 渲染的中国政府站
created: 2026-06-13
type: reference
tags: [scraping, zytzb, gov.cn, js-rendered, urllib, htmlparser]
---

# urllib + HTMLParser 抓取 JS 渲染的中国政府站

> **场景**：cron 环境网络受限，`browser_navigate` 抓到的页面快照（`browser_snapshot`）只显示导航栏/弹窗元素，**文章正文没有出现在 snapshot 里**——因为正文是通过 JS/AJAX 异步加载的。
> **典型站点**：`zytzb.gov.cn`（中央统战部）、其他中国党/政/机关站。
> **替代工具**：不用浏览器、纯 Python 抓正文。

---

## 核心技巧

`zytzb.gov.cn` 的文章页（如 `https://www.zytzb.gov.cn/zytzb/2026-05/21/article_2026052108270127463.shtml`）用 `urllib` 抓到的 HTML 包含**全部文章正文**——但**没有 `<p>` 标签包裹**（段落被 `&emsp;` + 换行符分隔）。这意味着：

- `curl | grep '<p>'` 抓不到正文
- `curl | sed 's/<[^>]*>//g'` 抓到正文（连同导航栏和 CSS 一起）
- **唯一干净的解法**：`urllib` + `HTMLParser` 解码全部文本，然后用关键词锚点定位正文

## 完整工作脚本（可复制修改）

```python
import urllib.request, re, sys
from html.parser import HTMLParser

class BodyExtractor(HTMLParser):
    """提取 <body> 内全部可见文本，跳过 <script>/<style> 等。"""
    def __init__(self):
        super().__init__()
        self.txt = []
        self.skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ('p','br','div','h1','h2','h3','li','tr','td','section','article'):
            self.txt.append('\n')
        if tag in ('script','style','nav','header','footer'):
            self.skip = True
    def handle_endtag(self, tag):
        if tag in ('script','style','nav','header','footer'):
            self.skip = False
    def handle_data(self, d):
        if not self.skip:
            self.txt.append(d)

def fetch_body(url, anchor_markers=None, end_markers=None,
               head_chars=200, tail_chars=4000):
    """抓 URL → 提取 body → 用锚点定位 → 返回正文片段。

    Args:
        url: 文章 URL
        anchor_markers: 用于定位正文起点的关键词列表（如 ['5月20日', '近日', '李干杰']）
        end_markers: 用于定位正文终点的关键词列表（如 ['ICP', '版权所有', '网站地图']）
        head_chars: 锚点前保留多少字符（上下文）
        tail_chars: 终点后保留多少字符（最大正文长度）
    """
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
    })
    data = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'ignore')

    p = BodyExtractor()
    p.feed(data)
    out = ''.join(p.txt)
    out = re.sub(r'\n+', '\n', out).strip()

    if anchor_markers:
        for m in anchor_markers:
            i = out.find(m)
            if i > 0:
                start = max(0, i - head_chars)
                out = out[start:]
                break

    if end_markers:
        end_idx = len(out)
        for m in end_markers:
            j = out.find(m, 500)
            if 0 < j < end_idx:
                end_idx = j
        out = out[:end_idx]

    return out.strip()[:tail_chars]


# 实战示例：抓 zytzb 2026-05-20 李干杰讲话
if __name__ == '__main__':
    body = fetch_body(
        "https://www.zytzb.gov.cn/zytzb/2026-05/21/article_2026052108270127463.shtml",
        anchor_markers=['5月20日', '近日', '李干杰'],
        end_markers=['ICP', '版权所有', '网站地图', '国家宗教事务局', '国务院侨务办公室'],
    )
    print(body)
```

**实测 2026-06-13**：成功抓取 zytzb 两篇 2026 年中央层面原文——

- 2026-04-22 党外人士形势政策报告会（约 1100 字正文）
- 2026-05-20 李干杰讲话（约 900 字正文）

## 为什么 browser_navigate 失败但 urllib 成功

| 工具 | 抓 zytzb 的结果 | 原因 |
|------|---------------|------|
| `browser_navigate` | 返回页面，snapshot 只有导航栏 | browser 渲染了 DOM 树但 snapshot 截不到 JS 异步加载的内容（依赖 `easysite` CMS 的 JS） |
| `urllib` | 静态 HTML 包含全文 | zytzb 的文章内容在 `<div class="dhyw">` 静态 HTML 中，**依赖 JS 渲染的是样式/导航**——内容在静态 HTML 里就有 |

**关键洞察**：很多中国党/政/机关站是"**内容静态 + 样式 JS**"的混合模式——内容为了 SEO 已静态化，但页面框架依赖 JS。所以 `urllib` 直接抓到全部正文。

## 适用站点判断

**直接试 `urllib` 抓正文即可**，如果以下信号都符合，大概率成功：
- 文章 URL 模式稳定（不是 `?id=xxx` 这种纯参数化）
- 页面在 Bing 索引中能搜到（说明有静态内容）
- 用 `curl -sL` 返回的 HTML body 部分超过 30KB（含内容）
- 没有 Cloudflare/JS challenge 弹窗

**典型适用站**：
- ✅ `zytzb.gov.cn`（中央统战部）—— 2026-06-13 验证
- ✅ `sara.gov.cn`（国家宗教局）—— 大概率适用，未验证
- ✅ `gwytb.gov.cn`（国台办）—— 已知适用（参考其他 cron session）
- ✅ `neac.gov.cn`（国家民委）—— 已知适用（详见 neac-url-patterns.md）
- ✅ `gov.cn/zhengce`（国务院政策文件库）—— 已知适用
- ❓ 大型商业新闻站（新华网、人民网）—— 静态 HTML + 段落多，`urllib` 也能抓但需要更多过滤

## 关键避坑

1. **headers 必须伪装**：
   ```python
   headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'}
   ```
   否则部分站会返回 403/空白。

2. **超时设 25 秒**——zytzb 等站点在 cron 环境首次访问较慢。

3. **解码用 `decode('utf-8', 'ignore')`**——避免个别字节乱码卡住整个流程。

4. **锚点用 `out.find(m) > 0`**——必须严格大于 0，避免返回位置 0（首字符）的假命中。

5. **终末标记用相对偏移**——`out.find(m, 500)` 表示从第 500 字符开始找，避免误命中正文中的相同词。

## 与现有技术的配合

- **与 `browser_navigate` 的关系**：`browser_navigate` 适合"看页面长啥样 / 找 URL 模式"，`urllib` 适合"批量抓正文"。**先用 browser 看 1-2 个页面摸清 URL 模式，再用 urllib 批量抓。**
- **与 neac-url-patterns.md 配合**：本文提供"如何抓正文"，neac-url-patterns.md 提供"neac 站点的 URL 模式"。两者叠加覆盖大多数政府站。
- **与 `requests` 库的对比**：`urllib` 是标准库无需安装，`requests` 第三方但 API 更友好。在 cron 环境优先用 `urllib`（减少 venv 依赖）。

## 真实使用案例

**2026-06-13 P14 山东实施细则深化**：

- **目标**：找 2026 年中央层面真实案例来反证 P14 实施细则
- **过程**：
  1. Bing 搜 5 次都返回通用结果（已记录在 SKILL.md "Bing 语义污染" 章节）
  2. `browser_navigate` 抓 zytzb 2026-05-20 页面 → snapshot 全文不可见（JS 弹窗遮挡）
  3. **切换到 `urllib` 抓静态 HTML** → 用 `BodyExtractor` 解析 → 锚点定位"5月20日" → 提取全部正文
  4. 同样方法抓 2026-04-22 党外人士形势政策报告会
- **产出**：
  - `raw/shandong-implementation-deepening-2026-06-13.md`（含 2 篇原文摘录）
  - `entities/policy-shandong-tongzhan.md` 重建（2.0KB → 22KB）

## 后续可拓展

- **加批量抓取**：从首页 listing 提取所有文章 URL → 循环调用 `fetch_body` → 写入 raw 摘要
- **加 changelog 监控**：每个政策页关联的 zytzb 文章 URL 列表，每 N 天重新 `fetch_body` 比对正文是否变化
- **加失败重试**：`urllib.request.urlopen` 失败时重试 3 次（指数退避）

---

## 附录：与"党内规范性文件原文不公开"模式的稳定信号对

`non-public-inner-party-docs.md` 记录了"原文不公开但讲话反推"的 6 步处理法。**2026-06-13 验证**：同一对 2026 年中央信号可同时反证 P12（双管理层级）和 P14（省级实施细则）——**信号密度高、跨政策页适用**：

| 文章 | 关键信号 | P12 反推 | P14 反推 |
|------|---------|---------|---------|
| 2026-04-22 党外人士形势政策报告会（总第6期）| 中央层面已制度化（3-4期/年），出席范围仅"在京" | 印证"双重管理"在中央层面仍运作 | 印证 P14 实施细则在"思想政治引领"环节缺量化指标、基层覆盖盲点 |
| 2026-05-20 李干杰讲话 | "近期中共中央印发有关文件"对党外代表人士选育管用作出系统部署，**但文件全文未公开**；"管理监督的针对性实效性"；"党的领导贯穿全过程" | 反证《意见》原文存在但未公开 | 反证 P14 在"管理监督"环节缺配套程序 + "央地时差"导致 P14 修订受阻 + 无党派代表人士覆盖盲点 |

**实战意义**：
- 未来如果 P12 / P14 都需要更新"近期中央信号"小节，**先看 zytzb 的"统战时讯"栏目最新 5 条**——大概率会有可引用的新信号
- 抓取方法见上文完整脚本
