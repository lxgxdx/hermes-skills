#!/usr/bin/env python3
"""
Trace how Hermes resolves the context window for a given provider+model.

Usage:
    python3 trace-context-window.py <provider> <model_id>
    e.g. python3 trace-context-window.py minimax-cn MiniMax-M3

Output: the resolved context window plus the path it took (override →
table entry → models.dev → fallback), so you can see at a glance which
layer is supplying the number.
"""
import sys
from pathlib import Path

HERMES_AGENT = Path.home() / ".hermes" / "hermes-agent"
sys.path.insert(0, str(HERMES_AGENT))

try:
    from agent.model_metadata import _MODEL_PROVIDER_DEFAULTS, _resolve_context_length
    from agent.models_dev import _fetched_windows
except ImportError as e:
    print(f"ERROR: cannot import Hermes modules. Is the venv active?\n  {e}")
    sys.exit(2)

def longest_substring_match(table, model_id):
    """Mirror Hermes' longest-first substring logic."""
    best_key, best_val = None, None
    for key, val in table.items():
        if key in model_id and (best_key is None or len(key) > len(best_key)):
            best_key, best_val = key, val
    return best_key, best_val

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    provider, model_id = sys.argv[1], sys.argv[2]
    full_id = f"{provider}/{model_id}"

    print(f"=== Resolving context window for {full_id} ===\n")

    # 1. Check the bundled table
    matched_key, matched_val = longest_substring_match(_MODEL_PROVIDER_DEFAULTS, model_id)
    if matched_key:
        print(f"[1] Bundled table HIT")
        print(f"    Substring key:  '{matched_key}'")
        print(f"    Context window: {matched_val:,} tokens")
    else:
        print(f"[1] Bundled table MISS — no substring match for '{model_id}'")

    # 2. Check models.dev cache
    if model_id in _fetched_windows:
        print(f"\n[2] models.dev cache HIT: {_fetched_windows[model_id]:,} tokens")
    else:
        print(f"\n[2] models.dev cache MISS (will fetch on first call)")

    # 3. Resolve via the official function
    try:
        resolved = _resolve_context_length(provider, model_id)
        print(f"\n[3] Resolved value: {resolved:,} tokens")
    except Exception as e:
        print(f"\n[3] _resolve_context_length raised: {e}")

    # 4. Show the actual resolver code so the user can audit the path
    try:
        import inspect
        print(f"\n=== Resolver source (for audit) ===")
        print(inspect.getsource(_resolve_context_length))
    except Exception:
        pass

if __name__ == "__main__":
    main()
