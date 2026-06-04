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

## Pitfall: Pre-Push Regex False-Positive on Redacted Placeholders

The regex in step 3 fires on its own recommended "safe placeholder" form, and on any redacted example of the shape `ghp_<prefix>...<suffix>`.

**Why this happens:** The example strings used in the very guidance below the regex — `ghp_xx...xxxx`, `ghp_Fc...ZhBU`, etc. — match `ghp_[A-Za-z0-9]{20,}` because everything between `ghp_` and `@` is 20+ word characters. The `...` is not a regex metacharacter; it's literal dots. So `Fc...ZhBU` is 9 chars (`F`,`c`,`.`,`.`,`.`,`Z`,`h`,`B`,`U`) — well over the 20-char floor.

**Concrete example of the false positive** (from a 2026-06-03 cron run):

```
$ git diff --cached | grep -E "ghp_[A-Za-z0-9]{20,}" | head
+   - https://lxgxdx:ghp_Fc...ZhBU@github.com/...
+   + https://lxgxdx:ghp_xx...xxxx@github.com/owner/repo.git
+https://lxgxdx:ghp_xx...xxxx@github.com/owner/repo.git
```

Every line is a *documentation* example of redaction, not a real token — but the grep fires anyway.

**Two fixes, apply both:**

1. **Strip the redaction marker from the diff before grepping.** Real tokens never contain `...`; placeholder examples always do.
   ```bash
   if git diff --cached | sed 's/\.\.\.//g' | grep -qE \
       'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|ghr_[A-Za-z0-9]{20,}|ghu_[A-Za-z0-9]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}'; then
       echo "ERROR: staged content contains a real-looking token. Aborting." >&2
       exit 2
   fi
   ```
   The `sed 's/\.\.\.//g'` collapses every `...` in the diff to empty *before* the regex runs, so redacted placeholders no longer match. Real tokens never contain `...` so they still fire.

2. **Exclude the entire `.archive/` directory upstream** in the rsync (already the recommendation in `push-protection-secrets.md`, but verify with `rsync -avn ... | grep archive`). The false-positive file in the 2026-06-03 run was `.archive/github-pat-retrieval/references/git-config-token-extract.md` — an archived skill with redacted-token examples. The rsync command had `--exclude '.archive/'` but the file was already tracked in the repo from a prior run, so `git add -A` re-staged it.

**Caveat on fix #1 (learned 2026-06-04):** the `sed 's/\.\.\.//g'` strip ONLY collapses redaction markers. If the staged content actually contains a real PAT in unredacted form — e.g. someone pasted a raw 40-char `ghp_<alnum><alnum><alnum><alnum>...<alnum><alnum><alnum><alnum>` token into a SKILL by mistake (no `...` in the actual string) — the regex will still match (the real token has no `...` in it). The fix is correct: false positives are reduced, real leaks are still caught. Just don't assume "no `...` in the diff ⇒ safe" — verify with the original (unstripped) regex too if you want a belt-and-suspenders check.

## Pitfall: rsync --exclude '.archive/' Doesn't Clean Up Files Already in the Workdir

The `rsync -av --delete … --exclude '.archive/'` form does not delete files that *already exist in the destination* under an excluded path. rsync simply never scans the excluded subtree, so `--delete` has nothing to do there. The next `git add -A` re-stages every pre-existing file under that path as a fresh addition.

This bit a 2026-06-04 cron run: `.archive/github-pat-retrieval/` (with a 40-char real PAT example inside) had been copied into `/tmp/hermes-skills-sync/.archive/` by an older script version that didn't exclude `.archive/`. The current exclude was correct, but the file was on disk, so `git add -A` re-staged it and the safety net correctly caught it.

**Three-part fix:**

1. **Add `--delete-excluded`** to the rsync so excluded files at the destination are also removed. This is the cleanest single change:
   ```bash
   rsync -av --delete --delete-excluded "$SRC/" "$WORKDIR/" \
       --exclude '.git' \
       --exclude '.archive/' \
       --exclude '.curator_backups/'
   ```
   This also removes `html-ppt/`, `ppt-master/`, etc. from the workdir, which is the correct outcome — they should not be in the public mirror either.

