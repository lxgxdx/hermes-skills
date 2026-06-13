---
name: hermes-model-metadata-debugging
description: Debug how Hermes resolves per-model capabilities (context window, max output tokens, pricing) and override them when a provider's actual API specs diverge from the bundled metadata. Load when a user reports "Hermes caps me at X tokens but the model actually supports Y", "my new model isn't recognized", "where does the 200K/32K/1M limit come from", or asks to patch model_metadata.py / models_dev.py.
category: software-development
---

# Hermes Model Metadata Debugging

Hermes bundles hardcoded model capability tables in `agent/model_metadata.py` and `agent/models_dev.py`. When a provider ships a new model or revises an existing one's window, Hermes is wrong until someone patches the source. This skill is the playbook for figuring out (a) where a specific number is coming from, and (b) the cleanest way to fix or override it.

## When to load this skill

Trigger phrases:
- "Model X shows the wrong context window in Hermes"
- "Why am I capped at 200K / 32K when the model supports 1M?"
- "Where does Hermes get model metadata from?"
- "How do I override the context window for provider X?"
- "I added a new provider/model and Hermes doesn't recognize it"
- "models.dev says 1M but Hermes says 200K"

Do NOT load this for: token-cost accounting (that's `providers.py` pricing tables), routing/fallback logic, or session context-compression triggers (those are in `agent/context_compressor.py`).

## The resolution chain (read this first)

Hermes resolves a model's effective context window in this order:

1. **User override** — `~/.hermes/config.yaml` `model.overrides[<provider/model>].context_window` (and the env-var equivalent). Highest priority.
2. **Per-model hardcoded entry** — `agent/model_metadata.py:_MODEL_PROVIDER_DEFAULTS`, longest substring match wins. Specific models (e.g. `"MiniMaxAI/MiniMax-M2.5": 204800`) are listed BEFORE generic substrings (e.g. `"minimax": 204800`).
3. **models.dev live fetch** — `agent/models_dev.py` calls `https://models.dev/api.json` and caches per-model `context_window`. **Failure mode**: if the network call fails, the fallback is `context_window: int = 200000` (see line 408, 494).
4. **Generic substring fallback** — the same `_MODEL_PROVIDER_DEFAULTS` table, matched by provider/model substring.
5. **Hardcoded safety floor** — `200000` in `models_dev.py` and `conversation_loop.py` line 2193 (error-classification default).

The **substring matching order matters**. If you see `"minimax": 204800` in the table and your model is `MiniMax-M3`, the catch-all `minimax` matches first UNLESS a more specific entry is listed before it. **Longest-first is documented behavior** in the table comment.

## Step-by-step: trace a wrong context window

```bash
# 1. Confirm what the user thinks the model supports
#    (ask for the official docs link — do NOT trust secondhand claims)

# 2. Find which file holds the metadata
cd ~/.hermes/hermes-agent
grep -n -B 1 -A 2 "minimax\|M3" agent/model_metadata.py

# 3. Read the surrounding block to understand substring priority
sed -n '195,215p' agent/model_metadata.py

# 4. Check whether the model has a per-model entry vs only a catch-all
#    If only a catch-all exists, that's the bug.

# 5. Verify the LIVE API actually returns what the docs claim
curl -s "$PROVIDER_BASE_URL/v1/models" | jq '.data[] | select(.id|contains("M3")) | {id, context_length, max_context_length}'
```

**Do NOT skip step 5.** The whole point of the bundled table is to avoid trusting the network every call — but when the table is wrong, the network IS the source of truth.

## Three override paths (in increasing invasiveness)

### Path A: config.yaml override (no source patch, survives upgrades)

```yaml
# ~/.hermes/config.yaml
model:
  default: minimax-cn/MiniMax-M3
  overrides:
    "minimax-cn/MiniMax-M3":
      context_window: 1048576   # 1M
```

Pro: zero source change, easy to revert, no merge conflict on `hermes update`.
Con: requires knowing the exact key shape Hermes checks. **Verify it works** by reading `model_metadata.py:_resolve_context_length` (or whatever the current resolver is named — search for "overrides" in that file).

### Path B: patch the bundled table (1-line change, persistent)

Edit `agent/model_metadata.py` around the provider's block. Add a **specific** entry ABOVE the catch-all substring, e.g.:

```python
# MiniMax — M3 ships with 1M context per <official doc URL>
"MiniMaxAI/MiniMax-M3": 1048576,   # 1M context (MUST come BEFORE "minimax" catch-all)
"minimax": 204800,                  # legacy models
```

Then upstream the change as a PR with a citation. This is the right answer when the bundled metadata is genuinely wrong — but it requires regenerating any compiled `*.pyc`/wheel in the active venv.

### Path C: fix models.dev fetch (last resort)

Only if the issue is the network fetch returning stale data, not the bundled table. Check `agent/models_dev.py` for the fetch URL and cache TTL.

## Common pitfalls

- **"I added a generic entry and it didn't take effect."** — Substring matching is longest-first. Your new `"minimax": 1048576` overrides the more specific `"MiniMaxAI/MiniMax-M3"` only if it appears LATER in the dict AND no other entry is longer than `"minimax"`. **Add the specific entry, not the generic one.**

- **"I patched the file but the runtime still uses 200K."** — You're running a stale `.pyc`. Run `find ~/.hermes -name "*.pyc" -delete` or restart the gateway. Also check whether `~/.hermes/hermes-agent/` is a symlink to a different worktree (Hermes worktrees share a venv — see AGENTS.md).

- **"The provider docs say 1M but the API rejects 800K requests."** — Distinguish *advertised* context window from *effective* context window. Some providers advertise the input window but cap output separately. Check `max_output_tokens` separately in `model_metadata.py` and the API's own `usage` block in a test request.

- **"Conflating substring with provider name."** — `_MODEL_PROVIDER_DEFAULTS` keys are model substrings, NOT provider names. The provider is matched separately (see `providers.py`). Don't conflate `minimax-cn` (provider) with `minimax` (model substring) — they look similar but the resolver uses different inputs.

- **"Trusting secondary sources."** — When a user says "X model supports Y context", demand the official API doc URL. Secondhand claims and outdated Medium articles are how 204800 ends up hardcoded for a 1M model. **Never patch on a secondhand claim** — the user prefers verification-first.

## Verification step (always do this)

After any override:

```bash
# 1. Restart the gateway/CLI to pick up the change
hermes restart  # or kill the running process

# 2. Run a probe that triggers context-window reporting
hermes status
# Look for the model's "context_window" field

# 3. Or grep the resolved value at runtime
python3 -c "from hermes_cli.model_metadata import _resolve_context_length; print(_resolve_context_length('minimax-cn', 'MiniMax-M3'))"
```

If the value didn't change, you didn't actually override the right path. Re-read the resolution chain.

## Related files

- `agent/model_metadata.py` — the main table. Two dicts: `_MODEL_PROVIDER_DEFAULTS` (substring → window) and `_OPENROUTER_MODEL_OVERRIDES` (full model ID → window).
- `agent/models_dev.py` — network fetch + cache. Has a `200000` fallback at lines 408 and 494.
- `agent/conversation_loop.py` line 2193 — error classifier uses `getattr(_compressor, "context_length", 200000)`. If you're debugging 200K-related errors, this is the spot.
- `agent/context_compressor.py` line 543 — comment explicitly mentions "200K → 32K" as the assumed model-switch pattern. If you change the floor, update the comment.
- `hermes_cli/providers.py` — `minimax-cn` is registered with `transport="anthropic_messages"`. **The context window is NOT set in providers.py** — it's purely in model_metadata.py. Don't waste time editing the wrong file.

## Support files

- `references/minimax-m3-case.md` — the actual session trace from 2026-06-01. Read this to see the search commands and the layering findings applied to a real model.
- `scripts/trace-context-window.py` — runs the resolver end-to-end and prints which layer (override / table / models.dev / fallback) supplied the number. Use this when debugging a new model — saves you from re-grepping the source.

## When to upstream vs when to keep it local

**Upstream** (open a PR against the hermes-agent repo) when:
- The bundled metadata is just factually wrong (e.g. 204800 vs 1M for a real model)
- The fix is one line with a citation
- You have the official doc URL

**Keep local** (config override) when:
- You're on a beta/private model
- The provider hasn't published a stable doc yet
- You can't verify the number independently
