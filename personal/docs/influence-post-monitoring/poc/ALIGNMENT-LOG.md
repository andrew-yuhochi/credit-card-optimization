# Alignment Log — influence-post-monitoring / poc

---

## 2026-04-18 — Mode A PRD-drafting alignment check: does the PRD faithfully adopt the MARKET-ANALYSIS commercial verdict, moat, monetization angle, regulatory precondition, and commercial signal instrument?

**Verdict**: ALIGNED
**Mode**: A
**Anchors**:
- MARKET-ANALYSIS §Commercial Verdict: "Plausible commercial SaaS — path is narrow, regulatory hurdle must be cleared first."
- MARKET-ANALYSIS §Uniqueness & Moat, candidate #1: "Verifiable Historical Accuracy of Individual Voices — Track Record Database (Durability: High, time-dependent) … TipRanks does this for Wall Street analysts. Nobody does it for buy-side / activist / short-seller social media investors."
- MARKET-ANALYSIS §Commercial Verdict, condition 3: "RIA/small-fund segment as deliberate second-phase commercial target — retail subscription is real but churny."
- MARKET-ANALYSIS §Commercial Risks, bullet 1: "Securities attorney consult ($500–$1,500) before charging first subscriber."
- MARKET-ANALYSIS §Commercial Signal Instrument: "50+ signups/week after 8 weeks of public operation without paid promotion. Below threshold signal: Under 20/week after 12 weeks → market not pulling hard enough for Beta investment."
- PRD §3 Commercial Thesis (Agreed): "Adopted commercial verdict: Plausible commercial SaaS — path is narrow, regulatory hurdle must be cleared first."
- PRD §3: "Adopted uniqueness / moat angle: Verifiable historical accuracy of individual buy-side voices — the track record database … the only genuinely durable commercial asset, and it requires time (not just engineering)."
- PRD §3: "Adopted monetization angle: Multi-tier retail + RIA SaaS with the RIA segment as the priority commercial target. Retail tier $35–$50/month … RIA/small-fund tier $150–$400/month."
- PRD §3: "A securities-attorney consult ($500–$1,500) is required before any commercial launch … hard prerequisite for the Beta phase, not optional."
- PRD §5 Commercial-Signal Instrument: "Public accuracy leaderboard with waitlist CTA … 50+ waitlist signups per week after 8 weeks … Below 20/week after 12 weeks = market not pulling hard enough; no Beta investment."
- PRD §7 Scope OUT: "Commercial launch of any kind: Beta scope, and only after the securities-attorney consult (§3 regulatory precondition)."

**Analysis**: All five verification points pass without exception. PRD §3 reproduces the MARKET-ANALYSIS commercial verdict verbatim, correctly names the track record database as the sole durable moat and explains that time (not engineering) is the limiting factor, adopts the RIA segment ($150–$400/month) as the priority commercial target with retail ($35–$50/month) as secondary, captures the hard regulatory precondition with the correct cost range and the correct legal citation (Investment Advisers Act of 1940), and cites the TipRanks acquisition within the ~$175–200M range stated in the MARKET-ANALYSIS. §6 Scope IN explicitly builds the track record data foundation (overnight_return, tradeable_return, excess_vol_score, 30-day per-poster scorecard) and the multi-tenant schema from day one, directly fulfilling MARKET-ANALYSIS §Implications for the PRD. §7 Scope OUT correctly defers the public leaderboard web page to MVP, auth/billing to Beta, and commercial launch to Beta-only-after-consult. One minor design evolution: the PRD uses `overnight_return` / `tradeable_return` / `excess_vol_score` where MARKET-ANALYSIS §Implications suggested `next_day_return` / `5_day_return` / `10_day_return`; this is a deliberate and more analytically rigorous choice (excess/vol is vol-adjusted and SPY-relative), not a drift from the thesis.

**Recommendation**: ALIGNED — proceed. The PRD may be locked. No revisions needed before implementation begins.

**User outcome**: [Leave blank — to be filled when user decides]

---

## 2026-04-18 — Milestone 1 deliverable review: WhatsApp delivery layer + morning alert renderer with user-approved format deviations

