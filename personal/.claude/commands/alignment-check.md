# Alignment Check — $ARGUMENTS

Invoke business-analyst to verify whether a proposal aligns with the project's stated north star (PRD + MARKET-ANALYSIS). Use this command — or just ask "is this aligned with our goal?" in conversation, which the main session will auto-route to business-analyst.

## Instructions

Parse `$ARGUMENTS` as `<project> "<proposal description>"`.

If the proposal is not given as a quoted string, ask the user to describe it in one sentence before proceeding.

### Step 1: Confirm reference docs exist

Verify `docs/<project>/<current-phase>/PRD.md` exists. If not, STOP — alignment cannot be checked without a PRD. Recommend running `/poc-kickoff` first.

(For Mode A — PRD-drafting alignment — the architect invokes BA directly inside `/poc-kickoff` Step 4 or `/phase-transition` Step 5. This command handles Modes B and C only.)

### Step 2: Dispatch to business-analyst

```
Agent(
  subagent_type: "business-analyst",
  description: "Alignment check for <project>: <short proposal>",
  prompt: """
Project: <project>
Current phase: <poc | mvp | beta>
Proposal: <proposal>

Run Mode B (PoC) or Mode C (MVP/Beta) — pick by phase.

Read:
- docs/<project>/<phase>/PRD.md (§3 Commercial Thesis, §4 Success Criteria, §5 Commercial-Signal Instrument, §6 Scope IN, §7 Scope OUT)
- (Mode C) docs/<project>/<phase>/MVP-GOALS.md if present
- (Mode C, Beta only) docs/<project>/<phase>/DEPLOYMENT.md and API-SPEC.md if present
- The most recent 3 entries in docs/<project>/<phase>/ALIGNMENT-LOG.md (create the file if absent)

Produce a verdict (ALIGNED / DRIFTING / VIOLATES) and append the entry to ALIGNMENT-LOG.md per your output format. Leave the User outcome line blank — the user fills it after deciding.

Do NOT edit PRD, BACKLOG, or any other doc — that's the user's call after seeing the verdict.
"""
)
```

### Step 3: Present verdict to user

Show the BA verdict and ask the user to choose, scoped to the verdict:

- **ALIGNED**: "OK to proceed — this fits PRD §<N>. Approved? (yes / discuss / drop)"
- **DRIFTING**: "BA flagged drift. Options: (a) revise the proposal to fit PRD, (b) update PRD §<N> with explicit rationale, (c) move to BACKLOG.md and revisit at phase boundary. Which?"
- **VIOLATES**: "BA blocks the proposal — it violates PRD §<N>. To proceed, the PRD section must be reopened. Run `/poc-kickoff` to revise (PoC) or `/phase-transition` (MVP/Beta), or drop the proposal. Which?"

### Step 4: Record the outcome

Once the user decides, dispatch business-analyst again with a small update prompt:

```
Agent(
  subagent_type: "business-analyst",
  description: "Update ALIGNMENT-LOG outcome",
  prompt: """
In docs/<project>/<phase>/ALIGNMENT-LOG.md, find the entry you just wrote for "<proposal>" and update its **User outcome** line to: <user's decision verbatim>. Do not modify the verdict, anchors, or analysis sections.
"""
)
```

## When to call this command

**Call** when:
- User proposes adding a new requirement (to BACKLOG.md or current milestone)
- User considers solving a newly-discovered need in the current phase
- User questions whether a milestone deliverable is on-mission
- During a milestone-validation conversation, a new requirement surfaces
- You (main session) detect an alignment-style question in conversation: "is this aligned…?", "does this fit…?", "are we drifting…?", "should we add…?"

**Do not call** for:
- Routine task implementation that's already in TASKS.md (presumed aligned at planning time)
- Bug fixes (no scope change)
- Tactical decisions that don't affect product direction (file naming, code style, library version bumps)

## Scope boundaries

- This command only runs Modes B/C. Mode A (PRD drafting) is invoked by architect inside `/poc-kickoff` and `/phase-transition`, not here.
- Do not edit PRD or BACKLOG from this command. The user decides after seeing the verdict and edits separately (or the next planning command does).
