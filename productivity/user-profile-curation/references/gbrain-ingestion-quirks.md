# GBrain ingestion & verification quirks

Two gotchas observed in the user-profile-curation v5 run (2026-06-05)
that future runs should bake in, not rediscover.

## Gotcha 1: "already embedded" ≠ "findable via the new slug"

**Symptom**: After `gbrain put` + `gbrain embed --slugs <slug>`, the
embed output reads `<slug>: all N chunks already embedded`. You assume
the slug is in the index. You run a generic `gbrain search "<slug>"`
and get nothing — but the slug string literally never appears in the
chunks themselves (only its content does). You panic and re-embed.

**Why it happens**: The embed command confirms the chunks are in the
vector index. The slug is a GBrain-side label, not text in the chunks.
Searching for the literal slug never matches.

**Fix**: Verify with a phrase taken from the report content, not the
slug. Use a unique 3-5 word phrase (e.g. "P17 民族团结进步促进法 v5
增量"). If the top hit is your new slug with similarity >0.85, ingestion
actually worked. Top hit being a different slug (like an older
`daily/YYYY-MM-DD`) means your new slug is not being surfaced — re-embed.

**Reverse-verification template**:

```bash
PATH="$HOME/.bun/bin:$PATH" gbrain put user-profile-YYYYMMDD \
  < ~/.hermes/memories/daily/YYYY-MM-DD-user-model-snapshot.md
PATH="$HOME/.bun/bin:$PATH" gbrain embed --slugs user-profile-YYYYMMDD
# VERIFY with a unique content phrase, NOT the slug
PATH="$HOME/.bun/bin:$PATH" gbrain search "<unique 3-5 word phrase from report>"
# Expect: top hit = user-profile-YYYYMMDD, similarity >0.85
```

## Gotcha 2: GBrain stats lag behind put

`gbrain stats` may still show the old page/chunk count for ~1 second
after `gbrain put` returns success. Don't trust stats as the ingestion
verifier. Use the semantic search verification (Gotcha 1) instead.

## When stats IS the right tool

- After a full dream cycle (multiple slugs ingested in one batch),
  `gbrain stats` is the only thing that tells you aggregate health
  (`Pages`, `Chunks`, `Embedded`, coverage %).
- After a single `user-profile-YYYYMMDD` put, stats is overkill and
  can mislead. Always pair single puts with semantic search.

## Common false alarms (ignore these)

- `gbrain doctor --json` reporting `resolver_health: warn` with "10
  warnings (MECE + DRY)" — this is a known false positive in 2026-06,
  not a real problem.
- `embed --stale` returning "0 chunks embedded" when coverage is
  already 100% — expected, no action needed.