**Verdict**: DRIFTING
**Mode**: B
**Anchors**:
- PRD §4 Success Criteria C1: "A WhatsApp message arrives before 9:00 AM ET on every US trading day, containing an Act Now section and a Watch List section (or an explicit 'no signals' message per the always-send rule)."
- PRD §4 Success Criteria C3: "Both messages ship on every trading day even when there are zero signals or zero outcomes to report — silence is never an outcome."
- PRD §6.4 Delivery item 16: "Per signal block: `DIRECTION $TICKER (Market Cap Class)`, conviction dots `●●●●○`, poster handle, inline corroboration/conflict tags (`⚠️ Direction changed`, `⚠️ Conflicted — opposing view exists`, `CORROBORATED — N posters`), quote fragment ≤ 150 chars."
- PRD §6.4 Delivery item 18: "Regulatory disclaimer footer on every message: `_This is information about public posts, not investment advice. Do your own research._`"
- PRD §11 Risks: "Regulatory action against 'Act Now' framing — Likelihood Low at PoC (personal use) — Mitigation: Disclaimer footer on every message; securities-attorney consult mandatory before Beta; frame all output as 'information,' not 'recommendations.'"
- PRD §6.4 Delivery item 19: "`MessageDelivery` interface with `send(text: str) -> bool` contract. Twilio WhatsApp Sandbox is primary; CallMeBot is automatic fallback." [DELIVERED — ALIGNED]

**Analysis**: C1, C3, and the `MessageDelivery` delivery abstraction (§6.4 item 19) are fully delivered and aligned. The commercial thesis (§3), commercial signal instrument (§5), and data architecture anchors (§6.5) are unaffected. Four §6 Scope IN format items were changed during user review: conviction dots (`●●●●○`) replaced by `✅` emoji + %, `CORROBORATED — N posters` label removed, quote truncation changed from ≤150 chars to 20 words, and the regulatory disclaimer footer removed from the message. The first three are cosmetic and low-risk. The disclaimer footer removal is the one item that intersects a named risk mitigation in §11 — the PRD explicitly lists "Disclaimer footer on every message" as the mitigation for the regulatory risk at PoC. All four deviations are user-approved, but none are yet documented as §8 UX-SPEC Override entries, leaving the PRD out of sync with what was built.

**Recommendation**: DRIFTING — the format deviations are acceptable given user approval, but two actions are needed before Milestone 2 begins: (a) the architect should add §8 override entries for the four Milestone 1 format decisions (conviction emoji, CORROBORATED removal, 20-word truncation, disclaimer removal), mirroring the pattern already established in §8 for prior UX-SPEC overrides; (b) the disclaimer footer removal in particular should carry an explicit rationale note — e.g., "removed for PoC personal-use readability; must be re-evaluated before any non-personal-use distribution" — so the regulatory risk mitigation gap is visible at the MVP gate. No proposal should be rejected; this is a documentation sync, not a reversal.

**User outcome**: [Leave blank — to be filled when user decides]

---

## 2026-04-19 — Milestone 2 deliverable review: conflict-block merged renderer for opposing-direction signals on the same ticker

**Verdict**: ALIGNED
**Mode**: B
**Anchors**:
- PRD §6.2 Conflict handling item 12: "3+ different posters on same ticker with mixed directions: group by direction. Each direction group becomes its own signal block. Both blocks appear in the alert with `⚠️ Conflicted — opposing view exists` tag."
- PRD §6.4 Delivery item 16: "Act Now section: maximum 5 signals displayed, ordered by conviction score descending."
- PRD §4 Success Criterion C4: "the system surfaces at least one signal per week that the user judges as genuinely actionable."
- PRD §7 Scope OUT: "Web dashboard / UI: PoC is WhatsApp-only."

**Analysis**: The conflict-block proposal is a renderer-level refinement of the already-in-scope conflict handling defined in §6.2 item 12. The PRD already specifies that opposing-direction signals on the same ticker appear together in the morning alert — the proposal tightens the visual treatment by collapsing two separate signal blocks into one consolidated conflict block with a 📈📉 header. Counting the conflict block as 1 toward the 5-signal display limit is consistent with §6.4's intent: the cap exists to prevent alert overload, and a conflict block communicates two positions in one unit without inflating that count. The format change is cosmetic and renderer-scoped; it does not touch the scoring engine, the data model, or any §7 Scope OUT item. The proposal narrows an existing behavior rather than introducing new scope, and the user's PoC validation question ("is the output useful?") is directly served by surfacing opposing views in a single readable unit. No pattern of repeated drift is present in the prior log entries that would affect this verdict.

**Recommendation**: ALIGNED — proceed; user can approve as-is. No PRD revision is required. The architect should add this as Override 17 in PRD §8 UX-SPEC Override Decisions (conflict-block merged rendering; conflict block counts as 1 against the 5-signal limit) to maintain the single source of truth already established by Overrides 14–16 from Milestone 1.

**User outcome**: [Leave blank — to be filled when user decides]

---

## 2026-04-19 — Milestone 2 full deliverable review: TASK-003 through TASK-010c (schema, ingestion, calendar, extraction, scoring, amplifier, cleanup, orchestrator, conflict renderer)

