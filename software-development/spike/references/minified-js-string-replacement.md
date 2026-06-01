# Minified JS Bundle String Replacement — Pitfalls

When localizing UI text in a minified React/JS bundle (e.g., a game simulator, web app), naive Python string replacement breaks the code if the target strings are parts of `.concat()` chains or other split-string patterns.

## The Failure Mode

In minified JS, long strings are often split across concatenation:

```javascript
// BEFORE replacement (broken):
console.warn("Could not place ship of size ".concat(i, " after ").concat(o, " attempts. Consider reducing ship count or increasing grid size."))

// If you replace " attempts." alone, you get:
// " attempts.".concat(...)  ← this string now has unmatched quotes inside!
```

**Simple find-replace on any string that is part of a `.concat()` chain will corrupt the JS syntax.**

## The Correct Approach

### Step 1: Extract all quoted strings and identify targets

```python
import re

content = open("bundle.js", "r", encoding="utf-8").read()

# Find every quoted string literal
strings_found = re.findall(r'"[^"]{0,200}"', content)

# For each UI string you want to translate, verify it exists as a STANDALONE literal
targets = ["Help", "Home", "Reset", "MISS", " sunk"]
for t in targets:
    if f'"{t}"' in content:
        print(f"OK: {t}")
    else:
        print(f"SKIP: {t} — not a standalone string (likely part of concat)")
```

### Step 2: Only replace strings that appear as complete quoted literals

```python
replacements = [
    ('"Help"', '"帮助"'),
    ('"Reset"', '"重置"'),
    ('"MISS"', '"未命中"'),
    # DO NOT include: '" attempts.' or any string fragment that is part of a concat chain
]

for old, new in replacements:
    if old in content:  # Verify it exists as written
        content = content.replace(old, new)
```

### Step 3: Verify syntax after replacement

```python
# Check for unclosed quotes (quick proxy for syntax validity)
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if line.strip().startswith('//') or line.strip().startswith('/*'):
        continue
    stripped = line.replace('\\"', '')
    if stripped.count('"') % 2 != 0:
        print(f"WARNING line {i}: {line[:80]}")
```

## Verification Checklist

Before repacking and delivering:

1. ✅ File size change is reasonable (Chinese chars ≈ same byte length as English)
2. ✅ JS syntax check passes (balanced quotes)
3. ✅ Key Chinese strings confirmed present: `grep -a "帮助" bundle.js`
4. ✅ Original English strings gone: `grep -a "Help" bundle.js` (should return nothing for replaced terms)
5. ✅ Load in browser — if blank screen, syntax is still broken somewhere

## Symptoms of a Broken Bundle

- Browser shows blank page (JS crash on load)
- Console error: `Unexpected token` or `Unterminated string literal`
- File size changed by only a few bytes when you replaced many strings (string was part of a chain)

## RAR Repacking on Linux

```bash
# Install rar (not just unrar, for creating archives)
sudo apt-get install -y rar

# Repack from extracted directory
cd /path/to/extracted/
rar a -y /path/to/output.rar  dirname
```
