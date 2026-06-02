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

In any rsync-based sync script, **exclude the entire `.archive/` directory** — never try to whitelist individual subdirectories. Hidden leading-dot directories are the failure mode:

```bash
# SAFEST — exclude the whole archive directory
rsync -av --delete "$SRC/" "$DST/" \
    --exclude '.git' \
    --exclude '.archive/'
```

**The trap (learned the hard way):** an exclude like `'.archive/github-pat-retrieval/'` *should* match the source-side relative path under `~/.hermes/skills/`, but in practice it can silently fail to match. Whether this is rsync's pattern engine treating leading-dot paths specially, or some other path-resolution quirk, the empirical result is: the file gets copied anyway, the commit lands with the real-looking token, and Push Protection blocks the push. Always dry-run first to confirm:

```bash
rsync -avn --delete "$SRC/" "$DST/" --exclude '.archive/' | grep -i archive
# Expected: no output. If you see any ".archive/" path, the exclude failed.
```

If you truly must exclude a single subdirectory instead of the whole `.archive/`, verify with dry-run; if it doesn't match, broaden the exclude to the parent.

Also clean the remote URL before pushing to avoid embedding tokens in .git/config:
```bash
git config remote.origin.url "https://github.com/owner/repo.git"
git push
```

## Cron / Recurring Sync Flow Pitfalls

When the sync is run on a cron schedule (e.g. a daily skills-publish job, a config-mirror, a notes-backup push), three additional failure modes appear that don't show up in one-off manual pushes.

### 1. Local `origin/main` is stale on every run

A workdir that was cloned once and reused will have an `origin/main` ref that lags behind the actual remote. If something else (a manual push, a parallel cron job, a teammate's commit) has advanced the remote, the next `git push` will be rejected with `fetch first`.

Always fetch + rebase (or pull --rebase) before push in a cron job:

```bash
cd "$WORKDIR"
git fetch origin
# Rebase local unpushed commits on top of the new remote HEAD
git rebase origin/main || {
    echo "rebase conflict — manual intervention required" >&2
    exit 3
}
```

If a duplicate commit (same subject line, different SHA) appears in the local history during rebase — common when the same cron job ran successfully once and then ran again before the local `origin/main` ref was updated — `git rebase --skip` is usually the right call. It discards the local duplicate and replays the rest on top of the remote's version.

For non-interactive cron use, set `GIT_EDITOR=true` so the rebase doesn't hang waiting for a human to edit the commit message:

```bash
GIT_EDITOR=true git rebase --continue
```

### 2. `git commit || exit 0` hides later push failures

A common cron pattern:

```bash
git add -A
git commit -m "sync" || exit 0   # no-op if nothing to commit
git push
```

This is fine until `git push` fails — the script exits 1, **but the commit has already been made locally**. The next run starts with a local HEAD one commit ahead of remote, which guarantees a non-fast-forward push (and re-triggers the same failure loop).

Fix: detect the push failure and recover by fetching + rebasing + retrying:

```bash
git push || {
    echo "push failed — fetching and rebasing for retry"
    git fetch origin && git rebase origin/main && git push
}
```

Alternatively, do the fetch + rebase *first*, every run, so the local is always reconcilable with the remote before any push attempt — see the full recipe in `references/cron-sync-to-github.md`.

### 3. Pre-push secret grep as a cheap safety net

Push Protection will reject pushes with secret-like patterns, but its error message is opaque (just "remote rejected" with a one-time unblock URL). Adding a pre-push grep against staged content gives clearer local diagnostics *and* surfaces rsync-exclude bugs that would otherwise leak through silently:

```bash
# After `git add -A`, before `git commit`
if git diff --cached | grep -qE 'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|ghr_[A-Za-z0-9]{20,}|ghu_[A-Za-z0-9]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}'; then
    echo "ERROR: staged content contains a real-looking token. Aborting." >&2
    echo "Inspect with: cd $WORKDIR && git diff --cached | grep -E 'ghp_|github_pat_'" >&2
    exit 2
fi
```

This catches the pattern at commit-time with a useful error, instead of letting it reach GitHub and getting "remote rejected" with a one-time unblock URL. It's also how you discover the leading-dot exclude bug above — if the grep fires, the rsync exclude didn't match what you thought it did.

For the complete cron recipe (rsync → fetch → rebase → secret-grep → commit → push → verify) see `references/cron-sync-to-github.md`.

## GitHub Secret Scanning vs Push Protection

| | Secret Scanning | Push Protection |
|--|--|--|
| When | Post-push (after commit lands) | Pre-push (blocks the push) |
| Scope | Patterns in any pushed commit | Patterns in the push being attempted |
| Response | Alert + notification | Block + URL to resolve |
| Can be bypassed | By security settings | Via GitHub web UI or API allowlist |
