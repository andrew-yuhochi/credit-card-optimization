---
name: phase-transition
description: Transition a project to its next development phase (MVP or Beta). Reads the previous phase's review, backlog, and completed work to inform planning.
---

# Phase Transition — $ARGUMENTS

You are transitioning a project to its next phase. Follow these steps in order.

## Step 1: Identify the Project and Target Phase

Parse the arguments to determine:
- **Project name**: The project being transitioned
- **Target phase**: `mvp` or `beta`

If not clear from arguments, ask the user.

## Step 2: Verify Prerequisites

**For MVP transition, verify:**
- [ ] `docs/<project>/poc/PHASE-REVIEW.md` exists (architect must produce this first)
- [ ] User has reviewed and approved the PoC PHASE-REVIEW.md
- [ ] All PoC milestones in `docs/<project>/poc/TASKS.md` are marked Done

**For Beta transition, verify:**
- [ ] `docs/<project>/mvp/PHASE-REVIEW.md` exists
- [ ] User has reviewed and approved the MVP PHASE-REVIEW.md
- [ ] All MVP milestones in `docs/<project>/mvp/TASKS.md` are marked Done
- [ ] MVP has been in personal use for a meaningful period

If prerequisites are not met, stop and tell the user what's missing.

## Step 3: Read Previous Phase Context

**For MVP transition, read from `docs/<project>/poc/`:**
1. `PHASE-REVIEW.md` — learnings, recommendations, technical debt
2. `BACKLOG.md` — unaddressed requirements (if exists)
3. `TASKS.md` — completed tasks log
4. `PRD.md` — current product definition
5. `TDD.md` — current technical design

**For Beta transition, read from `docs/<project>/mvp/`:**
1. `PHASE-REVIEW.md` — learnings, recommendations, technical debt
2. `BACKLOG.md` — unaddressed requirements
3. `TASKS.md` — completed tasks log
4. `PRD.md` — current product definition
5. `TDD.md` — current technical design

## Step 4: Discuss Phase Goals with User

Have a conversation with the user about the next phase. Ask about:
- What worked well in the previous phase that should continue?
- What was painful or unreliable?
- Which backlog items are now important?
- What does "done" look like for this phase?
- Any new requirements or changed priorities?

Follow the Conversation-First Principle — ask questions one at a time, listen, follow up.

## Step 5: Produce Phase Documents

**For MVP transition — create documents in `docs/<project>/mvp/`:**
1. Copy PRD.md, TDD.md, DATA-SOURCES.md, and BACKLOG.md from `poc/` into `mvp/` as starting points
2. Create `MVP-GOALS.md` from `docs/templates/MVP-GOALS-TEMPLATE.md`
3. Evolve `PRD.md` — add MVP-specific requirements, mark PoC-only items as complete
4. Evolve `TDD.md` — add reliability, automation, deployment considerations
5. Create new `TASKS.md` — new milestones for MVP work, incorporating promoted backlog items
6. The `poc/` originals stay frozen as historical record

**For Beta transition — create documents in `docs/<project>/beta/`:**
1. Copy PRD.md, TDD.md, DATA-SOURCES.md, and BACKLOG.md from `mvp/` into `beta/` as starting points
2. Re-invoke `market-analyst` for updated commercial analysis → save to `beta/MARKET-ANALYSIS.md`
3. Create `DEPLOYMENT.md` from deployment template
4. Create `API-SPEC.md` if the project exposes an API
5. Evolve PRD.md, TDD.md for Beta scope (auth, billing, multi-user, deployment)
6. Create new `TASKS.md` — new milestones for Beta work
7. The `mvp/` originals stay frozen as historical record

## Step 5.5: Business-Analyst Alignment Check — MANDATORY

After the new-phase docs are drafted, dispatch **business-analyst** (Mode A — PRD-drafting alignment) before architect's gate review:

> Run Mode A: review the new-phase `docs/<project>/<target-phase>/PRD.md` against the carry-forward `MARKET-ANALYSIS.md` (and the new-Beta MARKET-ANALYSIS.md if doing a Beta transition). Verify §3 Commercial Thesis (Agreed) still reflects the adopted commercial story; verify the new milestones in TASKS.md serve §4 Success Criteria and §6 Scope IN. Flag drift introduced by the phase transition. For Beta transitions, also verify §5 Commercial-Signal Instrument readings from the MVP PHASE-REVIEW.md justify the chosen Beta Decision.
>
> Output verdict and append to `docs/<project>/<target-phase>/ALIGNMENT-LOG.md`.

If BA returns DRIFTING or VIOLATES, loop architect ↔ BA before proceeding to Step 6.

## Step 6: Architect Review

Invoke the architect agent to review the updated documents for:
- Internal consistency across PRD, TDD, DATA-SOURCES, and TASKS
- Milestone structure with testable deliverables
- Phase-appropriate scope (no Beta features in MVP, etc.)
- Backlog items properly triaged (promoted, deferred, or dropped with rationale)

## Step 7: Report to User

Present a summary:
- Phase transition: [PoC → MVP] or [MVP → Beta]
- Key goals for the new phase
- Milestones planned with deliverables
- Promoted backlog items
- Deferred items and rationale
- First milestone ready to begin
