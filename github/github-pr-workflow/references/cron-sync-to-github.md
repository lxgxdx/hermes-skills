# Cron / Recurring Local-Dir → GitHub-Mirror Sync

A worked recipe for syncing a local directory (skills, configs, notes, backups) to a GitHub repository on a schedule. Covers the three failure modes that one-off pushes never hit: stale `origin/main`, hidden push failures, and silent rsync-exclude bugs.

## When to Use This

- You have a script that runs on cron (or any scheduled trigger) and publishes a local directory to a GitHub repo.
- You're writing that script for the first time and want to avoid the gotchas below.
- A previous run of that script failed with `! [rejected] main -> main (fetch first)` or `remote rejected due to repository rule violations` and you want to harden it.

If you're pushing a one-off branch from a development workdir, this isn't the right reference — use the main `github-pr-workflow` skill's push section.

## The Recipe

```bash
#!/bin/bash
# Sync a local directory to a GitHub mirror on a schedule.
# Idempotent — safe to run multiple times per day.

set -u  # don't `set -e`; we want to handle each failure explicitly
SRC="$HOME/.hermes/skills"          # local source
WORKDIR="/tmp/hermes-skills-sync"   # ephemeral git workdir
REPO="https://github.com/owner/repo.git"

# 1. Clone-once workdir (re-cloning every run is slow and loses any
#    local unpushed commits; reuse the existing one).
if [ ! -d "$WORKDIR/.git" ]; then
    rm -rf "$WORKDIR"
    git clone "$REPO" "$WORKDIR"
fi

# 2. Mirror local → workdir. ALWAYS exclude entire .archive/ (leading-dot
#    dirs are a known rsync exclude footgun — see push-protection-secrets.md).
rsync -av --delete "$SRC/" "$WORKDIR/" \
    --exclude '.git' \
    --exclude '.archive/' \
    --exclude '.curator_backups/'

cd "$WORKDIR" || exit 1
git add -A

# 3. Secret-pattern guard. Catches rsync-exclude bugs and stray tokens
#    before they reach GitHub (where the error is opaque and gated by
#    Push Protection).
if git diff --cached | grep -qE \
    'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|ghr_[A-Za-z0-9]{20,}|ghu_[A-Za-z0-9]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}'; then
    echo "ERROR: staged content contains a real-looking token. Aborting." >&2
    echo "Inspect: cd $WORKDIR && git diff --cached | grep -E 'ghp_|github_pat_'" >&2
    exit 2
fi

# 4. Commit (no-op if nothing changed).
git commit -m "Skills sync $(date '+%Y-%m-%d %H:%M')" || exit 0

# 5. Fetch + rebase BEFORE push. A long-lived workdir's `origin/main`
#    is stale by definition; pushing without reconciling it first is
#    guaranteed to fail in any concurrent-edit scenario.
git fetch origin
GIT_EDITOR=true git rebase origin/main || {
    echo "rebase conflict — manual intervention required" >&2
    exit 3
}

# 6. Clean any embedded token from remote URL (defense in depth).
git config remote.origin.url "$REPO"

# 7. Push with retry on transient rejection.
git push || {
    echo "push failed — refetching and retrying" >&2
    git fetch origin && GIT_EDITOR=true git rebase origin/main && git push
}
```

## The Three Failure Modes (and Why)

### A. `! [rejected] main -> main (fetch first)`

**Symptom:** Push fails with "Updates were rejected because the remote contains work that you do not have locally."

**Root cause:** The local `origin/main` ref is a snapshot from when the workdir was cloned. If *anything* advanced the remote since — a manual push from another machine, a parallel cron, a webhook-driven bot — the next push from this workdir is a non-fast-forward.

**Fix:** `git fetch origin` updates the ref, then `git rebase origin/main` replays local unpushed commits on top. The rebase can hit conflicts if the same file was edited on both sides — for cron jobs, that's a sign the script isn't the sole writer, and a rebase conflict is the right time to abort and notify a human (`exit 3`).

### B. `remote rejected` / push-protection unblock URL

**Symptom:** Push fails with "remote declined due to repository rule violations" and a URL to unblock-secret.

**Root cause:** GitHub Push Protection matched a secret pattern (`ghp_`, `github_pat_`, etc.) somewhere in the staged content — even inside an "anti-example" diff block, a comment, or a URL fragment.

**Fix (immediate):** `git rm --cached <offending-file>` + `git commit --amend --no-edit` to fold the removal into the existing commit, then retry. Don't try to amend a commit that's already in the remote — for that case, see the re-clone recovery pattern in `push-protection-secrets.md`.

**Fix (preventive):** The pre-push grep in step 3 of the recipe. It catches the bug at commit-time with a clear local error, and it surfaces rsync-exclude bugs (because if a secret-bearing file got synced, the exclude didn't work — and you want to know that *now*, not three days later when GitHub emails you).

### C. `rebase conflict` mid-cron

**Symptom:** The rebase in step 5 halts with "could not apply <commit>" and conflict markers in one or more files.

**Root cause:** The remote has commits the local doesn't, and at least one of them touches the same lines as a local commit. For a single-writer cron, this is rare; for anything multi-writer or multi-machine, it happens.

**Fix:** Two options:
- **Cron-friendly:** Abort and alert a human (`exit 3`). Cron jobs shouldn't be making judgment calls about content conflicts.
- **Best-effort:** Take the remote version (`git checkout --theirs <file>`), `git add` it, then `GIT_EDITOR=true git rebase --continue`. The local changes for that hunk are lost, but the push proceeds.

For non-interactive cron use, always set `GIT_EDITOR=true` so the rebase doesn't hang waiting for someone to type a commit message.

## Verifying Excludes Work

Before deploying a sync script, dry-run the rsync and confirm no excluded files leak through:

```bash
rsync -avn --delete "$SRC/" "$WORKDIR-test/" \
    --exclude '.git' \
    --exclude '.archive/' \
    | grep -E '\.archive/|\.git/'
# Expected: no output. If you see excluded paths, the pattern didn't match.
```

The `-n` flag (dry-run) shows what *would* be transferred without actually moving anything. Pipe through `grep` to see if your excludes are doing anything. If a leading-dot path is showing up in the output, broaden the exclude to the parent (e.g. exclude `.archive/` rather than `.archive/some-subdir/`).

## When to Re-clone vs Recover

| Situation | Action |
|-----------|--------|
| Push-protection blocked, workdir is fresh | `git rm --cached` offending file + `git commit --amend` + retry |
| Push-protection blocked, workdir is in a confused state (multiple failed attempts) | Re-clone to a new workdir, re-rsync, commit, push |
| `fetch first` rejection, no local unpushed commits | `git fetch origin && git push` (fast-forward) |
| `fetch first` rejection, local has unpushed commits | `git fetch origin && git rebase origin/main && git push` |
| Rebase conflict in cron | `exit 3` and alert — don't auto-resolve content conflicts |

## Related

- `references/push-protection-secrets.md` — full coverage of GitHub Push Protection: what triggers it, what placeholders are safe, and the re-clone recovery pattern.
- `references/github-large-file-pitfalls.md` — the 100 MB file size limit and BFG repo-cleaner recipe; relevant if your synced directory ever contains large assets.
