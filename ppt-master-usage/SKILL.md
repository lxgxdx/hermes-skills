---
name: ppt-master-usage
description: >
  Use ppt-master to generate natively-editable PPTX presentations from diverse input materials (PDF/DOCX/Markdown/text/URLs). Covers project initialization, SVG-based AI generation pipeline, post-processing, and export. Ideal for professional slide decks, reports, pitch decks, and educational materials that need polished, editable output.
  Use this skill whenever the user's request involves creating, generating, or assembling a PowerPoint/Keynote presentation, slide deck, or PPTX file — especially when they provide reference materials like PDFs, documents, or outlines.
  Not applicable: pure text-to-PPTX without visual structure (use simpler tools), editing existing PPTX templates manually, or non-presentation document generation.
tags: ["ppt", "powerpoint", "automation", "presentation", "slide-deck"]
category: productivity
---

# PPT Master — AI Presentation Engineer

This skill positions the Agent as a senior presentation engineer who transforms raw input materials into polished, natively-editable PPTX decks using the ppt-master AI pipeline. You are not just "making slides" — you're crafting a visual narrative: structuring content, designing layouts, enforcing visual consistency, and delivering production-ready files that the user can edit further in PowerPoint/Keynote.

Core philosophy: **A great deck tells a story, not just displays bullet points. Every slide earns its place. Layout, typography, color, and pacing are design decisions, not defaults.**

---

## Scope

✅ **Applicable**: 
- Creating slide decks from PDFs, DOCX, Markdown, plain text, web URLs
- Generating pitch decks, technical reports, educational materials, meeting presentations
- Converting lecture slides or research papers into presentation format
- Quick-turnaround "make a deck from these notes" scenarios

❌ **Not applicable**:
- Editing individual slides in an existing PPTX (open in PowerPoint directly)
- Pure text-to-PPTX with no structure or visual design intent
- Non-presentation formats (Word docs, PDFs for printing, HTML pages)
- Manual slide-by-slide export (use the automated pipeline)

---

## Workflow

### Step 1: Understand the Requirements

Whether and how much you ask depends on how much information has been provided. **Do not mechanically fire off a long list of questions every time**:

| Scenario | Ask? |
|---|---|
| "Make a deck from this PDF" (no audience, no tone) | ✅ Ask: audience, presentation length (minutes/slides), tone (formal/casual), any branding |
| "Turn this PRD into a 12-slide pitch deck for investors" | ❌ Enough info — start building |
| "Generate a presentation from these notes" | ⚠️ Only ask if structure is unclear from notes |
| "Make some slides about project status" | ✅ Too vague — ask about content, audience, format |
| "Create a quarterly report deck from this Excel data" | ✅ Ask: audience (exec vs team), key metrics to highlight, branding |

Key areas to probe (pick as needed):
- **Content scope**: What input material do they have? PDF/DOCX/Markdown/URL/plain text?
- **Deck parameters**: Approx slide count, aspect ratio (16:9 by default), duration?
- **Audience & tone**: Who's watching? C-suite / engineering / external? Formal or casual?
- **Design direction**: Do they have brand colors / logo? A reference deck? Or free artistic hand?
- **Visual complexity**: Charts / diagrams / screenshots needed? Or text-heavy?

### Step 2: Prepare Input Material

Read and understand the input thoroughly:

- **PDFs**: Extract text structure — identify headings, subheadings, body content, key data points
- **DOCX**: Parse sections, tables, images — preserve structure
- **Markdown**: Headings map to slides, subheadings to content sections
- **URLs**: Fetch and extract the relevant content
- **Plain text**: Ask for clarification if the structure isn't obvious

**Reading priority**: Content structure and story flow > visual details > individual word choice. Your job is to architect slides, not transcribe.

### Step 3: Initialize Project and Declare Design Direction

**Before generating SVG**, articulate the design direction in Markdown so the user can confirm:

```markdown
Design Direction:
- Slide count: ~N slides
- Aspect ratio: 16:9 (1920×1080)
- Color palette: [primary / accent / background — extract from brand or choose professional pair]
- Typography: [heading / body fonts — avoid Inter/Roboto clichés]
- Visual style: [minimal / bold / technical / creative / formal]
- Key structural decisions: [e.g. "3-column layout for feature overview"]
```

Then initialize the project:

```bash
SKILL_DIR=~/.hermes/skills/ppt-master/skills/ppt-master
~/.hermes/hermes-agent/.venv/bin/python3 ${SKILL_DIR}/scripts/project_manager.py init <project-name> --format ppt169
```

### Step 4: Generate Design Spec and SVG

1. The Strategist module reads the content and generates `design_spec.md` — review it for structural alignment before proceeding
2. The Executor module generates individual slide SVGs into `svg_output/`
3. **Do NOT skip to export yet** — SVGs need post-processing

### Step 5: Post-Processing (Required — Non-Negotiable)

⚠️ **This is the most critical step. Never skip it.**

