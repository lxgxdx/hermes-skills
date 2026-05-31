# GBrain YAML Pitfalls (2026-05-31)

## YAML title field quoting rules

GBrain `import` uses YAML frontmatter to read `title`, `type`, `tags`. If the title contains special characters, **always use plain strings without extra quotes** — YAML quoting rules are subtle and differ between parsers.

### ✅ Safe: plain string
```yaml
title: 互联网宗教信息服务管理办法
title: 中国共产党统一战线工作条例
title: 31条惠台措施
```

### ❌ Dangerous: double-quoted title with inner quotes
```yaml
title: "31条"惠台措施   # YAML parser sees "31条" as a quoted scalar, then bare 惠台措施 as unexpected
```

### ❌ Dangerous: other special chars in titles
- Colons in unquoted strings: `title: 互联网:管理办法` → needs quotes
- Leading/trailing spaces: `title: " 管理办法"` → strip or avoid
- Newlines in title: not allowed in YAML scalars

### Pattern
When writing any `page.md` for `gbrain import`, keep `title` as a plain ASCII-safe string. If you must include quotes or colons, escape them:
```yaml
title: "31条惠台措施（2018年）"   # outer quotes, no inner quotes
```

## Other import errors

- Multiline keys: YAML block mapping entries can fail if continuation line starts with a bare unquoted word. Stick to single-line values.
- Empty `title` field: silently accepted but page won't appear in search. Always include.
- Unknown `type`: silently accepted, defaults to `page`.

## Reproduction

Today (2026-05-31): `gbrain import` skipped `entities/policy-31-measures/page.md` with error:
```
can not read a block mapping entry; a multiline key may not be an implicit key at line 3, column 8
```
Root cause: title `"31条"惠台措施` — inner double quotes inside outer double quotes broke the YAML parser.

Fix: changed to `31条惠台措施` (no inner quotes) — import succeeded.
