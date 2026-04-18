# Product Requirements Document — [Project Name]

> **Status**: Draft | In Review | Approved
> **Author**: [Name]
> **Last Updated**: [Date]

## 1. Problem Statement
<!-- What problem are we solving? Who experiences this problem? Why does it matter? -->

## 2. Target User
<!-- Who is the primary user? What is their context, skill level, and motivation? -->

## 3. Success Criteria
<!-- How do we know the PoC works? List 3-5 measurable criteria. -->
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## 4. Commercial-Signal Instrument

Per CLAUDE.md, every project runs one cheap commercial-signal instrument from PoC onward. It is the single measurement that tells us, at the MVP→Beta decision point, whether the commercial thesis holds. Protect it in scope cuts.

- **Instrument**: [e.g., "Click-through rate on recommended papers" | "Classifier accuracy vs. user corrections" | "User edit rate on auto-categorized transactions"]
- **What it measures**: [The single hardest question of the commercial thesis — one sentence]
- **Where it lives**: [Module or file that records the signal, e.g., `src/telemetry/signal.py` or "CSV log at `data/signal.csv`"]
- **How it's read**: [Command or dashboard path that surfaces the current reading]
- **Target after ~3 months of MVP use**: [What reading would constitute a positive signal]
- **Scope protection**: [ ] Confirmed protected in milestone planning

If you cannot name a cheap instrument now, stop and discuss with the user. A project without a signal instrument cannot make the Beta decision.

## 5. Scope — What's IN
<!-- List the features and capabilities included in this PoC. Be specific. -->

## 6. Scope — What's OUT
<!-- Explicitly state what we are NOT building. This prevents scope creep. -->

## 7. User Workflow
<!-- Step-by-step: how does the user interact with this tool from start to finish? -->

## 8. Assumptions
<!-- What are we assuming to be true? List data availability, API access, user behavior assumptions. -->

## 9. Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
|      |           |        |            |

## 10. Future Considerations
<!-- What would the medium-term and long-term expansions look like? Reference but don't design them. -->
