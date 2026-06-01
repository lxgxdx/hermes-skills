# Case study: MiniMax M3 "200K vs 1M" question

**Date**: 2026-06-01
**Symptom**: User reported "M3 supports 1M context but Hermes still caps at 200K."
**Resolution**: Confirmed Hermes source is hardcoded 204,800; user was asked to verify with the official API before any patch.

## What was traced

1. `~/.hermes/config.yaml` line 2: `default: minimax-cn/MiniMax-M3` — confirmed active model.
2. `hermes_cli/providers.py:130-133` — `minimax-cn` provider registered, no context limit set there.
3. `agent/model_metadata.py:203-205` — comment says "official docs: 204,800 context for all models" with a doc URL. The catch-all `"minimax": 204800`.
4. `agent/model_metadata.py:243` — explicit `"MiniMaxAI/MiniMax-M2.5": 204800` listed for M2.5.
5. **No M3-specific entry** — so M3 falls through to the `minimax` catch-all.
6. `agent/models_dev.py:408,494` — network fetch fallback is 200000.
7. `agent/conversation_loop.py:2193` — error classifier default is 200000.
8. `agent/context_compressor.py:543` — comment "200K → 32K" model-switch scenario.

## What the user was told

- Hermes is the client, MiniMax is the source of truth.
- The 204800 is from a doc snapshot, not a hard constraint.
- Three fix paths: config.yaml override, single-line source patch, or wait for upstream.
- **Asked user to confirm the 1M claim against the official API before patching anything.**

## Lesson

This is exactly the pattern this skill exists for: provider doc evolution > Hermes bundled table. The fix is always the same — verify the API, then patch. The 1M claim was unverified, so no patch was made; the question is now parked in user memory as "verify with official source before changing model metadata."

## Related grep one-liner

If you see the same question with a different model, this one-liner finds the relevant block in 1 second:

```bash
cd ~/.hermes/hermes-agent && \
  grep -n -B 1 -A 2 "minimax\|<provider-substring>" agent/model_metadata.py | head -40
```
