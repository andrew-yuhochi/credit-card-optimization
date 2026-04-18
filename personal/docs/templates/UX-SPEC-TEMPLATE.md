# UX Specification — [Project Name]

> **Date**: [YYYY-MM-DD]
> **Designer**: ux-designer (subagent)
> **Status**: Draft | Reviewed with User
> **Related docs**: DISCOVERY-NOTES.md, RESEARCH-REPORT.md, MARKET-ANALYSIS.md
> **Project UX surface type**: Web App | CLI | Daily Digest Email | Slack Alert | Notebook | Multiple

## Executive Summary
<!-- 3–5 sentences. What is the user trying to accomplish, what surfaces will they interact with, and what are the top 1–2 UX decisions that shape the whole product. -->

## User Workflow Summary

### Current Workflow (without this tool)
<!-- Step-by-step map of what the user does today. Don't skip steps — the tedium is the point. -->

### Desired Workflow (with this tool)
<!-- Step-by-step map of what the user should do once the PoC exists. -->

### Friction Points Resolved
<!-- The moments of friction this tool removes. These are the high-value UX targets. -->

## Jobs-to-Be-Done

<!-- List the jobs the user is hiring this tool to do. Each job is a statement of intent, not a feature. -->

1. **[Job 1]** — [User's intent, not the mechanism]
2. **[Job 2]** — …
3. **[Job 3]** — …

## Information Architecture

### Surface Inventory
<!-- List every distinct surface the user will interact with. For a web app: pages. For CLI: commands. For email: sections. For alerts: message types. -->

| Surface | Purpose | Primary Question It Answers |
|---|---|---|
|  |  |  |

### Navigation Model
<!-- How the user moves between surfaces without losing context. For web: tabs, sidebar, breadcrumbs. For CLI: command hierarchy. For email: reading order. -->

### Reading Order / Visual Hierarchy
<!-- On any single surface, what should the user see first? What can be skimmed? What's at the bottom? -->

## Interaction Specification

<!-- One subsection per major touchpoint. Lightweight projects can collapse this into a single section. -->

### [Touchpoint 1: e.g., "Upload PDF Flow"]

- **Trigger**: [What causes this touchpoint to activate]
- **Input**: [What the user provides]
- **System response**: [What happens — what the user sees/hears]
- **Affordances**: [Click, drag, hover, keyboard, bulk actions — whatever is relevant]
- **Edge cases**: [What can go wrong]
- **Exit state**: [What the user leaves with]

### [Touchpoint 2: …]

## Human-in-the-Loop Patterns
<!-- Only if the project involves AI-assisted classification, extraction, or recommendation. Skip if not applicable. -->

### Confidence Surfacing
<!-- How does the system communicate when it's sure vs. unsure? -->

### Correction Flow
<!-- How does the user correct the system, and how does the correction feed back? -->

### Trust-Building Over Time
<!-- How does the user come to trust (or distrust) the system? What signals build or erode trust? -->

## Error & Empty States

### Error States
<!-- What does the user see when something fails? For each major failure mode: what the user sees, what they can do next. -->

### Empty States
<!-- What does the user see before they have any data? First-run experience. -->

### Success / Completion States
<!-- What does the user see when the task is done? How do they know they're done? -->

## Accessibility & Ergonomics
<!-- Keyboard access, screen reader, colour-blind safe palettes, CLI discoverability, etc. Brief — don't over-engineer for PoC. -->

## Wireframes / Structural Sketches
<!-- ASCII wireframes for web UIs, CLI command tree for CLI tools, email layout for digests, etc. Goal: shared understanding, not delivery assets. -->

```
[ASCII sketch goes here]
```

## Visual Mockup (Claude Design)

At PoC stage, produce ONE Claude Design Brief for the **single highest-risk UX surface** — the surface that, if wrong, would invalidate the project concept. ux-designer drafts the brief; the user runs Claude Design (claude.ai) manually; the resulting prototype becomes the Demo Artifact for the implementing task.

- **Highest-risk surface for this project**: [Name the surface and explain in one sentence why it's the highest-risk visual decision]
- **Brief location**: `docs/<project>/<phase>/designs/<surface-slug>-brief.md`
- **Prototype location**: `docs/<project>/<phase>/designs/<surface-slug>-prototype.{url,pdf}` (filled in after the user runs Claude Design)
- **Linked task**: [Which TASKS.md task uses this prototype as its Demo Artifact]

(MVP/Beta may add additional briefs for other surfaces. At PoC, restrain to one.)

## Open UX Questions
<!-- Anything the discovery notes did not resolve that matters for UX decisions. These go back to the user before implementation starts. -->

## Implications for the PRD
<!-- Specific, actionable UX flags for the architect. Things like: "the edit-totals-live interaction is the keystone UX decision, don't design it away in scope cuts", "don't add features X/Y to the dashboard — they crowd the primary job". Bullet list. -->
