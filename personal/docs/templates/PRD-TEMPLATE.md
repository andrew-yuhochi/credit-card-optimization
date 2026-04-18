# Product Requirements Document — [Project Name]

> **Status**: Draft | In Review | Approved
> **Author**: [Name]
> **Last Updated**: [Date]

## 1. Problem Statement
<!-- What problem are we solving? Who experiences this problem? Why does it matter? -->

## 2. Target User
<!-- Who is the primary user? What is their context, skill level, and motivation? -->

## 3. Commercial Thesis (Agreed)

The agreed-upon commercial story for this project. Adopted from the MARKET-ANALYSIS conversation — record what the user actually committed to, even if it differs from the analyst's recommendation. This is the **anchor** business-analyst reads in Modes B/C.

- **Adopted commercial verdict**: [e.g., "Plausible commercial SaaS targeting Canadian household segment" | "Personal-use-only — commercial path is weak" | "Needs pivot — current framing won't work commercially"]
- **Adopted uniqueness / moat angle**: [The specific differentiator the user committed to — quote it. E.g., "Receipt-based categorization with Canadian tax categories"]
- **Adopted monetization angle**: [Pricing model + tier structure the user committed to. E.g., "Freemium with $9/mo Pro tier" or "Personal use only — no monetization"]
- **Deviations from MARKET-ANALYSIS**: [If the user adopted something different from the analyst's recommendation, name it and explain why. Otherwise: "None — adopted as recommended."]
- **Decision date**: [YYYY-MM-DD]

If the user changes their mind on any of these, update this section and re-run business-analyst against current open BACKLOG items to re-evaluate alignment.

## 4. Success Criteria
<!-- How do we know the PoC works? List 3-5 measurable criteria. -->
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## 5. Commercial-Signal Instrument

Per CLAUDE.md, every project runs one cheap commercial-signal instrument from PoC onward. It is the single measurement that tells us, at the MVP→Beta decision point, whether the commercial thesis (§3) holds. Protect it in scope cuts.

- **Instrument**: [e.g., "Click-through rate on recommended papers" | "Classifier accuracy vs. user corrections" | "User edit rate on auto-categorized transactions"]
- **What it measures**: [The single hardest question of the commercial thesis — one sentence]
- **Where it lives**: [Module or file that records the signal, e.g., `src/telemetry/signal.py` or "CSV log at `data/signal.csv`"]
- **How it's read**: [Command or dashboard path that surfaces the current reading]
- **Target after ~3 months of MVP use**: [What reading would constitute a positive signal]
- **Scope protection**: [ ] Confirmed protected in milestone planning

If you cannot name a cheap instrument now, stop and discuss with the user. A project without a signal instrument cannot make the Beta decision.

## 6. Scope — What's IN
<!-- List the features and capabilities included in this PoC. Be specific. -->

## 7. Scope — What's OUT
<!-- Explicitly state what we are NOT building. This prevents scope creep. -->

## 8. User Workflow
<!-- Step-by-step: how does the user interact with this tool from start to finish? -->

## 9. Assumptions
<!-- What are we assuming to be true? List data availability, API access, user behavior assumptions. -->

## 10. Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
|      |           |        |            |

## 11. Future Considerations
<!-- What would the medium-term and long-term expansions look like? Reference but don't design them. -->