```bash
# Step 1: SVG post-processing (generates svg_final/ with editable vector shapes)
~/.hermes/hermes-agent/.venv/bin/python3 ${SKILL_DIR}/scripts/finalize_svg.py .

# Step 2: Export from svg_final/ only
~/.hermes/hermes-agent/.venv/bin/python3 ${SKILL_DIR}/scripts/svg_to_pptx.py -s final -i svg_final/
```

**Why this matters**: `svg_output/` contains raw AI-generated SVGs with text rendered as image paths (un-editable). `finalize_svg.py` converts these to native DrawingML vector shapes. Without this step, the PPTX is effectively a slideshow of screenshots — text, colors, and layout cannot be edited.

### Step 6: Verification

Before delivering, run through this checklist:

- [ ] PPTX opens without errors in PowerPoint/Keynote
- [ ] All slide text is **natively editable** (selectable, modifiable) — not image fallbacks
- [ ] Layout is consistent across slides (margins, spacing, alignment)
- [ ] No text overflow or truncation on any slide
- [ ] Color palette is consistent — no rogue hues
- [ ] Charts/tables/diagrams are rendered correctly

---

## Technical Specifications

### Python Environment

- Python 3.10+
- **Must use hermes-agent venv Python**, never system python3:
  ```bash
  ~/.hermes/hermes-agent/.venv/bin/python3
  ```
- Dependencies installed via `uv pip` (hermes-agent venv lacks pip):

  ```bash
  uv pip install svglib==1.5.1 reportlab PyMuPDF mammoth markdownify ebooklib nbconvert requests beautifulsoup4 pillow numpy cairosvg curl_cffi google-genai openai python-pptx cssselect2==0.9.0
  ```

### Hard Rules (Non-negotiable)

1. **Never skip `finalize_svg.py`** — exporting directly from `svg_output/` produces uneditable PPTX with image-fallback slides. Always run: `finalize_svg.py .` first (from the project directory).
2. **Never use system python3** — always use `~/.hermes/hermes-agent/.venv/bin/python3`. System python lacks the right deps and version.
3. **Always specify SKILL_DIR** — scripts are at `${SKILL_DIR}/scripts/`. Initialize this variable at project start.
4. **svglib must be < 1.6** — version 1.5.1 is the known stable release. Higher versions break SVG parsing.

### Common Pitfalls

- **"Why is my PPTX not editable?"** → You skipped `finalize_svg.py`. Rerun the pipeline from SVG output.
- **"Import google.genai fails"** → Use `import google.genai as genai` (not `import genai`).
- **"Script not found"** → Check `${SKILL_DIR}/scripts/` directory structure exists.
- **"Dependency error"** → Confirm you're using the hermes-agent venv Python, not system python3.
- **"SVG parsing error"** → Check if `svglib` version is ≤ 1.5.1.

---

## Design Principles

### No AI-Generated Presentation Clichés

- **Avoid default templates**: Don't use the same blue-theme color scheme every time. Adapt to the content's subject matter.
- **Meaningful visuals > decorative icons**: Every image, chart, or diagram should support the message — not fill whitespace.
- **Data integrity**: Never fabricate stats, charts, or figures. Use placeholders for missing data and flag them.
- **Typography variety**: Default to professional pairings (e.g., sans-serif headings + serif body, or a bold display face for titles). Avoid the overused Inter/Roboto/system-ui combo.

### Slide Structure Principles

- **One idea per slide**: If a slide has 3 distinct points, it should probably be 3 slides.
- **Visual hierarchy**: Title → subheading → body → callout. Each level should be visually distinct.
- **Appropriate density**: Executive decks: 1–3 bullets per slide. Technical decks: up to 6–8 if well-structured. Slide decks are not documents.
- **Whitespace is design**: Don't cram content. Let slides breathe.

### Layout and Typography

| Context | Recommendation |
|---|---|
| Title slides | 48–72px display font, bold |
| Section headers | 36–44px, distinct from body |
| Body text | 24–36px (readable on projector) |
| Captions / footnotes | 16–20px |
| Slide margins | 60–80px on all sides |

---

## Alternative Tools

If ppt-master results are unsatisfactory or the user requests an alternative:

- **PPTAgent** (EMNLP 2025): Two-stage approach (analyze reference PPT → iterative generation) + PPTEval 3D evaluation. V2 adds Deep Research + image gen. Install: `uvx pptagent onboard`. Generate: `uvx pptagent generate "topic" -o output.pptx`. Best when higher design quality is needed or as a comparison reference.
- GitHub: https://github.com/icip-cas/PPTAgent

---

## Pre-delivery Checklist

- [ ] PPTX exports without errors
- [ ] All slides are natively editable (verify in PowerPoint/Keynote)
- [ ] No text overflow or truncation
- [ ] Color scheme is consistent across all slides
- [ ] Content matches the user's input material (no fabricated data)
- [ ] File named descriptively (e.g., `Corporate_Pitch_Deck.pptx`, not `output.pptx`)
- [ ] If the deck contains sensitive/incomplete data, flag it to the user
