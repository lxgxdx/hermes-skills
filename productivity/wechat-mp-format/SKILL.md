---
name: wechat-mp-format
description: >-
  微信公众号文章排版与发布完整工作流。将 Markdown 内容转换为微信兼容的内联样式 HTML，
  生成封面图，并发布到公众号草稿箱。触发词：公众号排版/发布公众号/微信排版/公众号样式/把文章发到公众号。
tags: [wechat, mp, 公众号, 排版, html, publish]
category: productivity
---

# 微信公众号排版与发布专家

This skill positions the Agent as a senior WeChat article formatting engineer who transforms
Markdown content into WeChat-compatible HTML and publishes to the official account draft box.

Core philosophy: **排版即内容，样式即品牌** — Every formatting decision serves readability and brand identity.

---

## Scope

✅ **Applicable**:
- 将 Markdown 文章转换为微信兼容的 HTML
- 根据风格描述（科技风/活力风/政务风）生成对应排版
- 生成封面图（900×383）
- 发布到公众号草稿箱

❌ **Not applicable**:
- 微信后台直接编辑（用官方编辑器更方便）
- 订阅号不支持的 API 功能（需手动发布）
- 复杂交互页面（微信不支持）

---

## Workflow

### Step 1: 获取文章内容和风格

用户提供了文章内容后，确认：

| 场景 | 操作 |
|------|------|
| 提供了 Markdown 文件路径 | 直接读取文件 |
| 提供了文章主题/要点 | 先用 LLM 生成完整 Markdown，再转换 |
| 明确说了风格（活力橙/科技风/政务风） | 按风格生成 |
| 没有说风格 | 询问：需要哪种视觉风格？ |

**风格选项**（直接选，不用逐个问）：
- **活力政务风**：深蓝 #1E3A5F + 活力橙 #FF6B35 + 金黄 #FFD23F（用户偏好）
- **简约专业风**：白底 + 灰黑文字 + 蓝色强调
- **人文温暖风**：米黄底 #fdf6e3 + 棕色强调
- **科技深色风**：深蓝黑底 + 霓虹色文字

### Step 2: 声明设计方向

在动手之前，先向用户确认：

```
文章标题：[标题]
风格：[活力政务风 / 其他]
主要配色：[强调色]
封面主标题：[6-10字提炼]
```

用户确认后再生成，避免返工。

### Step 3: Markdown → 微信兼容 HTML

**核心原则**：微信会大幅剥离 HTML/CSS，所有样式必须内联。

#### 3.1 CSS 白名单（仅这些属性可用）

| 类别 | 可用属性 |
|------|---------|
| 颜色/背景 | `color`, `background-color`（仅纯色 #hex，**不支持 rgba/gradient**） |
| 字体 | `font-size`, `font-weight`, `font-style`, `letter-spacing` |
| 对齐 | `text-align`, `text-decoration`, `text-indent`, `vertical-align` |
| 间距 | `margin`, `padding`, `line-height` |
| 边框 | `border`, `border-left/right/top/bottom`（solid/dashed/dotted） |
| 布局 | `display: block/inline/inline-block`, `width`, `height`, `max-width` |

#### 3.2 CSS 黑名单（必定被删除）

- `position: absolute/relative/fixed` — 全删
- `float`, `z-index` — 删除
- `box-shadow`, `border-radius` — 删除
- `background-image`, `linear-gradient()`, `radial-gradient()` — 删除
- `rgba()` 颜色 — 改用 #hex
- `transform`, `animation`, `transition` — 删除
- `::before` / `::after` — 不可能使用

#### 3.3 HTML 标签限制

| 标签 | 问题 | 替代方案 |
|------|------|---------|
| `<style>` | 被完全删除 | 内联 `style="..."` |
| `<ol>`, `<ul>`, `<li>` | 微信覆盖 list-style，序号丢失 | 用 `<p>` + 显式序号/符号 |

#### 3.4 装饰字符（替代 CSS 效果）

| 想要效果 | 不能用 | 用这个 |
|---------|--------|--------|
| 波浪下划线 | `background-image: url(svg...)` | Unicode `〰〰〰〰` |
| 荧光高亮 | `linear-gradient` | 纯色 `background-color: #fff176` |
| 竖条装饰 | `::before` + gradient | `border-left: 5px solid #ffeb3b` |
| 分割线 | SVG wave | 字符 `· · · ✦ · · ·` |
| 图标前缀 | `::before { content: "✦" }` | HTML 直接写 `✦` |

**可用装饰字符**：`✦` `〰` `◦` `✎` `📝` `💡` `✏️` `⭐` `·` `—` `↓` `🔥`

### Step 4: 各元素转换规范

#### 标题

