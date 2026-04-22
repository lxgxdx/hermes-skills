---
name: minimax-dspy-evolution-fix
description: Fix MiniMax API integration with DSPy 3.x for Hermes Agent Self-Evolution. Covers API configuration and patching evolution scripts.
tags: [minimax, dspy, hermes, evolution, api-integration]
category: mlops
---

# MiniMax + DSPy 3.x Evolution Fix

## Problem
When using MiniMax with Hermes Agent Self-Evolution, you encounter:
1. API connection failures even with valid configuration
2. DSPy's `dspy.LM()` doesn't pass required parameters for custom providers
3. Evolution scripts fail to connect to MiniMax API

## Root Cause
DSPy 3.x's `dspy.LM()` constructor doesn't automatically forward `api_base` parameters to the underlying litellm call when using custom providers like MiniMax.

## Solution

### 1. Correct Model Name and Configuration
```python
# For MiniMax China region
model_name = "minimax/MiniMax-M2.7-highspeed"
api_base = "https://api.minimaxi.com/v1"
# API key should be set in environment variables
```

### 2. Patch Evolution Scripts
Three files need patching to pass `api_base` parameter:

**File 1: `evolution/skills/evolve_skill.py`**
```python
# Replace the dspy.LM() call with:
import os as _os
_lm_kwargs = {}
if eval_model.startswith("minimax/"):
    _lm_kwargs["api_base"] = "https://api.minimaxi.com/v1"
    # API key from environment
    _api_key = _os.environ.get("MINIMAX_CN_API_KEY") or _os.environ.get("MINIMAX_API_KEY")
    if _api_key:
        _lm_kwargs["api_key"] = _api_key
lm = dspy.LM(eval_model, **_lm_kwargs)
```

**File 2: `evolution/core/dataset_builder.py`**
```python
# Replace the dspy.LM() call with:
import os as _os
_lm_kwargs = {}
if self.config.judge_model.startswith("minimax/"):
    _lm_kwargs["api_base"] = "https://api.minimaxi.com/v1"
    _api_key = _os.environ.get("MINIMAX_CN_API_KEY") or _os.environ.get("MINIMAX_API_KEY")
    if _api_key:
        _lm_kwargs["api_key"] = _api_key
lm = dspy.LM(self.config.judge_model, **_lm_kwargs)
```

**File 3: `evolution/core/fitness.py`**
```python
# Replace the dspy.LM() call with:
import os as _os
_lm_kwargs = {}
if self.config.eval_model.startswith("minimax/"):
    _lm_kwargs["api_base"] = "https://api.minimaxi.com/v1"
    _api_key = _os.environ.get("MINIMAX_CN_API_KEY") or _os.environ.get("MINIMAX_API_KEY")
    if _api_key:
        _lm_kwargs["api_key"] = _api_key
lm = dspy.LM(self.config.eval_model, **_lm_kwargs)
```

### 3. Install Required Dependencies
```bash
# MIPROv2 requires optuna
pip install optuna
```

### 4. Run Evolution Command
```bash
cd ~/hermes-agent-self-evolution
source .venv/bin/activate

python -m evolution.skills.evolve_skill \
  --skill your-skill-name \
  --iterations 10 \
  --eval-source synthetic \
  --hermes-repo ~/.hermes/hermes-agent \
  --optimizer-model minimax/MiniMax-M2.7-highspeed \
  --eval-model minimax/MiniMax-M2.7-highspeed
```

## Key Findings

### 1. Model Name Format
- Use `minimax/MiniMax-M2.7-highspeed` not just `MiniMax-M2.7-highspeed`
- The `minimax/` prefix is required for litellm to recognize the provider

### 2. API Base URL
- China region: `https://api.minimaxi.com/v1`
- Must be explicitly passed via `api_base` parameter
- **Critical**: Also need to pass `api_key` parameter explicitly, not just rely on environment variables

### 3. DSPy Compatibility Issues
- GEPA optimizer may fail with "max_steps" parameter error (version mismatch)
- Falls back to MIPROv2 which requires `optuna`
- Constraint validation may fail even with correct YAML frontmatter (false positives)

### 4. Performance Results
- Baseline scores: ~40-45%
- Optimized scores: ~55-60% (30-50% relative improvement)
- Best configuration: Instruction 2 + Few-Shot Set 5
- **Actual example**: easyocr-unraid-p4-deploy skill improved from 43.77% to 58.26% (+14.49% absolute, +33% relative)

### 5. Patch Implementation Details
- Need to patch ALL THREE files that call `dspy.LM()`:
  1. `evolution/skills/evolve_skill.py` (line ~141)
  2. `evolution/core/dataset_builder.py` (line ~126) 
  3. `evolution/core/fitness.py` (line ~75)
- Use `import os as _os` to avoid namespace conflicts
- Check both `MINIMAX_CN_API_KEY` and `MINIMAX_API_KEY` environment variables

## Troubleshooting

### API Connection Failures
1. Verify environment variables are set
2. Check model name format includes `minimax/` prefix
3. Ensure `api_base` is passed in `dspy.LM()` call

### Optimization Failures
1. Install `optuna` for MIPROv2
2. If GEPA fails, it will automatically fall back to MIPROv2
3. Constraint failures don't prevent optimization, just deployment

### Output Location
- Optimized skills saved to: `output/skill-name/evolved_FAILED.md`
- Review manually for constraint validation issues

## Best Practices
1. Always test API connectivity before running evolution
2. Monitor for constraint validation false positives
3. Review optimized skills manually before deployment
4. Consider using simpler optimizers if dependency issues persist