# GBrain YAML Pitfalls

GBrain `import` parses YAML frontmatter strictly. Common trap patterns and fixes.

## Pitfall 1: Double quotes nested inside double-quoted title

**❌ Wrong**: `title: "31条"惠台措施`
- YAML parser sees `"31条"` as a quoted scalar, then encounters bare `惠台措施` after the closing quote — multiline key error.

**✅ Safe**: plain string without inner quotes
```yaml
title: 31条惠台措施
title: 中国共产党统一战线工作条例
```

**✅ Safe**: outer quotes only, no inner quotes
```yaml
title: "31条惠台措施（2018年）"
```

**Reproduction (2026-05-31)**: `entities/policy-31-measures/page.md` skipped with:
```
can not read a block mapping entry; a multiline key may not be an implicit key at line 3, column 8
```
Fix: removed inner quotes → import succeeded.

**Reproduction (2026-06-03)**: `entities/policy-26-measures/page.md` had same pattern `title: "26条"惠台措施` — fixed in dream cycle.

## Pitfall 2: Wiki-style `[[slug]]` links inside YAML list values (2026-06-08 NEW)

**❌ Wrong**: bracketed wiki links in `sources:` list:
```yaml
sources:
  - https://www.gwytb.gov.cn/local/202606/...
  - [[policy-taiwan-investment]] （母法基础）
  - [[policy-31-measures]] （"31条"惠台措施）
```

**Error**:
```
bad indentation of a sequence entry at line 13, column 34:
    - [[policy-taiwan-investment]] （母法基础）
                               ^
expected <block end>, but found '<scalar>'
```

**Root cause**: YAML block-collection parser treats `[[` as flow-style sequence start inside a `-` list item. The double brackets break the block scalar interpretation.

**✅ Fix**: strip `[[` and `]]` in frontmatter (wiki links belong in body, not YAML):
```yaml
sources:
  - https://www.gwytb.gov.cn/local/202606/...
  - policy-taiwan-investment （母法基础）
  - policy-31-measures （31条惠台措施）
```

Or just remove the wiki-link bullets from `sources` entirely — sources should be URLs only.

**Reproduction (2026-06-08)**: `entities/problem-case-taiwan-qualification-barriers/page.md` (comparisons/ 首发) skipped on first import with the above error. Fixed by sed `replace_all('[[', '').replace_all(']]', '')` in frontmatter → re-imported cleanly.

**Detection script** (use before `gbrain import` to catch both pitfalls):
```python
import yaml
content = open(path).read()
fm = content.split('---', 2)[1]
try:
    yaml.safe_load(fm)
except yaml.YAMLError as e:
    print(f"YAML error: {e}")
```

## Other import errors

- Multiline keys: YAML block mapping entries can fail if continuation line starts with a bare unquoted word. Stick to single-line values.
- Empty `title` field: silently accepted but page won't appear in search. Always include.
- Unknown `type`: silently accepted, defaults to `page`.
- Special chars in unquoted titles: colons `互联网:管理办法`, leading spaces, newlines — quote the whole field if needed.