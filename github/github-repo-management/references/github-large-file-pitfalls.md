# GitHub File Size Limits & Large File Pitfalls

## GitHub's Hard Limits

| Limit | Value |
|-------|-------|
| Max file size | **100 MB** |
| Max repo size | Soft limit ~5 GB |
| Max blob size (Git) | 100 MB |

Files exceeding 100 MB are **rejected at pre-receive hook** — they cannot be pushed regardless of auth or method.

## Common Sources of Oversized Files

### 1. Hermes Curator Backups (`.curator_backups/`)

Located at `~/.hermes/skills/.curator_backups/`, these contain `skills.tar.gz` archives created by the curator. They routinely exceed 275 MB.

**If you sync `~/.hermes/skills/` to GitHub via rsync without excluding this directory, the push will fail.**

### 2. ML Model Files (`.gguf`, `.safetensors`, `.bin`)

Binary model weights almost always exceed 100 MB. Never commit these to a regular Git repo.

### 3. Dataset Files

CSVs, JSONL, or Parquet files with large corpora frequently exceed the limit.

### 4. Node_modules, Virtual Environments

Dependencies are not source and should never be in a Git repo.

## Prevention Strategies

### For rsync-based sync scripts

Always exclude these patterns:

```bash
rsync -av --delete ~/.hermes/skills/ "$WORKDIR/" \
    --exclude '.git' \
    --exclude 'html-ppt' \
    --exclude 'ppt-master' \
    --exclude '.curator_backups' \   # <-- Critical: curator backups are 100-300MB+
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '.venv'
```

### Use `.gitignore` proactively

```gitignore
.curator_backups/
*.gguf
*.safetensors
*.bin
node_modules/
__pycache__/
.venv/
```

### For accidental large-file commits already in history

If a large file was committed and pushed, you must rewrite history:

```bash
# Remove from git index (keeps local file)
git rm --cached path/to/large/file

# Commit the removal
git commit -m "Remove oversized file"

# Force push (required because history changed)
git push origin main --force
```

**Warning**: `git push --force` rewrites public history. Coordinate with collaborators.

## BFG Repo-Cleaner (Faster History Rewrite)

For repos with many large files or large history:

```bash
# Download the BFG jar
curl -L -o bfg.jar https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# Clone fresh (BFG requires a fresh clone)
git clone --mirror https://github.com/user/repo.git
cd repo.git

# Delete all files > 100MB (or specific patterns)
java -jar bfg.jar --strip-blobs-bigger-than 100M .

# Clean up
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force
```

## GitHub LFS (Git Large File Storage)

For genuinely large files you need in version control:

```bash
# Install git-lfs
git lfs install

# Track file types
git lfs track "*.gguf"
git lfs track "*.safetensors"
git lfs track "*.pth"

# Now commit normally — Git LFS handles the large files
git add .
git commit -m "Add model weights"
git push
```

Note: GitHub LFS has its own storage quotas (1 GB free).

## Quick Diagnostic

```bash
# Find files > 50MB in current directory
find . -type f -size +50M -exec ls -lh {} \;

# Check for large files in git history
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | grep blob | sort -k3 -n -r | head -20

# Check repo size on GitHub
gh repo view owner/repo --json diskUsage
```
