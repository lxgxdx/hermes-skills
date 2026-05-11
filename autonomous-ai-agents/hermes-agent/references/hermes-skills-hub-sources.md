# Hermes Skills Hub — 数据源分析

## 核心文件

- `~/.hermes/hermes-agent/tools/skills_hub.py` — Skills Hub 核心库（3200+ 行）
- `~/.hermes/hermes-agent/hermes_cli/skills_hub.py` — CLI 封装

## unified_search 源码位置

`tools/skills_hub.py` 第 3209 行：

```python
def unified_search(query: str, sources: List[SkillSource],
                   source_filter: str = "all", limit: int = 10) -> List[SkillMeta]:
    """Search all sources (in parallel) and merge results."""
    all_results, _, _ = parallel_search_sources(
        sources,
        query=query,
        source_filter=source_filter,
        overall_timeout=30,
    )
    # Deduplicate by name, preferring higher trust levels
    _TRUST_RANK = {"builtin": 2, "trusted": 1, "community": 0}
    seen: Dict[str, SkillMeta] = {}
    for r in all_results:
        if r.name not in seen:
            seen[r.name] = r
        elif _TRUST_RANK.get(r.trust_level, 0) > _TRUST_RANK.get(seen[r.name].trust_level, 0):
            seen[r.name] = r
    deduped = list(seen.values())
    return deduped[:limit]
```

## 内置 SkillSource（source_id 列表）

| Class | source_id | 描述 | Trust Level |
|-------|-----------|------|-------------|
| `GitHubSource` | `github` | 任意 GitHub 仓库 | community |
| `ClawHubSource` | `clawhub` | clawhub.ai 市场 | community |
| `LobeHubSource` | `lobehub` | lobehub agents 索引 | community |

## 关键源码片段

### parallel_search_sources（多源并行搜索）

```python
# tools/skills_hub.py 第 3123 行
return src.source_id(), src.search(query, limit=limit)
```

API 搜索来源（第 3154 行）：
```python
_api_source_ids = frozenset({"github", "skills-sh", "clawhub",
                              "lobehub", "hermes-index", "optional-skills"})
```

### SkillMeta 数据结构

```python
@dataclass
class SkillMeta:
    name: str
    description: str
    source: str           # "official", "github", "clawhub", "claude-marketplace", "lobehub"
    identifier: str        # source-specific ID
    trust_level: str      # "builtin" | "trusted" | "community"
    repo: Optional[str] = None
    path: Optional[str] = None
    tags: List[str] = field(default_factory=list)
```

## 安装路径

- **用户安装的 hub skills**: `~/.hermes/skills/`（按 category 子目录组织）
- **内置 skills**: `~/.hermes/hermes-agent/skills/`

## hub lock 文件

```
~/.hermes/skills/.hub/lock.json
```

记录每个已安装 skill 的来源、commit hash、安装时间。

## 调试：查看所有可用 sources

```python
import sys
sys.path.insert(0, '~/.hermes/hermes-agent')
from tools.skills_hub import ALL_SOURCES
for s in ALL_SOURCES:
    print(s.source_id(), type(s).__name__)
```

## 与 Claude Code find-skill 的对比

| | Hermes `hermes skills search` | Claude Code `find-skill` |
|--|--|--|
| 数据源数 | ~3（clawhub, lobehub, github） | 14 |
| skills 数量 | 较少（社区规模） | 4800+ |
| 信任体系 | builtin/trusted/community 三级 | 多源排名（按 GitHub stars） |
| 安装命令 | `hermes skills install` | `find-skill install` |
| 内置还是外部 | 内置 | 外部 skill |

Hermes 的优势是内置无需安装；Claude Code 的优势是生态更丰富。