**Verdict**: ALIGNED
**Mode**: B
**Anchors**:
- PRD §3 Commercial Thesis (Agreed): "Verifiable historical accuracy of individual buy-side voices — the track record database … the only genuinely durable commercial asset … requires time (not just engineering). The track record database must be built from PoC day one."
- PRD §4 Success Criteria C5: "Every scored signal is persisted with all raw inputs … AND outcome metrics … This is the regression dataset for MVP weight calibration and the track record database for commercial use."
- PRD §4 Success Criteria C6: "All five conviction factors … are computed for every signal and stored individually in the DB with config-driven weights."
- PRD §4 Success Criteria C9: "On pipeline startup, inactive primary accounts are automatically replaced by backup accounts so the active count stays at exactly 30."
- PRD §6.2 Signal processing items 7–12: three-layer ticker extraction, whitelist, Haiku directional scoring, five-factor model with config-driven weights, two-tier virality, conflict handling.
- PRD §6.4 Delivery item 16: "Act Now section: maximum 5 signals displayed, ordered by conviction score descending."
- PRD §6.5 Data architecture item 22: "Scoring weights and thresholds as DB-stored config (not hardcoded)."
- PRD §7 Scope OUT: "Web dashboard / UI: PoC is WhatsApp-only."

**Analysis**: Every Milestone 2 task maps directly to a named §6 Scope IN requirement. TASK-003 builds the multi-tenant schema and config-driven scoring weights (§6.5 items 20–23, C5, C6). TASK-004 implements the `SocialMediaSource` ABC, twikit ingestion, and `AccountRegistry` backup-promotion logic (§6.1 items 1–2, 5, C9). TASK-005 delivers the NYSE trading calendar for collection-window and holiday handling (§6.1 item 3). TASK-006 delivers three-layer ticker extraction with whitelist (§6.2 items 7–8). TASK-007 delivers Claude Haiku directional scoring with Pydantic validation and sync repo wiring (§6.2 item 9). TASK-008 delivers the full five-factor scoring engine, conflict resolver, and signal classifier with DB-stored config weights (§6.2 items 10–12, C6). TASK-009 delivers amplifier fetcher and market-cap resolver with 7-day cache (§6.1 item 6, §6.2 items 4, 10). TASK-010a performs legacy cleanup without adding new scope. TASK-010b delivers the morning pipeline orchestrator that wires all components end-to-end (§4 C1, C3). TASK-010c (conflict block renderer, previously ALIGNED per 2026-04-19 log entry) delivers the conflict signal UI and enforces the 5-signal cap (§6.4 item 16, §6.2 item 12). Post-excerpt blockquote standardisation and the 5-signal ACT NOW cap are renderer-level refinements within §6.4; neither introduces new scope nor touches §7 Scope OUT. One open documentation gap carried from Milestone 1: the Milestone 1 log entry flagged that four user-approved format deviations (conviction emoji, CORROBORATED removal, 20-word truncation, disclaimer removal) were not yet captured as §8 Override entries — this gap remains open and should be closed before the Milestone 3 gate.

**Recommendation**: ALIGNED — proceed to Milestone 3. No proposal should be rejected or revised. One housekeeping action remains outstanding from the Milestone 1 DRIFTING verdict: the architect should add §8 override entries for the four Milestone 1 format decisions before the Milestone 3 gate so the PRD single source of truth is complete.

**User outcome**: [Leave blank — to be filled when user decides]

---

## 2026-04-19 — Edge case test coverage expansion for TASK-016 (Milestone 5)

**Verdict**: PARTIAL (subset ALIGNED, subset DRIFTING)
**Mode**: B
**Anchors**:
- PRD §4 Success Criteria C1–C9: PoC success is framed around the engine working end-to-end — signals flow, scores persist, messages ship, raw data is intact.
- TASKS.md Milestone 5 goal: "Integration tests, security review, and README complete. Known-good state ready for 4-week personal-use PoC validation."
- TASKS.md TASK-016 acceptance criteria: `pytest` passes ≥80% coverage; all external deps mocked; 10 fixtures covering named scenarios; no live-credential requirements.
- PRD §7 Scope OUT: "Weight auto-recalibration / feedback-loop retraining: MVP scope."
- PRD §11 Risks and Mitigations: twikit suspension, Twilio silent-fail, yfinance staleness, Burry-pattern deletion, and Claude Haiku misclassification are explicitly named as PoC-level risks with stated mitigations.