```html
<!-- h1 标题 -->
<h1 style="text-align:center;font-size:1.65em;font-weight:900;color:#2c2c2c;
    letter-spacing:1px;margin:1.2em 0 0.4em;padding:12px 20px;">
  ✦ 标题文字
</h1>
<p style="text-align:center;font-size:15px;color:#e06060;
    letter-spacing:4px;margin:0 0 1em 0;">〰〰〰〰〰〰〰〰〰〰</p>

<!-- h2 标题 -->
<h2 style="font-size:1.3em;font-weight:700;color:#1E3A5F;
    margin:1.8em 0 0.4em;padding:6px 0 6px 12px;
    border-left:5px solid #FF6B35;">标题文字</h2>
<p style="border-bottom:2px dashed #FFD23F;margin:0 0 0.8em 0;
    height:0;font-size:0;line-height:0;overflow:hidden;">-</p>

<!-- h3 标题 -->
<h3 style="font-size:1.15em;font-weight:600;color:#4a6a5a;
    margin:1.4em 0 0.5em;padding-left:4px;">✎ 标题文字</h3>
```

#### 段落

```html
<p style="letter-spacing:0.5px;line-height:1.9;margin:0.8em 0;color:#3a3a3a;">
  段落文字内容...
</p>
```

#### 列表（绝不用 ol/ul/li）

```html
<!-- 无序列表 -->
<p style="padding-left:24px;margin:0.35em 0;line-height:1.8;
    letter-spacing:0.5px;color:#3a3a3a;">
  <span style="color:#FF6B35;">◦</span> 列表项内容
</p>

<!-- 有序列表 -->
<p style="padding-left:24px;margin:0.35em 0;line-height:1.8;
    letter-spacing:0.5px;color:#3a3a3a;">
  <strong style="color:#1E3A5F;font-weight:700;">1.</strong> 第一项内容
</p>
```

#### 表格

```html
<table style="border-collapse:collapse;margin:1.4em auto;max-width:100%;
    text-align:left;font-size:15px;border:2px solid #1E3A5F;">
  <thead>
    <tr>
      <th style="background-color:#1E3A5F;color:#ffffff;font-weight:700;
          padding:10px 14px;border-bottom:2px solid #1E3A5F;text-align:center;">
        列名
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding:9px 14px;border-bottom:1px dashed #FFD23F;
          color:#4a4a4a;vertical-align:top;line-height:1.6;">内容</td>
    </tr>
  </tbody>
</table>
```

#### 引用块

```html
<blockquote style="background-color:#fff9c4;border-left:4px solid #FF6B35;
    margin:1.5em 0;padding:12px 16px;font-size:15px;color:#5d4e37;">
  <p style="margin:0 0 6px 0;font-size:0.85em;">💡</p>
  <p style="margin:4px 0;letter-spacing:0.5px;line-height:1.9;color:#5d4e37;">
    引用文字内容
  </p>
</blockquote>
```

#### 代码块（不用 code 整段）

```html
<section style="border:2px dashed #1E3A5F;margin:1.4em 0;padding:20px 16px 16px;
    font-size:13px;line-height:1.65;overflow-x:auto;background-color:#f5f5f5;">
  <p style="font-size:13px;color:#1E3A5F;font-weight:700;margin:0 0 8px 0;">CODE</p>
  <p style="margin:0 0 4px 0;line-height:1.65;word-wrap:break-word;">
    <code style="color:#c0392b;font-size:13px;">第一行代码</code>
  </p>
  <p style="margin:0 0 4px 0;line-height:1.65;word-wrap:break-word;">
    <code style="color:#c0392b;font-size:13px;">&nbsp;&nbsp;缩进行代码</code>
  </p>
</section>
```

**代码块规则**：
1. `<`, `>`, `&` 必须转义为 `&lt;`, `&gt;`, `&amp;`
2. 缩进空格转成 `&nbsp;`
3. 空行转成只含 `&nbsp;` 的行

#### 行内格式

```html
<strong style="color:#2c2c2c;font-weight:700;border-bottom:2px solid #FF6B35;
    padding-bottom:1px;">加粗强调</strong>

<em style="background-color:#FFD23F;font-style:normal;padding:0 3px;">高亮文字</em>

<code style="color:#c0392b;background-color:#fef9e7;padding:2px 6px;font-size:14px;
    border-bottom:1px dotted #c0392b;">行内代码</code>

<a href="URL" style="color:#1E3A5F;text-decoration:none;
    border-bottom:1px dashed #1E3A5F;">超链接</a>
```

#### 分割线

```html
<p style="text-align:center;margin:2em 0;color:#b8a88a;
    font-size:15px;letter-spacing:6px;">· · · ✦ · · ·</p>
```

### Step 5: 封面图生成

封面尺寸：**900×383**（比例约 2.35:1）

**设计原则**：
1. 主标题提炼为 **6-10 个中文字符**，字号建议 64-76px
2. 主体居中，占画面中部 60-75%
3. 字号要足够大，缩到公众号卡片后仍能辨认
4. 使用 PIL 加载中文字体（自动遍历系统字体路径）

**活力政务风配色封面**：
- 底色：深蓝渐变 #1E3A5F → #0d1f3c
- 标题：白色/金黄 #FFD23F
- 装饰：橙色 #FF6B35 线条