2. **Or, replace `git add -A` with a pathspec that excludes the archive:**
   ```bash
   git add -- ':!/.archive' ':!/.curator_backups'
   ```
   Narrower (doesn't physically remove files from the workdir) but achieves the same commit-time effect.

3. **Or, nuke the workdir's `.archive/` after every rsync** with a targeted find-delete if the rsync step needs to stay read-only.

`rsync -avn … | grep archive` (dry-run) is a good check for *what rsync will copy next*, but it is NOT a check for *what `git add -A` will stage*. Always do a `git status -s` after the rsync and look for unexpected `A ` (added) lines under excluded paths.

## Pitfall: `git rm --cached -r .archive/` Causes a Mass-Deletion Commit

If a single subdir under `.archive/` is the offender (e.g. `.archive/github-pat-retrieval/`), the obvious fix is:

```bash
git rm --cached -r .archive/github-pat-retrieval/
```

This is correct for the offender, but it has a side effect: every *other* tracked file under `.archive/` (e.g. `.archive/github-auth/`, `.archive/codebase-inspection/`, …) now shows up in `git status` as `D ` (deleted). If you commit and push, you'll ship a mass deletion of every archived skill, even though the only thing you wanted to drop was one subdir.

**Fix:** Restore the rest of `.archive/` from HEAD *before* `git add -A`:

```bash
# 1. Unstage the offender
git rm --cached -r .archive/<offending-subdir>/

# 2. Restore everything else under .archive/ to match HEAD
git checkout HEAD -- .archive/

# 3. Re-stage the legitimate changes
git add -A

# 4. Re-verify the safety net
git diff --cached | sed 's/\.\.\.//g' | grep -qE 'ghp_[A-Za-z0-9]{20,}|…' && exit 2 || true
```

Same pattern applies to any directory you partially want to keep: `git rm --cached -r` is a sledgehammer, and you need a `git checkout HEAD -- <dir>` afterward if the dir is already tracked and you only wanted to drop a sub-path.

## Authoring Rule: Never Show Unredacted `ghp_<prefix>...<suffix>` Examples in SKILL.md Files

This is a meta-rule for anyone editing a skill or reference that documents redaction behavior.

The `...` (or `…`) in `ghp_xx...xxxx` is Hermes's redaction marker. Real GitHub PATs have *no* redaction marker in their original form — they look like `ghp_<36 alnum chars>` with no dot-run in the middle. So presenting a "looks-redacted" example such as `ghp_Fc...ZhBU` in a SKILL.md is either:

- **A genuine real PAT pasted into the SKILL by mistake** — in which case the SKILL itself will trigger Push Protection and re-leak on every cron sync that copies it. This happened in the 2026-06-04 run: the example `ghp_Fc...ZhBU` in `.archive/github-pat-retrieval/SKILL.md` was actually a 40-char real token, not a placeholder.
- **A `ghp_<4+ real chars>...<4+ real chars>` example string that simulates the redacted shape** — in which case it still matches the pre-push regex and is indistinguishable from the real-PAT case to the safety net.

Either way, the right approach is to **use placeholders that do not start with a real token family prefix at all**:

```
ghp_<your_token>     # angle-bracket placeholder
TOKEN_NAME_HERE      # no prefix at all
<GH_TOKEN>           # angle-bracket only
```

If you must illustrate the redaction *shape* (prefix + middle + suffix) in a doc, use a non-`ghp_` example, or use a clearly-fake `ghp_` prefix followed by `<20` alnum chars (e.g. `ghp_xx xxxx` with a space — see the `push-protection-secrets.md` cheat sheet for which shapes still trip the regex).

Before committing any new SKILL.md or example file, run:

```bash
git diff --cached | grep -nE 'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}'
```

If the only matches are inside backticks/code blocks that use the recommended placeholders above, you're fine. If anything else shows up, rewrite before pushing.

**Recovery pattern when the safety net correctly blocks a real doc file mixed in with a legitimate sync:**

The pre-push grep is doing its job — don't bypass it. Instead, unstage the offending file from this commit so the rest of the sync can proceed, and deal with the offender separately (rewrite the example, delete the file, or `git rm --cached` it from history):

```bash
# 1. Identify the offending file
git diff --cached | grep -nE "ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"

# 2. Unstage it (preserves the working-copy file on disk, just removes from this commit)
cd "$WORKDIR"
git restore --staged .archive/<offending-skill>/...

# 3. Re-verify
git diff --cached | grep -nE "ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
# Expected: no output. (Then proceed with commit + push as in step 4-7.)
```

If the offending file is *already tracked* in the remote and you want it gone permanently, `git rm --cached <path>` then commit the deletion in a separate commit. Don't try to rewrite history from inside the cron script — re-clone if needed.

**Why the cron session should NOT just push past the warning:** the safety net exists to surface rsync-exclude bugs. If the regex fires, the exclude didn't work. Fix the exclude or the source file; don't paper over the warning with a force-push.

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
