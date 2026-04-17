# Hermes Skills

Hermes Agent 的技能库备份，每日 6:00 自动同步至 GitHub。

> 删除的技能可在此仓库找回，通过 `git log` 或 GitHub commit 历史恢复。

## 目录

- [Apple](#apple)
  - [Apple Notes](#apple-apple-notes)
  - [Apple Reminders](#apple-apple-reminders)
  - [Findmy](#apple-findmy)
  - [Imessage](#apple-imessage)
- [Autonomous Ai Agents](#autonomous-ai-agents)
  - [Claude Code](#autonomous-ai-agents-claude-code)
  - [Codex](#autonomous-ai-agents-codex)
  - [Hermes Agent](#autonomous-ai-agents-hermes-agent)
  - [Opencode](#autonomous-ai-agents-opencode)
- [Creative](#creative)
  - [Architecture Diagram](#creative-architecture-diagram)
  - [Ascii Art](#creative-ascii-art)
  - [Ascii Video](#creative-ascii-video)
  - [Creative Ideation](#creative-creative-ideation)
  - [Excalidraw](#creative-excalidraw)
  - [Manim Video](#creative-manim-video)
  - [P5Js](#creative-p5js)
  - [Popular Web Designs](#creative-popular-web-designs)
  - [Songwriting And Ai Music](#creative-songwriting-and-ai-music)
- [Data Science](#data-science)
  - [Jupyter Live Kernel](#data-science-jupyter-live-kernel)
- [Devops](#devops)
  - [Hermes Web Ui Deploy](#devops-hermes-web-ui-deploy)
  - [Webhook Subscriptions](#devops-webhook-subscriptions)
- [Email](#email)
  - [Himalaya](#email-himalaya)
- [Gaming](#gaming)
  - [Minecraft Modpack Server](#gaming-minecraft-modpack-server)
  - [Pokemon Player](#gaming-pokemon-player)
- [Github](#github)
  - [Codebase Inspection](#github-codebase-inspection)
  - [Github Auth](#github-github-auth)
  - [Github Code Review](#github-github-code-review)
  - [Github Issues](#github-github-issues)
  - [Github Pr Workflow](#github-github-pr-workflow)
  - [Github Repo Management](#github-github-repo-management)
- [Leisure](#leisure)
  - [Find Nearby](#leisure-find-nearby)
- [Mcp](#mcp)
  - [Mcporter](#mcp-mcporter)
  - [Native Mcp](#mcp-native-mcp)
- [Media](#media)
  - [Gif Search](#media-gif-search)
  - [Heartmula](#media-heartmula)
  - [Songsee](#media-songsee)
  - [Youtube Content](#media-youtube-content)
- [Mlops](#mlops)
  - [Huggingface Hub](#mlops-huggingface-hub)
  - [Tei Unraid Nvidia Deploy](#mlops-tei-unraid-nvidia-deploy)
- [Note Taking](#note-taking)
  - [Obsidian](#note-taking-obsidian)
- [Openclaw Imports](#openclaw-imports)
  - [Academic Research](#openclaw-imports-academic-research)
  - [Baidu Search](#openclaw-imports-baidu-search)
  - [Bing Search](#openclaw-imports-bing-search)
  - [Convert To Pdf](#openclaw-imports-convert-to-pdf)
  - [Document Editor](#openclaw-imports-document-editor)
  - [Document Organizer](#openclaw-imports-document-organizer)
  - [Github](#openclaw-imports-github)
  - [Obsidian](#openclaw-imports-obsidian)
  - [Pdf Ocr](#openclaw-imports-pdf-ocr)
  - [Pdf Smart Tool Cn](#openclaw-imports-pdf-smart-tool-cn)
  - [Pdf To Image Preview](#openclaw-imports-pdf-to-image-preview)
  - [Pdf To Word With Format](#openclaw-imports-pdf-to-word-with-format)
  - [Tmux](#openclaw-imports-tmux)
  - [Word Docx](#openclaw-imports-word-docx)
  - [Ws Excel](#openclaw-imports-ws-excel)
- [Productivity](#productivity)
  - [Gbrain Ops](#productivity-gbrain-ops)
  - [Google Workspace](#productivity-google-workspace)
  - [Hermes To Gbrain Sync](#productivity-hermes-to-gbrain-sync)
  - [Linear](#productivity-linear)
  - [Nano Pdf](#productivity-nano-pdf)
  - [Notion](#productivity-notion)
  - [Ocr And Documents](#productivity-ocr-and-documents)
  - [Openclaw Memory Sync](#productivity-openclaw-memory-sync)
  - [Powerpoint](#productivity-powerpoint)
  - [Ppt Master Install](#productivity-ppt-master-install)
  - [Pptagent Debugging](#productivity-pptagent-debugging)
  - [Pptagent Deploy](#productivity-pptagent-deploy)
  - [Tz File Organizer](#productivity-tz-file-organizer)
- [Red Teaming](#red-teaming)
  - [Godmode](#red-teaming-godmode)
- [Research](#research)
  - [Arxiv](#research-arxiv)
  - [Blogwatcher](#research-blogwatcher)
  - [Llm Wiki](#research-llm-wiki)
  - [Polymarket](#research-polymarket)
  - [Research Paper Writing](#research-research-paper-writing)
- [Smart Home](#smart-home)
  - [Openhue](#smart-home-openhue)
- [Social Media](#social-media)
  - [Xitter](#social-media-xitter)
- [Software Development](#software-development)
  - [Plan](#software-development-plan)
  - [Requesting Code Review](#software-development-requesting-code-review)
  - [Subagent Driven Development](#software-development-subagent-driven-development)
  - [Systematic Debugging](#software-development-systematic-debugging)
  - [Test Driven Development](#software-development-test-driven-development)
  - [Writing Plans](#software-development-writing-plans)

---

## Apple

### Apple Notes
Use `memo` to manage Apple Notes directly from the terminal. Notes sync across all Apple devices via iCloud.
*路径: `apple/apple-notes`*

### Apple Reminders
Use `remindctl` to manage Apple Reminders directly from the terminal. Tasks sync across all Apple devices via iCloud.
*路径: `apple/apple-reminders`*

### Findmy
Track Apple devices and AirTags via the FindMy.app on macOS. Since Apple doesn't provide a CLI for FindMy, this skill uses AppleScript to open the app and screen capture to read device locations.
*路径: `apple/findmy`*

### Imessage
Use `imsg` to read and send iMessage/SMS via macOS Messages.app.
*路径: `apple/imessage`*

---

## Autonomous Ai Agents

### Claude Code
Delegate coding tasks to Claude Code (Anthropic's autonomous coding agent CLI) via the Hermes terminal. Claude Code v2.x can read files, write code, run tests, and navigate codebases.
*路径: `autonomous-ai-agents/claude-code`*

### Codex
Delegate coding tasks to Codex (OpenAI's autonomous coding agent CLI) via the Hermes terminal.
*路径: `autonomous-ai-agents/codex`*

### Hermes Agent
Hermes Agent is an open-source AI agent framework by Nous Research that runs in your terminal, messaging platforms, and IDEs.
*路径: `autonomous-ai-agents/hermes-agent`*

### Opencode
Use OpenCode as an autonomous coding worker orchestrated by Hermes terminal/process tools. OpenCode is a provider-agnostic, open-source AI coding agent with a TUI and CLI.
*路径: `autonomous-ai-agents/opencode`*

---

## Creative

### Architecture Diagram
Generate professional, dark-themed technical architecture diagrams as standalone HTML files with inline SVG graphics.
*路径: `creative/architecture-diagram`*

### Ascii Art
Multiple tools for different ASCII art needs — cowsay, figlet, boxes, etc. No API keys required.
*路径: `creative/ascii-art`*

### Ascii Video
Production pipeline for ASCII art video — converts video/audio/images/generative input into colored ASCII character video output (MP4, GIF, image sequence).
*路径: `creative/ascii-video`*

### Creative Ideation
Generate project ideas through creative constraints.
*路径: `creative/creative-ideation`*

### Excalidraw
Create hand-drawn style diagrams using Excalidraw JSON format. Files can be drag-and-dropped onto excalidraw.com.
*路径: `creative/excalidraw`*

### Manim Video
Production pipeline for mathematical and technical animations using Manim Community Edition. Creates 3Blue1Brown-style explainer videos.
*路径: `creative/manim-video`*

### P5Js
Production pipeline for interactive and generative visual art using p5.js. Creates browser-based sketches, generative art, data visualizations.
*路径: `creative/p5js`*

### Popular Web Designs
54 real-world design systems ready for use when generating HTML/CSS.
*路径: `creative/popular-web-designs`*

### Songwriting And Ai Music
Songwriting craft and AI music generation prompts (Suno focused).
*路径: `creative/songwriting-and-ai-music`*

---

## Data Science

### Jupyter Live Kernel
Gives you a stateful Python REPL via a live Jupyter kernel. Variables persist across executions. Use instead of `execute_code` when you need to build up state incrementally.
*路径: `data-science/jupyter-live-kernel`*

---

## Devops

### Hermes Web Ui Deploy
hermes-web-ui 安装、启动、局域网访问配置。
*路径: `devops/hermes-web-ui-deploy`*

### Webhook Subscriptions
Create dynamic webhook subscriptions so external services (GitHub, GitLab, Stripe) can trigger Hermes agent runs.
*路径: `devops/webhook-subscriptions`*

---

## Email

### Himalaya
Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.
*路径: `email/himalaya`*

---

## Gaming

### Minecraft Modpack Server
Set up a modded Minecraft server from a CurseForge/Modrinth zip or modpack URL.
*路径: `gaming/minecraft-modpack-server`*

### Pokemon Player
Play Pokemon games autonomously via headless emulation using the `pokemon-agent` package.
*路径: `gaming/pokemon-player`*

---

## Github

### Codebase Inspection
Analyze repositories for lines of code, language breakdown, file counts using `pygount`.
*路径: `github/codebase-inspection`*

### Github Auth
Set up authentication so the agent can work with GitHub repositories, PRs, issues, and CI.
*路径: `github/github-auth`*

### Github Code Review
Perform code reviews on local changes before pushing, or review open PRs on GitHub.
*路径: `github/github-code-review`*

### Github Issues
Create, search, triage, and manage GitHub issues.
*路径: `github/github-issues`*

### Github Pr Workflow
Complete guide for managing the PR lifecycle — create branches, commit changes, open PRs, request reviews.
*路径: `github/github-pr-workflow`*

### Github Repo Management
Create, clone, fork, configure, and manage GitHub repositories.
*路径: `github/github-repo-management`*

---

## Leisure

### Find Nearby
Find restaurants, cafes, bars, pharmacies, and other places near any location. Uses OpenStreetMap (free, no API keys).
*路径: `leisure/find-nearby`*

---

## Mcp

### Mcporter
Use `mcporter` to discover, call, and manage MCP (Model Context Protocol) servers and tools directly from the terminal.
*路径: `mcp/mcporter`*

### Native Mcp
Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available.
*路径: `mcp/native-mcp`*

---

## Media

### Gif Search
Search and download GIFs directly via the Tenor API using curl.
*路径: `media/gif-search`*

### Heartmula
Set up and run HeartMuLa, the open-source music generation tool.
*路径: `media/heartmula`*

### Songsee
Generate spectrograms and multi-panel audio feature visualizations from audio files.
*路径: `media/songsee`*

### Youtube Content
Fetch YouTube video transcripts and transform them into useful formats.
*路径: `media/youtube-content`*

---

## Mlops

### Huggingface Hub
Search, download, and upload models, datasets, and Spaces using the `hf` CLI.
*路径: `mlops/huggingface-hub`*

### Tei Unraid Nvidia Deploy
在 Unraid 上通过 Docker 部署 TEI (text-embeddings-inference)，原生 OpenAI 兼容 API。
*路径: `mlops/tei-unraid-nvidia-deploy`*

---

## Note Taking

### Obsidian
Read, search, and create notes in the Obsidian vault.
*路径: `note-taking/obsidian`*

---

## Openclaw Imports

### Academic Research
Search 250M+ academic works via OpenAlex. No API key required.
*路径: `openclaw-imports/academic-research`*

### Baidu Search
Search the web via Baidu AI Search API.
*路径: `openclaw-imports/baidu-search`*

### Bing Search
Bing search skill for all users. No API key needed.
*路径: `openclaw-imports/bing-search`*

### Convert To Pdf
Convert one or multiple documents to PDF by uploading.
*路径: `openclaw-imports/convert-to-pdf`*

### Document Editor
高级文档编辑工具，支持Word和Excel深度格式化，完美适配机关公文格式规范国家标准。
*路径: `openclaw-imports/document-editor`*

### Document Organizer
Organize documents by analyzing content and categorizing files.
*路径: `openclaw-imports/document-organizer`*

### Github
Interact with GitHub using the `gh` CLI.
*路径: `openclaw-imports/github`*

### Obsidian
Work with Obsidian vaults (plain Markdown notes).
*路径: `openclaw-imports/obsidian`*

### Pdf Ocr
PDF扫描件转Word文档，支持中文OCR识别。
*路径: `openclaw-imports/pdf-ocr`*

### Pdf Smart Tool Cn
PDF智能处理工具 v2.1 — 支持PDF转换、OCR识别、合并拆分、数字签名、批量处理、水印添加、加密解密。
*路径: `openclaw-imports/pdf-smart-tool-cn`*

### Pdf To Image Preview
将PDF文件的每一页转换为图片文件，支持自定义图片格式和分辨率。
*路径: `openclaw-imports/pdf-to-image-preview`*

### Pdf To Word With Format
高精度PDF转Word转换服务，最大程度保留原始文档的所有格式信息。
*路径: `openclaw-imports/pdf-to-word-with-format`*

### Tmux
Remote-control tmux sessions for interactive CLIs.
*路径: `openclaw-imports/tmux`*

### Word Docx
Create, inspect, and edit Microsoft Word documents and DOCX files with reliable styles, numbering, tables.
*路径: `openclaw-imports/word-docx`*

### Ws Excel
Excel 操作 — 数据处理、公式、表格操作。
*路径: `openclaw-imports/ws-excel`*

---

## Productivity

### Gbrain Ops
GBrain 个人知识库操作手册，涵盖 gbrain put 必须通过 stdin、bunfs bug 等。
*路径: `productivity/gbrain-ops`*

### Google Workspace
Gmail, Calendar, Drive, Contacts, Sheets, and Docs integration.
*路径: `productivity/google-workspace`*

### Hermes To Gbrain Sync
把 Hermes 的微信/Telegram 对话自动同步到 GBrain 个人知识库，实现长期记忆和语义搜索。
*路径: `productivity/hermes-to-gbrain-sync`*

### Linear
Manage Linear issues, projects, and teams via the GraphQL API.
*路径: `productivity/linear`*

### Nano Pdf
Edit PDFs using natural-language instructions.
*路径: `productivity/nano-pdf`*

### Notion
Use the Notion API to create, read, update pages, databases, and blocks.
*路径: `productivity/notion`*

### Ocr And Documents
Extract text from PDFs and scanned documents using web_extractor or marker.
*路径: `productivity/ocr-and-documents`*

### Openclaw Memory Sync
从 openclaw 的 SQLite 记忆库中读取长期记忆，用于融合跨智能体的记忆。
*路径: `productivity/openclaw-memory-sync`*

### Powerpoint
Use this skill any time a .pptx file is involved — creating, reading, editing, combining, splitting.
*路径: `productivity/powerpoint`*

### Ppt Master Install
安装 ppt-master 技能及其依赖（GitHub 5.4k stars 的 AI PPT 生成工具）。
*路径: `productivity/ppt-master-install`*

### Pptagent Debugging
PPTAgent (deeppresenter) 本地部署故障排查记录。
*路径: `productivity/pptagent-debugging`*

### Pptagent Deploy
PPTAgent（ICIP/EMNLP 2025）本地部署指南，含 uv 安装、依赖解决、API key 配置。
*路径: `productivity/pptagent-deploy`*

### Tz File Organizer
从备份目录批量整理重要会议材料到年份目录，并更新Excel会议目录。
*路径: `productivity/tz-file-organizer`*

---

## Red Teaming

### Godmode
Jailbreak API-served LLMs using G0DM0D3 techniques — Parseltongue input obfuscation, GODMODE CLASSIC templates, ULTRAPLINIAN multi-model racing.
*路径: `red-teaming/godmode`*

---

## Research

### Arxiv
Search and retrieve academic papers from arXiv via their free REST API. No API key required.
*路径: `research/arxiv`*

### Blogwatcher
Monitor blogs and RSS/Atom feeds for updates using the blogwatcher-cli tool.
*路径: `research/blogwatcher`*

### Llm Wiki
Karpathy's LLM Wiki — build and maintain a persistent, interactive LLM knowledge base.
*路径: `research/llm-wiki`*

### Polymarket
Query Polymarket prediction market data via their public REST APIs.
*路径: `research/polymarket`*

### Research Paper Writing
End-to-end pipeline for producing publication-ready ML/AI research papers targeting NeurIPS, ICML, ICLR, ACL, AAAI, COLM.
*路径: `research/research-paper-writing`*

---

## Smart Home

### Openhue
Control Philips Hue lights, rooms, and scenes via the OpenHue API.
*路径: `smart-home/openhue`*

---

## Social Media

### Xitter
Interact with X/Twitter via the x-cli terminal client.
*路径: `social-media/xitter`*

---

## Software Development

### Plan
Use this skill when the user wants a plan instead of execution.
*路径: `software-development/plan`*

### Requesting Code Review
Automated verification pipeline before code lands — static scans, quality gates, an independent reviewer subagent.
*路径: `software-development/requesting-code-review`*

### Subagent Driven Development
Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.
*路径: `software-development/subagent-driven-development`*

### Systematic Debugging
Systematic approach to debugging — quick patches mask underlying issues.
*路径: `software-development/systematic-debugging`*

### Test Driven Development
Write the test first. Watch it fail. Write minimal code to pass.
*路径: `software-development/test-driven-development`*

### Writing Plans
Write comprehensive implementation plans for when the implementer has zero context for the codebase.
*路径: `software-development/writing-plans`*

---
