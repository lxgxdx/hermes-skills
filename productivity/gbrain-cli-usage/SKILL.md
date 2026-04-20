---
name: gbrain-cli-usage
description: Correct way to invoke GBrain CLI (bun package, not Python)
category: productivity
---

# GBrain CLI Usage

GBrain is a bun package — it CANNOT be invoked via `python -m gbrain` or direct `gbrain` command (shebang uses `#!/usr/bin/env bun` which fails if bun isn't in PATH).

## Correct invocation

```bash
/home/lxgxdx/.bun/bin/bun /home/lxgxdx/.bun/bin/gbrain <command> [args]
```

Or from the gbrain directory:
```bash
cd /home/lxgxdx/gbrain && bun src/cli.ts <command> [args]
```

## Common commands

```bash
# Query brain
/home/lxgxdx/.bun/bin/bun /home/lxgxdx/.bun/bin/gbrain query "search terms"

# List all pages
/home/lxgxdx/.bun/bin/bun /home/lxgxdx/.bun/bin/gbrain list

# Health check
/home/lxgxdx/.bun/bin/bun /home/lxgxdx/.bun/bin/gbrain doctor --fast
```

## PATH issue

`which gbrain` returns nothing because the shebang `#!/usr/bin/env bun` can't find bun in the environment's PATH. The bun binary lives at `/home/lxgxdx/.bun/bin/bun` and the gbrain CLI at `/home/lxgxdx/.bun/bin/gbrain` (symlink to `../install/global/node_modules/gbrain/src/cli.ts`).
