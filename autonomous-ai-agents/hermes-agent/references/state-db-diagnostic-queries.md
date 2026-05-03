# Hermes State.db Diagnostic Queries

Reusable SQL queries against `~/.hermes/state.db` for skill efficiency analysis and usage diagnostics.

**Connection:**
```python
import sqlite3
from pathlib import Path
db_path = Path.home() / ".hermes" / "state.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
```

---

## Skill Efficiency: Follow-up Quality

Measures how often an Agent repeats `skill_view` after loading a skill — high repeat count means the Agent isn't remembering the workflow and must re-read it every time.

```python
import json
from collections import defaultdict, Counter

cursor.execute("""
    SELECT m.tool_calls
    FROM messages m
    WHERE m.tool_calls IS NOT NULL AND m.tool_calls != ''
    ORDER BY m.timestamp
""")

skill_followup = defaultdict(list)
all_rows = cursor.fetchall()

for i, row in enumerate(all_rows):
    try:
        tools = json.loads(row['tool_calls']) if row['tool_calls'] else []
        for t in tools:
            func = t.get('function', {})
            name = func.get('name', '')
            if name == 'skill_view':
                args = json.loads(func.get('arguments', '{}')) if isinstance(func.get('arguments', '{}'), str) else func.get('arguments', {})
                skill_name = args.get('name', '')
                followups = []
                for j in range(i+1, min(i+4, len(all_rows))):
                    next_tc = all_rows[j]['tool_calls']
                    try:
                        next_tools = json.loads(next_tc) if next_tc else []
                        for nt in next_tools:
                            followups.append(nt.get('function', {}).get('name', ''))
                    except:
                        pass
                skill_followup[skill_name].extend(followups)
    except:
        pass

for skill, tools in sorted(skill_followup.items(), key=lambda x: -len(x[1])):
    c = Counter(tools)
    useful = sum(c.get(k, 0) for k in ['terminal', 'read_file', 'write_file', 'execute_code', 'patch'])
    wasted = c.get('skill_view', 0)
    print(f"{skill}: useful={useful} wasted={wasted}")
```

**Interpretation:**
- `wasted > 0`: Agent repeatedly re-reads this skill → needs optimization or better memorization
- `useful / (useful + wasted) > 0.8`: High efficiency, skill content is well-internalized

---

## Tool Call Distribution by Source

```python
cursor.execute("""
    SELECT m.session_id, m.tool_calls, s.source
    FROM messages m
    JOIN sessions s ON m.session_id = s.id
    WHERE m.tool_calls IS NOT NULL AND m.tool_calls != ''
""")

from collections import defaultdict, Counter
tool_per_source = defaultdict(Counter)

for row in cursor.fetchall():
    source = row['source'] or 'unknown'
    try:
        tools = json.loads(row['tool_calls'])
        for t in tools:
            name = t.get('function', {}).get('name', 'unknown')
            tool_per_source[source][name] += 1
    except:
        pass

for source, counter in sorted(tool_per_source.items(), key=lambda x: -sum(x[1].values())):
    total = sum(counter.values())
    print(f"\n[{source}] ({total} calls)")
    for name, cnt in counter.most_common(5):
        print(f"  {name:<35} {cnt:>5}")
```

---

## Task Topic Distribution from User Messages

```python
task_keywords = {
    'PPT': ['ppt', '幻灯', '演示文稿', 'slides', 'deck', '生成PPT'],
    'OCR': ['ocr', 'pdf转', '扫描件', '图片识别'],
    '知识库': ['gbrain', '脑库', '知识库', '同步对话'],
    '智能家居': ['home assistant', 'ha', 'zigbee', 'Aqara'],
    'Docker部署': ['docker', 'unraid', '部署', '安装'],
    'GitHub': ['github', '搜索'],
    '信息稿/统战': ['信息稿', '统战', '统一战线'],
    'Wiki构建': ['wiki', '抓取文档', '构建wiki'],
    'Excel/台账': ['excel', '台账', 'xlsx'],
    '调试排错': ['调试', 'error', 'failed', '报错'],
}

topic_counts = Counter()
cursor.execute("""
    SELECT m.content, s.source
    FROM messages m
    JOIN sessions s ON m.session_id = s.id
    WHERE m.role = 'user'
    ORDER BY m.timestamp
""")

for (content, source) in cursor.fetchall():
    for topic, keywords in task_keywords.items():
        if any(kw in (content or '').lower() for kw in keywords):
            topic_counts[topic] += 1
            break

for topic, cnt in topic_counts.most_common():
    print(f"  {topic:<15} {cnt:>5}")
```

---

## Session Complexity by Source

```python
cursor.execute("""
    SELECT source,
           AVG(message_count) as avg_msg,
           AVG(tool_call_count) as avg_tool,
           MAX(message_count) as max_msg,
           MAX(tool_call_count) as max_tool,
           COUNT(*) as cnt
    FROM sessions
    GROUP BY source
    ORDER BY cnt DESC
""")
for row in cursor.fetchall():
    print(f"  {row[0]:<12} {row[5]:>4}sess  msg={row[1]:.1f}  tool={row[2]:.1f}  max_msg={row[3]}  max_tool={row[4]}")
```

---

## Cron Job Success Rate

```python
cursor.execute("""
    SELECT ended_at, end_reason, ended_at - started_at as duration, title
    FROM sessions
    WHERE source = 'cron'
    ORDER BY ended_at DESC
    LIMIT 50
""")

success = fail = 0
durations = []
for row in cursor.fetchall():
    reason = row['end_reason']
    dur = row['duration'] or 0
    durations.append(dur)
    if reason == 'cron_complete':
        success += 1
    else:
        fail += 1

print(f"Cron success: {success}/{success+fail} ({success*100//(success+fail)}%)")
print(f"Avg duration: {sum(durations)/len(durations)/60:.1f} min")
```

---

## Installed vs Called Skills

```python
# What skills are actually in ~/.hermes/skills/
skill_dir = Path.home() / ".hermes" / "skills"
installed = {p.name for p in skill_dir.iterdir()} if skill_dir.exists() else set()

# What skills were actually called via skill_view
real_calls = Counter()
cursor.execute("SELECT m.tool_calls FROM messages m WHERE m.tool_calls IS NOT NULL")
for (tc_str,) in cursor.fetchall():
    try:
        for t in json.loads(tc_str):
            args = json.loads(t['function']['arguments']) if isinstance(t['function']['arguments'], str) else t['function']['arguments']
            if t['function']['name'] == 'skill_view' and args.get('name'):
                real_calls[args['name']] += 1
    except:
        pass

never_called = installed - set(real_calls.keys())
print(f"Installed: {len(installed)}, Called: {len(real_calls)}, Never called: {len(never_called)}")
for s in sorted(never_called):
    print(f"  - {s}")
```
