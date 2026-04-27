#!/usr/bin/env python3
"""
scrape_doc.py - Documentation site scraper for wiki ingestion.

Usage:
    from scrape_doc import scrape_doc_page, save_raw_article
    md = scrape_doc_page('https://docs.example.com/guide')
    save_raw_article('my-guide', 'https://docs.example.com/guide', md, Path.home() / 'wiki')
"""

import subprocess
import hashlib
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import markdownify as md


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
        for elem in soup.find_all(tag):
            elem.decompose()

    # Find main content — try content-specific selectors first
    # NOTE: MediaWiki uses id='content', VitePress uses class='vp-doc'
    article = (
        soup.find('div', class_='vp-doc') or                            # VitePress
        soup.find('article') or                                           # Docusaurus / HA / general HTML5
        soup.find('div', id='content') or                                 # MediaWiki (pve.proxmox.com)
        soup.find('div', class_='page-content') or                        # HA official docs
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
    """Remove UI noise from Chinese documentation sites and general web pages."""
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
        if any(re.match(p, stripped) for p in skip_patterns):
            continue
        if re.match(r'^[\s]*\d+[\s]*$', stripped) and stripped.strip().isdigit():
            continue
        if stripped:
            cleaned.append(line)
        elif cleaned and cleaned[-1].strip():
            cleaned.append(line)
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return '\n'.join(cleaned)


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


def content_hash(md_content: str) -> str:
    """Compute hash for content comparison."""
    return hashlib.md5(md_content.encode()).hexdigest()


def strip_frontmatter(content: str) -> str:
    """Strip the '# Title\\n\\n> 来源：...\\n> 抓取时间：...\\n\\n' header from raw article files."""
    return re.sub(r'^#.*?\n\n>.*?\n\n', '', content, count=1)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 scrape_doc.py <url> [slug]")
        sys.exit(1)
    url = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else url.split('/')[-1].replace('.md', '')
    md_content = scrape_doc_page(url)
    print(f"Fetched: {len(md_content)} chars")
    print(md_content[:500])
