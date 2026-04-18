# Phase Review — [Project Name] / [Phase: PoC | MVP | Beta]

> **Phase completed**: [Date]
> **Reviewed by**: architect
> **User approved**: [ ] Yes / [ ] No

## Phase Summary
- **Goal**: [What this phase set out to prove/validate]
- **Outcome**: [Was the goal met? One sentence verdict]
- **Duration**: [Start date → End date]
- **Milestones completed**: [X of Y]

## What Worked
- [Pattern, tool, approach, or decision that should carry forward]
- [...]

## What Didn't Work
- [Technical debt, workaround, or approach that needs rethinking]
- [Impact: how it affected the phase and what it means for the next phase]
- [...]

## Known Technical Debt
| Area | Description | Severity | Recommended Phase to Address |
|------|-------------|----------|------------------------------|
| [Module/Component] | [What's wrong and why] | Low / Medium / High | MVP / Beta / Never |

## Unresolved Backlog
Items from BACKLOG.md not addressed in this phase:

| Backlog ID | Description | Priority Reassessment | Recommendation |
|-----------|-------------|----------------------|----------------|
| BL-XXX | [Description] | [Same / Higher / Lower] | [Promote / Defer / Drop] |

## Commercial Signal Results
- **Instrument**: [What was measured — reference PRD §5 Commercial-Signal Instrument]
- **Data collected**: [Summary of what the instrument showed]
- **Interpretation**: [What this means for commercial viability]
- **Recommendation**: [Continue measuring / Adjust instrument / Act on findings]

## Beta Decision Checklist

> **Required at MVP phase review. Mark "N/A — PoC" at PoC review; mark "Already in Beta" at Beta review.**

Per CLAUDE.md, the MVP → Beta transition requires three explicit answers.

### (a) Does the tool solve my problem?
- [ ] Yes / [ ] No
- **Evidence**: [Specific examples of the tool replacing the manual workflow; daily-use frequency; problem-resolution rate]

### (b) Does the reliability and UX meet my standard?
- [ ] Yes / [ ] No
- **Evidence**: [Uptime, error recovery incidents, manual-intervention events; scannable output; configuration ease without code edits]

### (c) Did the commercial-signal instrument show promise?
- [ ] Yes / [ ] No / [ ] Inconclusive
- **Evidence**: [Signal reading vs. the target set in MVP-GOALS.md; trend over time; comparison to competitor benchmarks from MARKET-ANALYSIS.md]

### Beta Decision
- [ ] **Begin Beta** — all three are Yes, or two Yes + one Inconclusive with a concrete plan to resolve.
- [ ] **Continue MVP** — one or more criteria not yet met; iterate on the MVP before re-reviewing.
- [ ] **Enjoy as personal tool** — tool works, but commercial signal is absent or unlikely to improve. No Beta.

**Rationale**: [3-5 sentences explaining the chosen path]

## Reusable Patterns Surfaced

Patterns, utilities, or architectural approaches that worked well in this phase and might benefit other projects in the portfolio. Promotion from project-local → portfolio-wide skill is a user decision; this section makes the prompt routine at every phase review.

| Pattern | What it does | Candidate location | User decision |
|---------|-------------|--------------------|---------------|
| [e.g., "Twikit rate-limit backoff"] | [One-line description] | [e.g., `.claude/skills/api-integration-patterns/` or new skill] | Promote / Defer / Keep project-local |

## Recommendations for Next Phase
1. **Prioritize**: [What should be done first and why]
2. **Defer**: [What can wait and why]
3. **Reconsider**: [What needs rethinking based on this phase's learnings]
4. **New risks**: [Anything discovered that wasn't anticipated]

## Updated Roadmap
Brief revision of the project's medium-term direction based on this phase's outcomes:
- [Next phase focus areas]
- [Features to add, harden, or drop]
- [Timeline expectations]
