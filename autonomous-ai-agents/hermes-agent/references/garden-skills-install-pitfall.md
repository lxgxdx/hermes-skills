# garden-skills 安装陷阱

## 问题

从 `https://github.com/ConardLi/garden-skills` 安装技能时，使用 `blob/main/` URL 会导致技能内容变成 HTML 而非 Markdown。

## 正确安装方式

必须使用 `raw.githubusercontent.com` URL：

```bash
hermes skills install https://raw.githubusercontent.com/ConardLi/garden-skills/main/skills/kb-retriever/SKILL.md --category productivity --name kb-retriever --force --yes
```

## 技能清单

| 技能名 | 用途 | 推荐度 |
|--------|------|--------|
| `kb-retriever` | 本地知识库检索 | ✅ 有效 |
| `gpt-image-2` | GPT Image 2 图像生成 | ❌ 内容为 HTML，未修复 |
| `web-design-engineer` | 网页视觉设计 | ❌ 内容为 HTML，未修复 |
| `web-video-presentation` | 文章→网页视频 | ❌ 内容为 HTML，未修复 |

## 验证技能是否损坏

```bash
head -5 ~/.hermes/skills/<category>/<skill>/SKILL.md
```

- 正确内容：第一行是 `---`（YAML frontmatter）
- 损坏内容：第一行是 `<!DOCTYPE html>`

## 图像生成替代方案

`gpt-image-2` 技能损坏，但 MiniMax CN 图像生成 API 可直接调用。详见 `baoyu-infographic/references/minimax-image-api.md`。

正确安装 raw URL 后，`gpt-image-2` 的图像生成流程仍然可以通过直接 API 调用使用，无需依赖 skill 内容。
