---
name: wiki-scraping
description: "Scrape documentation websites and web articles into clean markdown for wiki ingestion. Handles VitePress, Docusaurus, MkDocs, and standard web pages. Uses BeautifulSoup + markdownify for high-quality HTML→Markdown conversion."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wiki, scraping, web, markdown, documentation]
    category: productivity
---

# Wiki Scraping

Scrape web content into clean markdown for wiki ingestion. This skill handles documentation sites (VitePress, Docusaurus, MkDocs) and general web articles.

## When This Skill Activates

Use this skill when:
- The user asks to scrape, crawl, or ingest a URL into their wiki
- A wiki needs bulk re-scraping of documentation pages
- Content quality from previous scrapes was poor (HTML noise, broken code blocks, UI elements included)

## Quick Start

```python
from hermes_tools import terminal

# Single page
result = terminal("""
python3 -c "
from scrape_doc import scrape_doc_page
print(scrape_doc_page('https://docs.example.com/guide'))
"
""")
```

## Core Function: `scrape_doc_page()`

```python
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import subprocess, re

def scrape_doc_page(url: str) -> str:
    """Fetch and convert a documentation page to clean markdown."""
    html = subprocess.run([
        "curl", "-s", "-L",
        "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
        "--max-time", "20",
        url
    ], capture_output=True, text=True, timeout=25).stdout

    soup = BeautifulSoup(html, 'html.parser')

    # Remove noise elements
    for tag in ['script', 'style', 'nav', 'header', 'footer', 'aside',
                'button', 'svg', 'noscript', 'iframe', 'form', 'input']:
        for e in soup.find_all(tag):
            e.decompose()

    # Find main content — try content-specific selectors first
    article = (
        soup.find('div', class_='vp-doc') or          # VitePress (docs.frigate-cn.video, vitepress.dev)
        soup.find('article') or                         # Docusaurus, standard HTML5
        soup.find('div', class_=re.compile(r'mkdocs|mdoc|doc-content', re.I)) or  # MkDocs
        soup.find('main') or
        soup.find('div', class_=re.compile(r'markdown|content|article', re.I)) or
        soup.body
    )

    if not article:
        return ""

    # Clean element attributes — only keep link-related ones
    for elem in article.find_all(True):
        for attr in list(elem.attrs):
            if attr not in ('href', 'src', 'alt', 'title', 'class'):
                del elem[attr]

    md_text = md(
        str(article),
        heading_style="atx",
        code_style="fenced",
        strip=['script', 'style', 'nav', 'header', 'footer', 'aside',
               'button', 'svg', 'noscript', 'iframe', 'form']
    )

    return post_clean(md_text)


def post_clean(md_text: str) -> str:
    """Remove UI noise from Chinese documentation sites."""
    lines = md_text.split('\n')
    cleaned = []
    skip_patterns = [
        r'^问AI',
        r'^推荐提问',
        r'^显示思考过程',
        r'^用户反馈',
        r'^返回顶部',
        r'^主题$',
        r'^菜单$',
        r'^Skip to content',
        r'^[\s]*[官网|文档|演示|反馈|翻译|赞助]',
        r'^[\s]*(以上版本|更新时间|阅读时长)[\s]*$',
    ]
    for line in lines:
        stripped = line.strip()
        # Skip noise lines
        if any(re.match(p, stripped) for p in skip_patterns):
            continue
        # Skip standalone line numbers (from code blocks)
        if re.match(r'^[\s]*\d+[\s]*$', stripped) and stripped.strip().isdigit():
            continue
        # Skip empty lines at start/end
        if stripped:
            cleaned.append(line)
        elif cleaned and cleaned[-1].strip():
            cleaned.append(line)
    # Strip leading/trailing blank lines
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return '\n'.join(cleaned)
```

## Known Documentation Site Structures

| Site Type | Content Selector | Examples |
|-----------|-----------------|----------|
| **VitePress** | `div.vp-doc` | docs.frigate-cn.video, vitepress.dev |
| **Docusaurus** | `article` | docusaurus.io sites |
| **MkDocs** | `div.wy-nav-content` or `article` | readthedocs.io sites |
| **GitBook** | `div.markdown-body` or `article` | gitbook.com |
| **MediaWiki** | `div#content` (by ID) | pve.proxmox.com, wikipedia |
| **HA Official** | `article` or `div.page-content` | home-assistant.io |
| **Standard HTML** | `main` or `div.content` | Most blogs, news sites |

**Critical**: Content selectors use FALLBACK CHAIN — always try most specific first:
```python
article = (
    soup.find('div', class_='vp-doc') or           # VitePress
    soup.find('article') or                          # Docusaurus / HA / general
    soup.find('div', id='content') or                # MediaWiki (note: id, not class!)
    soup.find('div', class_='page-content') or       # HA official
    soup.find('main') or
    soup.body
)
```

## Saving to Wiki Raw Directory

```python
from pathlib import Path
from datetime import datetime

def save_raw_article(slug: str, url: str, md_content: str, wiki_dir: Path) -> Path:
    """Save scraped content to wiki raw directory."""
    raw_dir = wiki_dir / "raw" / "articles"
    raw_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_dir / f"{slug}.md"
    title = slug.replace('-', ' ').replace('/', ' ').title()

    output = (
        f"# {title}\n\n"
        f"> 来源：{url}\n"
        f"> 抓取时间：{datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"{md_content}"
    )
    file_path.write_text(output, encoding='utf-8')
    return file_path
```

## Bulk Scraping Pattern

When scraping multiple URLs:

1. Define a dict of `slug -> url`
2. **Delete all `.bak` files first** (they contain pre-update content that would otherwise be read as "current")
3. Loop through with progress logging
4. **Strip frontmatter header** from existing file before computing hash — old format has `# Title\n\n> 来源：...\n> 抓取时间：...\n\n` prefix that must be removed for fair comparison
5. Only write if content hash actually changed
6. **Append to wiki `log.md`** with summary after completion

```python
import re
# Before hash comparison, clean old file's header
if local_file.exists():
    old = local_file.read_text(encoding='utf-8')
    old_body = re.sub(r'^#.*?\n\n>.*?\n\n', '', old, count=1)  # strip header
    old_hash = hashlib.md5(old_body.encode()).hexdigest()
```

## Pitfalls

- **Never use raw HTMLParser or `get_text()`** — it captures the entire page including nav, sidebars, and UI widgets. Always use a content-specific selector.
- **Chinese documentation sites** (like docs.frigate-cn.video) have extra UI noise: `问AI`, `推荐提问`, `显示思考过程`, `用户反馈` — must be post-cleaned.
- **English docs.frigate.video is unreachable** from this server — use docs.frigate-cn.video (same content, accessible).
- **`.bak` files accumulate** when updating — clean them AFTER each update run completes, not before. Old .bak files contain the pre-update content and should be removed after successful write.
- **Compare content hashes, not timestamps** — but when comparing, strip the frontmatter header from existing files first:
  ```python
  # Old file has "# Title\n\n> 来源：...\n> 抓取时间：...\n\n" prefix
  old_without_header = re.sub(r'^#.*?\n\n>.*?\n\n', '', old_content, count=1)
  ```
- **Some pages return JS-rendered content** (36-char response with only `<!doctype html>`) — these are SPA pages where curl returns a redirect shell. Verify actual content length before saving.
- **VitePress content area** is `div.vp-doc` (class, no ID). MediaWiki content is `div#content` (ID, no class) — these are easy to confuse.
