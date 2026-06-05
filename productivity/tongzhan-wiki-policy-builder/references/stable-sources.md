---
name: stable-sources
description: 统战政策原文与案例的稳定访问 URL 模式（2026-06-06 经验沉淀）。中央党内法规全文转载源、政协系统案例源、Bing/中央统战部失效 URL 备查清单。
---

# 统战政策抓取 — 稳定来源备查表

> 经验沉淀自 2026-06-06 cron 任务（建设《中国共产党政治协商工作条例》页面）。
> 用途：cron 任务执行时遇到 `gov.cn / news.cn / qstheory.cn` 404 时，按本表顺序备选。

---

## 一、中央党内法规全文（中国共产党中央委员会 / 中央办公厅 / 中央统战部 / 中央台办 发布）

**特点**：`flk.npc.gov.cn` 不收录（仅收法律法规），`gov.cn/zhengce` 也不收录（仅收行政规章）。qstheory.cn / news.cn 经常 404。

**稳定源（按可靠度排序）**：

1. **地方纪委监委网站** — **最稳定**
   - 模式：`http://{city}.qinfeng.gov.cn/info/1004/xxxxx.htm` 或 `http://{city}.jjjc.gov.cn/info/...`
   - 案例：宝鸡市纪委监委 `https://baoji.qinfeng.gov.cn/info/1004/24277.htm` 完整转载《中国共产党政治协商工作条例》7章31条
   - 规律：各省地级市纪委监委几乎都转载新华社/中央纪委国家监委发布的中央党内法规
   - 发现方法：搜索"X市纪委监委 + 条例名"，命中后进站内查看完整正文

2. **地级市党报数字报** — 较稳定
   - 案例：`epaper.tibet3.com/qhrb/html/.../content_xxx.htm`（青海日报）
   - 案例：`yndaily.yunnan.cn/content/...`（云南日报）
   - **⚠️ Bing 列出的 URL 经常 404**（被源站清理）— 优先以"中央党内法规名 + 报纸名"搜索

3. **人民政协网理论时评** — 仅限政协/统战相关
   - URL 模式：`https://www.rmzxw.com.cn/{category}/content_xxx.html`
   - 站内搜索 URL 不可直接构造，必须用首页搜索框

4. **中国政协网** — 仅限政协系统
   - URL 模式：`http://www.cppcc.gov.cn/zxww/YYYY/MM/DD/ARTIxxxxxxxxxxxxxxx.shtml`
   - ⚠️ ART 数字 ID 不连续，URL 经常失效
   - 可靠途径：首页 → "权威发布"栏目按时间浏览

## 二、政协 / 统战执行案例

| 主题 | 首选源 | 备选 |
|------|--------|------|
| 政协协商实施 | 人民政协网"协商"栏目 https://www.rmzxw.com.cn/xieshang/ | 中国政协网首页"政协工作" |
| 民主党派工作 | 人民政协网"多党合作"栏目 | 中央统战部首页"统战时讯" |
| 民族团结 | 国家民委 https://www.neac.gov.cn/ | 中央统战部"各地动态" |
| 宗教工作 | 国家宗教局 http://www.sara.gov.cn/ | 中央统战部首页 |
| 工商联 | 中华工商时报 https://www.cbt.com.cn/ | 全国工商联 https://www.acfic.org.cn/ |
| 港澳台 | 国台办 https://www.gwytb.gov.cn/ | 香港中联办、澳门中联办官网 |
| 党外干部 / 统战综合 | 人民网统战频道 http://tyzx.people.cn/ | 求是网政治栏目 |

## 三、⚠️ Bing 索引但不稳定的 URL 模式（避免写入 sources）

下列模式在 Bing 搜索结果中常见但实际 404 率 >80%：
- `qstheory.cn/dukan/qs/...` （求是网旧栏目）
- `epaper.tibet3.com/qhrb/html/.../content_xxx.htm`
- `yndaily.yunnan.cn/content/YYYYMM/DD/content_xxxx.html`
- `china.com.cn/...` 部分栏目
- `cppcc.gov.cn/zxww/.../ARTI...shtml`（ART 数字过大时）

**应对**：将此类 URL 写入 sources 前必须 `curl -I --max-time 5` 验证返回 200；否则不写入，避免页面出现死链。

## 四、工具小技巧

- **Bing 搜索结果 URL 提取**：
  ```js
  Array.from(document.querySelectorAll('#b_results h2 a, a.tilk'))
    .slice(0, 15)
    .map((a, i) => `${i+1}. ${a.innerText} → ${a.href}`)
    .join('\n')
  ```
- **页面正文提取（去除 HTML）**：
  ```js
  document.body.innerText.substring(0, 8000)
  ```
- **检查 404 vs 200 快速**：
  ```bash
  curl -sLI --max-time 5 "URL" | head -1
  ```
