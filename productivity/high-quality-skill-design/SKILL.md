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

For skills involving creative/design output, add a section that tells the
Agent what NOT to do — the common AI-generated patterns to avoid:

```markdown
### No AI-Generated Clichés

- **Bad pattern 1** — why it's bad
- **Bad pattern 2** — why it's bad
```

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
