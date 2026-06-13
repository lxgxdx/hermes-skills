---
name: x-twitter-cli
description: Class-level guide to interacting with X (Twitter) from the terminal — covers the two main CLI tools (x-cli and xurl), their auth models, command surfaces, when to prefer one over the other, and the per-CLI recipes for posting, reading timelines, searching, DMs, and media uploads. Load when you need to post to or read from X/Twitter programmatically.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [twitter, x, social-media, x-cli, xurl, official-api, posts, timelines, dms, media]
    related_skills: []
---

# X (Twitter) CLI Tools — Class-Level Guide

Two terminal CLIs cover the X / Twitter API surface from Hermes:

| Tool | Author | Auth model | Best for |
|------|--------|------------|----------|
| **[xurl](references/xurl-official.md)** | X developer platform (official) | X API OAuth app credentials (`xurl auth set`) | Shortcut commands, raw v2 endpoint access, DMs, media uploads, multi-app workflows |
| **[x-cli (xitter)](references/xitter-x-cli.md)** | Infatoshi community | X API OAuth keys (X_API_KEY/SECRET/BEARER/ACCESS) | Posting, timelines, mentions, bookmarks, user lookups via a Python-based CLI |

> Both are full-featured and call the official X v2 API. The difference is mostly ergonomics (command shape, auth setup) and the specific command set each exposes. Pick the one whose command set matches what you need; both can be installed side-by-side.

## Sections

1. **[xurl — Official X CLI](references/xurl-official.md)** — shortcut commands + raw v2 access. JSON output. The most "complete" option: posts, replies, quotes, deletes, searches, timelines, mentions, likes, reposts, bookmarks, follows, blocks, mutes, DMs, media uploads, multi-account.
2. **[x-cli (xitter)](references/xitter-x-cli.md)** — Python-based CLI for posting, reading timelines, searching, liking, retweeting, bookmarks, mentions, user lookups.

## When to Use Which

- **Use xurl** when you need any of: DM sending, media uploads, raw v2 endpoint access, multi-account workflows, or you want the X-platform-maintained tool. It is the most feature-complete of the two.
- **Use x-cli (xitter)** when you only need core read/post/engage operations and prefer a Python install via `uv`.

For the vast majority of read-and-post workflows, either tool works. Pick by installed availability and command-style preference.

## When to Load This Umbrella

- Posting to or reading from X/Twitter programmatically
- Deciding between xurl and x-cli for a new project
- Auditing a workflow that already uses one of the CLIs and considering switching
- Setting up X API auth in either model (env vars for x-cli, `xurl auth set` for xurl)

## Auth Setup Summary

**xurl:**
```bash
# Install
brew install xdevplatform/tap/xurl   # or download binary from GitHub releases
# Auth
xurl auth set   # interactive: paste your X API keys/tokens
```

**x-cli (xitter):**
```bash
# Install
uv tool install x-cli
# Auth: set env vars (or put in ~/.hermes/.env)
export X_API_KEY="..."
export X_API_SECRET="..."
export X_BEARER_TOKEN="..."
export X_ACCESS_TOKEN="..."
export X_ACCESS_TOKEN_SECRET="..."
```

## Related Skills

None — this is the only X/Twitter surface in the skill library. If you need general social-media scheduling or multi-platform posting, that would be a different skill (none currently exists).