**Analysis**: The PoC question is "does the engine work?" — test coverage that proves the engine survives the exact failure modes named in §11 is directly aligned. Edge cases that protect the correctness of scoring logic, signal persistence, and message delivery (the three things §11 explicitly worried about) belong in PoC. Edge cases that test graceful degradation under sustained production load — rate-limit retry loops, partial batch recovery, character-limit truncation — are reliability/hardening concerns that the three-phase framework explicitly reserves for MVP. The prior log shows no repeated drift toward hardening; this is a first-time question.

**PoC shortlist (wire into TASK-016)**:
- Claude returns malformed JSON → zero-score sentinel (PRD §6.2 item 9; §11 Claude Haiku misclassification risk)
- Ticker that's a common word (e.g. "IT") → filtered by whitelist (PRD §6.2 items 7–8; §11 false-positive risk)
- Score exactly on tier boundary (final_score = 0.70) → correct tier assigned (PRD §6.2 items 10–11)
- Post with 10+ ticker mentions → top-N selection without crash (PRD §6.2 item 7)

**Deferred to MVP BACKLOG**: account suspended mid-run (retry/swap is MVP resilience); twikit 429 retry (back-off policy is hardening); Claude API timeout (timeout policy is hardening; zero-score sentinel handles the output side); DB write fails mid-pipeline (partial-batch recovery is operational resilience); partial signal batch (same); Twilio 429 (§11 rates this Low at PoC — 2 msgs/day); message over 4,000 char (delivery UX hardening; no PRD length contract at PoC).

**Recommendation**: PARTIAL — add the four PoC edge cases to TASK-016's existing fixture list (expands from 10 to ~14 fixtures; appropriate for ≥80% coverage). No separate task needed. Log the seven deferred cases to BACKLOG.md for MVP before TASK-016 begins.

**User outcome**: [Leave blank — to be filled when user decides]

---

## 2026-04-19 — Milestone 3 deliverable review: TASK-011 through TASK-013b (market data client, outcome engine, evening renderer + orchestration, renderer format overhaul)

**Verdict**: ALIGNED
**Mode**: B
**Anchors**:
- PRD §3 Commercial Thesis (Agreed): "The track record database must be built from PoC day one."
- PRD §4 Success Criteria C2: "A WhatsApp message arrives between 4:30–5:30 PM ET on every US trading day, containing outcome metrics (overnight return, tradeable return, excess/vol score) for flagged stocks and a 30-day per-poster scorecard ranked by average excess/vol score."
- PRD §4 Success Criteria C5: "Every scored signal is persisted with all raw inputs … AND outcome metrics … This is the regression dataset for MVP weight calibration and the track record database for commercial use."
- PRD §4 Success Criteria C7: "For every flagged signal, the system computes `(stock_return − SPY_return) / stock_20d_vol` and stores it alongside the raw returns."
- PRD §6.3 Outcome computation items 13–15: `overnight_return`, `tradeable_return`, `excess_vol_score`; SPY return and 20d vol stored for transparency; 30-day scorecard per poster ranked by avg excess/vol.
- PRD §6.4 Delivery item 17: "Per-stock outcome block shows three metrics: overnight return, tradeable return, excess/vol score — with `(SPY: +X% | vol: X%)` shown in parentheses for transparency."
- PRD §7 Scope OUT: "Web dashboard / UI: PoC is WhatsApp-only."

**Analysis**: All four Milestone 3 tasks map directly to named §6 Scope IN requirements. TASK-011 delivers `fetch_stock_vol` and `fetch_spy_return` with yfinance + Alpha Vantage fallback (§6.3 items 13–14, PRD Assumption 4, C7). TASK-012 delivers `OutcomeEngine` and `ScorecardAggregator` — the exact outcome schema (overnight_return, tradeable_return, spy_return, stock_20d_vol, excess_vol_score) demanded by C5, C7, and §6.3 items 13–15; the track-record database (§3 moat) begins accumulating data here. TASK-013 delivers the evening renderer and `run_evening` orchestration with always-send and `--use-fixtures`, closing C2 and C3. TASK-013b's format overhaul (numbered signals, D2D/O2C labels, decimal score, conflict grouping, 5-slot cap) is a renderer-level UX refinement that is user-approved and stays within the WhatsApp-only PoC boundary; it tightens, not expands, the evening output. No §7 Scope OUT items are touched. The Milestone 1 documentation gap (four §8 override entries outstanding) remains open from prior log entries — this milestone does not worsen it, but it should be closed before the Milestone 4 gate.

**Recommendation**: ALIGNED — proceed. Milestone 3 fully delivers C2, C5, C7, and the track record data foundation required by §3. One housekeeping action carries forward: the architect should add §8 override entries for the four Milestone 1 format deviations (conviction emoji, CORROBORATED tag removal, 20-word truncation, disclaimer removal) before Milestone 4 begins.

**User outcome**: [Leave blank — to be filled when user decides]
