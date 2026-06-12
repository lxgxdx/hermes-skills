#!/usr/bin/env python3
"""双正则扫描所有 Wiki 政策文件的漏洞标注（兼容内联+章节格式）

6/12 必做升级：兼容两种标注格式
- 格式 A（内联）：**xx漏洞** — xx
- 格式 B（章节）：### 2.x 标题 ⚠️

6/11 cron 之前只匹配格式 A，漏报 4 个文件共 21 个标注漏洞。
本脚本是 SKILL.md 二B-1 步骤 1 的标准化工具。

Usage:
    python3 scripts/double_regex_scan.py
    # 输出：所有政策文件的漏洞列表（去重后）
"""

import os, re, glob

policy_dir = "/home/lxgxdx/wiki/entities/"
files = sorted(glob.glob(f"{policy_dir}/policy-*.md"))

all_vulns = []
for fpath in files:
    fname = os.path.basename(fpath)
    with open(fpath, encoding="utf-8") as fp:
        content = fp.read()

    # 格式 A：内联  **xx漏洞** — xx
    matches_a = re.findall(r'\*\*([^*]+?漏洞)\*\*\s*[—\-]\s*([^\n]+)', content)
    # 格式 B：章节  ### 2.x 标题 ⚠️
    matches_b = re.findall(r'###\s*\d+\.\d+\s+([^\n]+?)(?:\s*⚠️+)?\s*(?:\n|$)', content)

    for title, desc in matches_a:
        all_vulns.append((fname, "A", title.strip(), desc.strip()[:80]))
    for title in matches_b:
        all_vulns.append((fname, "B", title.strip(), "(章节式标注)"))

# 去重：同文件+标题
seen = set()
unique = []
for v in all_vulns:
    key = (v[0], v[2])
    if key not in seen:
        seen.add(key)
        unique.append(v)

print(f"=== Wiki 政策库漏洞扫描结果 ===\n")
print(f"总漏洞数（去重后）: {len(unique)}\n")

# 按文件汇总
by_file = {}
for fname, fmt, title, desc in unique:
    by_file.setdefault(fname, []).append((fmt, title, desc))

# 显示全部漏洞标题
print(f"{'文件':<48} {'格式':<3} {'漏洞标题':<40}")
print("-" * 100)
for fname in sorted(by_file.keys()):
    for fmt, title, desc in by_file[fname]:
        title_short = title[:38] if len(title) > 38 else title
        print(f"{fname:<48} {fmt:<3} {title_short}")