```python
from PIL import Image, ImageDraw, ImageFont
import os

def generate_cover(text, subtitle="", output_path="/tmp/wechat_cover.png"):
    img = Image.new('RGB', (900, 383), '#1E3A5F')
    draw = ImageDraw.Draw(img)
    
    # 找中文字体
    font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
    ]
    font_main = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_main = ImageFont.truetype(fp, 72)
                break
            except:
                continue
    
    if font_main is None:
        font_main = ImageFont.load_default()
    
    # 绘制主标题（居中）
    bbox = draw.textbbox((0, 0), text, font=font_main)
    text_w = bbox[2] - bbox[0]
    x = (900 - text_w) // 2
    draw.text((x, 130), text, fill='#FFD23F', font=font_main)
    
    # 副标题
    if subtitle:
        font_sub = ImageFont.truetype(font_main.path, 36) if hasattr(font_main, 'path') else font_main
        draw.text((450 - 100, 220), subtitle, fill='#ffffff', font=font_sub)
    
    # 装饰线
    draw.rectangle([50, 300, 850, 305], fill='#FF6B35')
    
    img.save(output_path, 'PNG')
    return output_path
```

### Step 6: 发布到公众号草稿箱

#### 6.1 凭证配置（一次性）

用户需要提供微信 AppID 和 AppSecret，存入：

```
~/.wechat/config
WECHAT_APPID=wxXXXXXXXXXXXXXXXX
WECHAT_APPSECRET=***************
```

**安全提醒**：对话中出现 AppSecret 时，发布后提醒用户去公众平台重置。

#### 6.2 发布流程

```
[1] 读取 Markdown → [2] 转换 HTML → [3] 兼容性检查 → [4] 生成封面 → [5] 获取 token → [6] 上传封面 → [7] 创建草稿
```

**获取 access_token**：
```
GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}
```

**上传封面**：
```
POST https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={TOKEN}&type=image
Content-Type: multipart/form-data
```

**创建草稿**：
```json
POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token={TOKEN}
{
  "articles": [{
    "title": "标题",
    "author": "作者",
    "digest": "摘要",
    "content": "HTML内容（全部内联样式）",
    "thumb_media_id": "封面的media_id",
    "content_source_url": "",
    "need_open_comment": 0,
    "only_fans_can_comment": 0
  }]
}
```

#### 6.3 错误码处理

| errcode | 含义 | 处理 |
|---------|------|------|
| 40164 | IP 不在白名单 | 用 `curl ifconfig.me` 获取出口 IP，去公众号后台添加白名单 |
| 40007 | 缺少 thumb_media_id | 检查封面上传是否成功 |
| 48001 | API 未授权（订阅号） | 手动去草稿箱发布 |
| 40001 | token 过期 | 重新获取 |

---

## 模板学习能力

用户可以发送任意参考模板（截图、链接、或直接发公众号文章 URL），我会分析其风格特征并复现。无需手动描述风格，发送模板即可。

**使用流程**：
1. 用户发送模板
2. 我分析风格：配色、字体、间距、装饰元素、布局特点
3. 按分析结果生成对应排版

## 预置主题速查

### 活力政务风（用户偏好）

```css
/* 配色 */
底色: #ffffff
主文字: #2c2c2c
h2: #1E3A5F + #FF6B35 左边框
h3: #4a6a5a
强调色: #FF6B35, #FFD23F
引用块: #fff9c4 底 + #FF6B35 左边框
表格表头: #1E3A5F 底 + 白字
代码块: #f5f5f5 底 + #1E3A5F 虚线边框
装饰字符: ✦ 〰 ◦ 💡
```

### 科技深色风

```css
底色: #0d1f3c
主文字: #d7e8ff
h1/h2: #00f5ff（霓虹青）
强调色: #ff2bd6, #39ff14, #ffea00
引用块: #1a2a4a 底 + #00f5ff 左边框
代码块: #090b1a 底 + #00f5ff 虚线边框
```

---

## Pre-delivery Checklist

- [ ] 全部样式内联，无 `<style>` 标签
- [ ] 未使用 `position`、`box-shadow`、`border-radius`、`linear-gradient`、`rgba()`
- [ ] 未使用 `<ol>`、`<ul>`、`<li>`，列表用 `<p>` + 显式符号
- [ ] 装饰全用 Unicode 字符（✦ 〰 ◦ 💡），不用伪元素
- [ ] 表格表头和 body 不同底色
- [ ] 代码块逐行渲染，`<` `>` `&` 已转义
- [ ] 封面图主标题字号 ≥ 64px，中文字体非方块
- [ ] 封面构图居中，无大面积无效空白
- [ ] 提醒用户去草稿箱确认效果
- [ ] 若对话中出现 AppSecret，提醒重置

---

## 常见问题

**Q：用户只给了几个要点，没有完整文章？**
A：先用 LLM 根据要点扩展为完整 Markdown，再进入转换流程。

**Q：封面图字体显示为方块？**
A：自动遍历系统中文字体路径，找不到时用默认字体并警告。

**Q：用户没有公众号 API 凭证？**
A：只生成 HTML，用户手动复制到公众号编辑器。

**Q：订阅号无法 API 发布？**
A：创建草稿成功即可，用户去草稿箱手动发布。
