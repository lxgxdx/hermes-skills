# GitHub Push Protection & Secret Scanning

GitHub's Push Protection automatically scans every push and blocks it if a secret pattern is detected. Secret Scanning is separate from Push Protection — Push Protection blocks the push, Secret Scanning is a post-push alert system.

## How Push Protection Detects Secrets

Push Protection uses **pattern matching** similar to GitHub's secret scanning. It detects:
- Token prefixes: `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_` (GitHub PAT prefixes)
- API keys for major cloud providers
- Private keys, credentials in URLs

Critically: it scans **all text in the commit**, not just code. Prose, comments, string literals, variable names — all are examined.

## Patterns That Trigger (Even in Examples)

```markdown
<!-- BLOCKED even in prose -->
If your token looks like `ghp_Fc...ZhBU`, it was redacted.
```

```python
# BLOCKED — b'ghp_' is a byte string literal
start = raw.find(b'ghp_')
```

```bash
# BLOCKED — URL with embedded token pattern
git remote add origin https://user:ghp_xxx@github.com/repo.git
```

```python
# BLOCKED — even a comment mentioning the pattern
# Real token format: ghp_ followed by 36 chars
```

## What "ghp_Fc...ZhBU" Actually Means

The `...` is NOT literal — it is Hermes Agent's redaction marker. The real token was partially masked by `agent/redact.py`. The format `ghp_Fc...ZhBU` means:
- Prefix: `ghp_Fc` (real)
- Middle: [REDACTED] (redacted by Hermes)
- Suffix: `ZhBU` (real)

Push Protection does not know about Hermes redaction — it sees `ghp_Fc...ZhBU` and recognizes the `ghp_` + suffix pattern as a valid GitHub PAT format.

## Safe Token Placeholders

Always use placeholders that do not start with a real token family prefix:

```
ghp_xx...xxxx       # clearly fake — safe
TOKEN_NAME_HERE     # safe
YOUR_GITHUB_TOKEN   # safe
<YOUR_TOKEN>        # safe
```

Never use `ghp_` as a prefix in any example, even partially.

## When Already Blocked — Recovery Pattern

If Push Protection has already blocked a push and the workdir is in a confused state:

**Do NOT try `git reset --hard` on a workdir that already has a blocked commit in its history.** The staged changes may still carry the secret. Instead:

```bash
# 1. Clone fresh to a new directory
git clone https://github.com/owner/repo.git /tmp/repo-clean

# 2. Apply your fixes in the clean clone
# (rsync or copy your changes over)

# 3. Commit and push from the clean state
cd /tmp/repo-clean
git add -A
git commit -m "fix: remove secret patterns"
git push
```

The old workdir had a corrupt index (stale staged content from a prior failed attempt). A clean clone sidesteps the entire problem.

## Preventing Future Blocks

When editing any skill or file that references GitHub tokens:

1. **Never use real token prefixes** (`ghp_`, `gho_`, etc.) even in comments
2. **Use obviously-fake placeholders**: `TOKEN_NAME_HERE`, `ghp_xx...xxxx`
3. **For archived skills** (`.archive/` directory) that contain historical examples with real patterns, exclude them from rsync/sync operations entirely
4. **Before pushing**, run a scan locally:
   ```bash
   grep -r "ghp_\|gho_\|ghu_\|ghs_" . --include="*.md" --include="*.py" --include="*.sh"
   ```
   If any match appears outside of a clearly-labeled "FAKE" or "EXAMPLE" section, fix it first.

## Exclude Archived Skills with Secrets from Sync Scripts

In any rsync-based sync script:
```bash
rsync -av --delete "$SRC/" "$DST/" \
    --exclude '.git' \
    --exclude '.archive/github-pat-retrieval/'   # has real PAT examples
```

**Critical rsync exclude path rule:** The `--exclude` pattern must match the **source-side relative path**, not the destination or some other path variant.

Common mistake — this does NOT work:
```bash
# WRONG — pattern doesn't match anything in the source tree
--exclude 'github/github-pat-retrieval'
```

The correct pattern for `~/.hermes/skills/.archive/github-pat-retrieval/` is:
```bash
--exclude '.archive/github-pat-retrieval/'
```

Always verify excludes work by running rsync in dry-run mode first:
```bash
rsync -avn --delete "$SRC/" "$DST/" --exclude '.archive/github-pat-retrieval/'
```

Also clean the remote URL before pushing to avoid embedding tokens in .git/config:
```bash
git config remote.origin.url "https://github.com/owner/repo.git"
git push
```

## GitHub Secret Scanning vs Push Protection

| | Secret Scanning | Push Protection |
|--|--|--|
| When | Post-push (after commit lands) | Pre-push (blocks the push) |
| Scope | Patterns in any pushed commit | Patterns in the push being attempted |
| Response | Alert + notification | Block + URL to resolve |
| Can be bypassed | By security settings | Via GitHub web UI or API allowlist |
