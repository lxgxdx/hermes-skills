---
name: web-design-engineer
description: >
  AI agent skill that transforms AI-generated web pages from "functional" to "stunning."
  Injects design taste into AI coding agents (Claude Code, Cursor, etc.) through anti-cliché rules,
  design system declaration, oklch color theory, and curated font pairings.
  Use when generating HTML/CSS/JavaScript web pages, landing pages, presentations, or data visualizations.
  Source: https://github.com/ConardLi/web-design-skill
---

# Web Design Engineer Skill

> AI agent skill that transforms AI-generated web pages from "functional" to "stunning."

## 核心价值

现代 LLM 能生成功能正确的网页，但视觉上容易趋同：Inter字体、蓝主按钮、紫粉渐变、emoji当图标。

这个 skill 通过设计系统让 AI 做出**有品味**的页面。

---

## 六步工作流

```
1. 理解需求  →  信息不足时才提问
2. 收集设计上下文  →  代码 > 截图，不空着开始
3. 声明设计系统  →  颜色/字体/间距/动效，写在 Markdown 里，再写代码
4. 早期展示 v0 草稿  →  占位符 + 布局 + token，让用户校正
5. 完整构建  →  组件/状态/动效，关键决策点暂停
6. 验证  →  交付前检查清单，无 console 错误，无失控色调
```

---

## 反 AI 套路清单（必须遵守）

明确禁止以下模式：
- 紫-粉-蓝渐变背景
- 左侧边竖线卡片
- Inter / Roboto / Arial / Fraunces / system-ui 字体
- emoji 作为图标替代
- 伪造数据、假 logo 墙、假评价

---

## oklch 色彩系统

颜色在感知均匀的 oklch 空间推导。同样亮度值看起来亮度一致——不像 HSL，黄色50%和蓝色50%实际亮度差异很大。

---

## 精选配色+字体搭配（6组）

| 风格 | 颜色 | 字体 | 场景 |
|------|------|------|------|
| 现代科技 | 蓝紫 | Space Grotesk + Inter | SaaS/开发工具 |
| 优雅编辑 | 暖棕 | Newsreader + Outfit | 内容/博客 |
| 高端品牌 | 近黑 | Sora + Plus Jakarta Sans | 奢侈/金融 |
| 活泼消费 | 珊瑚 | Plus Jakarta Sans + Outfit | 电商/社交 |
| 简约专业 | 青蓝 | Outfit + Space Grotesk | 仪表盘/B2B |
| 手工温暖 | 焦糖 | Caveat + Newsreader | 食品/教育 |

---

## 支持的输出类型

- 网页/落地页
- 交互原型（带设备框架）
- HTML幻灯片（1920×1080，键盘导航）
- 数据可视化（Chart.js/D3.js）
- CSS/JS动画
- 设计系统（token探索、组件变体）

---

## 使用方式

放入项目的 `.agents/skills/web-design-engineer/` 目录：

```
your-project/
├── .agents/skills/web-design-engineer/
│   ├── SKILL.md
│   └── references/
│       └── advanced-patterns.md    # 代码模板库 (~520行)
```

部分工具用 `.claude/skills/` 目录，根据工具选择。

---

## 关键设计原则

1. **设计系统声明** — 强制 AI 在写代码前用自然语言描述设计 token
2. **v0 草稿策略** — 早期展示半成品，用户可校正方向
3. **占位符哲学** — 用 `[icon]` 等诚实标记，不乱画 SVG 假图标
4. **高级模式库** — 常见 UI 模式的代码模板直接可用

---

## 参考文件

- `references/advanced-patterns.md` — 高级 UI 模式代码模板库（521行），包含常用组件的代码模式

---

## 灵感来源

Anthropic 2026年4月发布的 Claude Design 系统提示词的开源移植版。
