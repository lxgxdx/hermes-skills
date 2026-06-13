---
name: high-quality-skill-design
description: >
  Design and restructure Hermes Agent SKILL.md files using patterns from
  ConardLi/web-design-skill — role identity, scope matrix, decision-driven
  workflows, design declaration, hard rules, anti-cliché principles, and
  pre-delivery checklists. Use this when creating new skills from scratch
  or upgrading existing ones that are too procedural/mechanical.
tags: [skill-design, prompt-engineering, hermes-agent, writing, best-practices]
category: productivity
---

# High-Quality Hermes Skill Design

This skill captures the design principles and structural patterns from
[ConardLi/web-design-skill](https://github.com/ConardLi/web-design-skill)
(a 5.9k-star repository that defines how to write Agent skills that produce
"stunning, not functional" outputs).

Apply this pattern when:
- Creating a new SKILL.md from scratch
- An existing skill is purely procedural ("do step 1, step 2...") without
  design judgment or decision-making guidance
- Users are getting mechanical/predictable outputs from a skill
- The skill involves creative or design-oriented work

---

## Core Principles

### 1. Role Identity — Not a Tool, an Expert

Bad: "This skill uses ppt-master to generate PPTX files."
Good: "This skill positions the Agent as a senior presentation engineer who
transforms raw input into polished, natively-editable decks."

**Format**: First paragraph of `# Title` section should establish identity,
not describe the tool. Use the pattern:

> This skill positions the Agent as a [ROLE] who [HIGH-LEVEL PURPOSE].
> You are not just [NARROW ACTIVITY] — you're [BROADER RESPONSIBILITY].

### 2. Scope Declaration (✅ / ❌)

Always include a Scope section with explicit applicable ❌ non-applicable
use cases. Use a bullet list, not paragraph:

```markdown
## Scope

✅ **Applicable**:
- Use case A
- Use case B

❌ **Not applicable**:
- Use case C
- Use case D
```

This prevents the Agent from using the skill in wrong contexts.

### 3. Situational Decision-Making

Instead of a fixed "do these steps every time," include a **decision matrix**
in Step 1 that tells the Agent when to ask questions vs. when to proceed:

```markdown
| Scenario | Action |
|---|---|
| "Do X with no details" | ✅ Ask extensively: param1, param2 |
| "Use this spec to do X for Y audience" | ❌ Enough info — start |
| "Turn screenshot into X" | ⚠️ Only ask if behavior is unclear |
```

Key instruction to include above the table: **"Do not mechanically fire off
a long list of questions every time."** This prevents the Agent from being
annoyingly verbose in well-specified scenarios.

### 4. Design Declaration Step

Before the Agent executes, have them **declare design direction in Markdown**
so the user can confirm early. This prevents whole-work re-dos:

```markdown
Design Direction:
- Parameter 1
- Parameter 2
- Key decisions
```

The format should be simple Markdown — the user confirms or adjusts before
the Agent invests effort in full generation.

### 5. Hard Rules Section

Include a "Hard Rules" subsection that lists **non-negotiable constraints**
the Agent must follow. These are things where violating them causes real
damage (broken output, uneditable files, wasted time).

Format: Numbered list with the consequence of violation:

```markdown
### Hard Rules (Non-negotiable)

1. **Rule description** — consequence of violation.
2. **Another rule** — consequence.
```

### 6. Pre-delivery Checklist

Every skill should end with a checklist the Agent runs through before
declaring the task done:

```markdown
## Pre-delivery Checklist

- [ ] Item 1
- [ ] Item 2
```

Include both technical checks (does it work?) and quality checks (does it
look good?).

### 7. Anti-Cliché Principles

For skills involving creative/design output, add a section that tells
the Agent what NOT to do — the common AI-generated patterns to avoid:

```markdown
## No AI-Generated Clichés

- **Bad pattern 1** — why it's bad
- **Bad pattern 2** — why it's bad
```

### 8. Cross-Skill Boundary Discipline (2026-06-14 established)

A skill must declare what it is **NOT**. When a user operates multiple
domain skills (e.g. 信息稿 + PPT + Wiki + 日报), each skill has its own
persona, scope, and iron rules. **Do not cross-pollinate.**

**Real incident (2026-06-13 飞书 session, lxgxdx)**: Microsoft SkillOpt
was being evaluated. Its `LLM-miner` mode dug "task patterns" from
session history and produced two rule sets:

- Round 1: "信息稿格式" rules — conflicted with the user's "创意活力"
  preference for 信息稿
- Round 2: **"PPT 规则"** — the user explicitly said:
  > "**PPT 规则跟统战信息稿 skill 不相关**"

The user killed SkillOpt not because it was bad tech, but because **it
proposed rules that violated the boundary between two of his domain
skills**. The 信息稿 skill is for writing government information
reports; the PPT skill is for designing training presentations. Each
has its own rules. A skill output that mixes them is unusable.

**Iron rule (apply to every domain skill you write)**:

> **One skill = one domain = one set of rules. If your skill would
> import rules from another skill's domain, you are crossing a
> boundary — refuse or rename.**

**Where to add this in your SKILL.md**:

In the Scope section, add a third bullet category:

```markdown
✅ **Applicable**: [this skill's domain]
❌ **Not applicable**: [other skills' domains, explicitly named]
⚠️ **Boundary**: [if X looks adjacent, defer to skill-Y]
```

**Why this matters for this user specifically** (lxgxdx):
- Operates 5+ skills daily: 信息稿 / PPT / Wiki / 日报 / cron
- Each skill has its own iron rules (e.g. 信息稿 = "五莲县自己的",
  PPT = "创意活力+不要死板")
- **He notices** when rules from one skill leak into another
- A 19KB SKILL.md with 200+ rules is *worse* than a focused 8KB skill
  if it forces the Agent to apply the wrong rules in the wrong context

**Anti-pattern**: "general-purpose" or "domain-agnostic" skills. The
moment you write "适用于任何需要 X 的场景" you have crossed a
boundary. Skills are sharp tools; generality is rust.

**Companion signal — preference-embedding**: the same user-correction
that exposed this boundary issue also surfaces the user's general
preference for **focused, single-domain skills**. When a new skill is
proposed that overlaps with two existing skills, the right answer is
to **split it into two skills**, not to merge.

---

## Structural Template

```markdown
---
name: skill-name
description: >-
  [One-line purpose + when to use + when NOT to use]
tags: [tag1, tag2]
category: category
---

# [Role Title] — [Role Identity]

[Role identity paragraph]

Core philosophy: **[One-sentence quality bar.]**

---

## Scope

✅ **Applicable**: [use cases]
❌ **Not applicable**: [non-use cases]

---

## Workflow

### Step 1: Understand the Requirements

[Decision matrix — when to ask questions vs. proceed]

### Step 2: [Next Step]

### Step N: Verification

[Technical specs, hard rules, and common pitfalls below workflow]

---

## [Technical Specifications or Design Principles]

### Hard Rules (Non-negotiable)
### Common Pitfalls
### Pre-delivery Checklist
```

---

## Anti-Patterns to Avoid

- **Pure procedural instructions** ("Step 1: Initialize project, Step 2: Run
  command") with no design judgment — the Agent will follow them mechanically
  without adapting to the user's situation.
- **No scope boundaries** — Agent uses the skill when it shouldn't.
- **Always-question pattern** — Agent asks a full question set even when the
  user has given all necessary info. Use the decision matrix to prevent this.
- **No quality bar** — No statement about what "good" looks like, so the
  Agent defaults to functional-but-mediocre output.
- **Missing anti-cliché guidance** — For creative/design skills, the Agent
  will default to AI-common patterns (same colors, same layouts, same fonts).
