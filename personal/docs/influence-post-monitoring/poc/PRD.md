# Product Requirements Document — Influence Post Monitoring

> **Status**: Draft
> **Author**: architect
> **Last Updated**: 2026-04-18
> **Phase**: PoC
> **Depends on**: DISCOVERY-NOTES.md, MARKET-ANALYSIS.md, RESEARCH-REPORT.md, UX-SPEC.md
> **Supersedes**: 2026-04-15 PRD (email + 17-account + win-rate design — rebuilt in this revision)

---

## 1. Problem Statement

Viral posts from well-known institutional investors on X/Twitter cause short-term stock rallies that the user is missing systematically. The user does not monitor X continuously and discovers these events after the move has already happened. The canonical example is Bill Ackman's viral X post about FNMA/FMCC (late April 2026), which caused a ~50% rally the following Monday — a signal the user only noticed retrospectively.

The user's core insight is that **the signal is not the quality of the investment thesis, but the social momentum** — how many institutional funds notice a credible voice and pile in. A post by a credible figure crossing a virality threshold is effectively a coordination mechanism for fund participation. No existing product addresses this specific niche: curated, credibility-weighted, buy-side social-signal monitoring with verifiable track records.

---

## 2. Target User

**Primary user (PoC)**: the project's builder — a Data Scientist / ML Engineer based in Canada, self-directed retail investor with a US-equity focus. Technically sophisticated but not a full-time trader. Wants a morning briefing that enables "should I watch this today" decisions, not automated execution. Values explainability: who posted, why it scores highly, and whether that investor has been right before.

**Success for the primary user**: never again miss a signal like the Ackman/FNMA tweet that caused a 50% rally the following Monday.

**Eventual commercial users (documented for scope, not built at PoC)**:
- Active retail swing traders (Persona B, $25–$50/month)
- **Independent RIAs / small funds (Persona C, $150–$400/month — highest commercial value)**
- Finance content creators (Persona D, $50–$100/month)

---

## 3. Commercial Thesis (Agreed)

Adopted from MARKET-ANALYSIS.md and confirmed by the user.

- **Adopted commercial verdict**: **Plausible commercial SaaS — path is narrow, regulatory hurdle must be cleared first.** Market gap is real: no current product tracks curated buy-side / activist / short-seller social voices with conviction scoring and verifiable track records. The thesis is validated by the TipRanks acquisition (Goldman Sachs, 2021, ~$175M), which proves individual-voice track record scoring has acquisition-level commercial value.
- **Adopted uniqueness / moat angle**: **Verifiable historical accuracy of individual buy-side voices — the track record database.** TipRanks does this for Wall Street sell-side analysts; no one does it for activists, short sellers, and fund managers who post publicly on X. This is the **only genuinely durable commercial asset**, and it requires time (not just engineering). The track record database must be built from PoC day one.
- **Adopted monetization angle**: **Multi-tier retail + RIA SaaS** with the RIA segment as the priority commercial target. Retail tier $35–$50/month (high churn, price-sensitive); RIA/small-fund tier $150–$400/month (durable, higher ARPU). Historical dataset licensing deferred to 12–18 months post-launch. Retail is the volume; RIA is the profit.
- **Regulatory precondition (hard)**: **A securities-attorney consult ($500–$1,500) is required before any commercial launch.** Systematically distributing scored "Act Now" recommendations for compensation sits in legally gray territory under the Investment Advisers Act of 1940. This consult is a hard prerequisite for the Beta phase, not optional. All PoC and MVP output is framed as "information," never "recommendations."
- **Deviations from MARKET-ANALYSIS**: None — adopted as recommended.
- **Decision date**: 2026-04-18

If the user changes their mind on any of these, this section will be updated and business-analyst will re-run against current BACKLOG items.

---

## 4. Success Criteria

The PoC is successful when all of the following are true:

- [ ] **C1 — Morning alert ships daily**: A WhatsApp message arrives before 9:00 AM ET on every US trading day, containing an Act Now section and a Watch List section (or an explicit "no signals" message per the always-send rule).
- [ ] **C2 — Evening summary ships daily**: A WhatsApp message arrives between 4:30–5:30 PM ET on every US trading day, containing outcome metrics (overnight return, tradeable return, excess/vol score) for flagged stocks and a 30-day per-poster scorecard ranked by average excess/vol score.
- [ ] **C3 — Always-send honored**: Both messages ship on every trading day even when there are zero signals or zero outcomes to report — silence is never an outcome.
- [ ] **C4 — At least one actionable signal per week**: Across ~4 weeks of PoC validation, the system surfaces at least one signal per week that the user judges as genuinely actionable (would have considered entering a trade).
- [ ] **C5 — Raw data store intact**: Every scored signal is persisted with all raw inputs (post text, engagement metrics, retweeter list, all five component scores) AND outcome metrics (overnight return, tradeable return, SPY return, 20d vol, excess/vol score). This is the regression dataset for MVP weight calibration and the track record database for commercial use.
- [ ] **C6 — Five-factor scoring works end-to-end**: All five conviction factors (credibility, two-tier virality, directional consensus, amplifier quality, liquidity modifier) are computed for every signal and stored individually in the DB with config-driven weights.
- [ ] **C7 — Excess/vol score computed correctly**: For every flagged signal, the system computes `(stock_return − SPY_return) / stock_20d_vol` and stores it alongside the raw returns.
- [ ] **C8 — Burry-pattern resilience**: If a post is deleted between fetch cycles, the stored post text, engagement metrics, and scores are retained; the signal is still alerted on with `deleted=True` flagged.
- [ ] **C9 — Account validation and backup promotion**: On pipeline startup, inactive primary accounts are automatically replaced by backup accounts so the active count stays at exactly 30.

---

## 5. Commercial-Signal Instrument

Per CLAUDE.md and per MARKET-ANALYSIS.md §Commercial Signal Instrument.

- **Instrument**: **Public accuracy leaderboard with waitlist CTA** — a free public web page (built at MVP, NOT PoC) showing each monitored investor's rolling 30/90/180-day average excess/vol score across their flagged signals, with a single "Join waitlist for morning briefing" CTA.
- **What it measures**: Does the market pull hard enough on credibility-weighted buy-side social signals to justify commercial build-out?
- **Where it lives at PoC**: Track record database — every signal's `excess_vol_score` is persisted per poster in the `signals` table and aggregated into the per-poster scorecard shown in the evening WhatsApp summary. The public web page is MVP scope; the **data foundation** it requires is PoC scope and must be complete from day one.
- **How it's read**:
  - **PoC**: evening WhatsApp summary 30-day scorecard shows top 5 posters by average excess/vol score.
  - **MVP**: weekly waitlist-signup count from the public leaderboard page.
- **Target at MVP → Beta decision point**: **50+ waitlist signups per week after 8 weeks of public operation without paid promotion.** Below **20/week after 12 weeks** = market not pulling hard enough; no Beta investment.
- **Scope protection**: [x] Confirmed protected in milestone planning. The track record data model (`signals.overnight_return`, `signals.tradeable_return`, `signals.excess_vol_score`, `signals.spy_return`, `signals.stock_20d_vol`, per-poster aggregation) is a Milestone 2 / 3 artifact, not deferrable. Every scope cut discussion must preserve this schema.

---

## 6. Scope — What's IN

### 6.1 Ingestion
1. **X/Twitter monitoring of 30 curated primary accounts** plus a **15-account backup list**.
2. **Account validation and backup promotion**: on pipeline startup, verify each primary account is reachable; promote a backup to primary if inactive. Active count stays at exactly 30.
3. **Post collection window**: strictly from **previous market close to alert send time (~9:00 AM ET)**. Weekend posts accumulate from Friday close to Monday morning. Prev-close resolution uses a trading calendar (NYSE schedule) that correctly handles weekends AND US public holidays — via `pandas_market_calendars` or `exchange_calendars`.
4. **Polling cadence**: **2-hour intervals during market hours (9 AM–5 PM ET), once overnight.** Balances twikit suspension risk against Burry-pattern post deletion risk.
5. **twikit-based scraping** (dedicated throwaway X account per ToS-risk mitigation), abstracted behind a `SocialMediaSource` interface for a one-file swap to the official API at MVP.
6. **Amplifier data fetch**: for posts crossing the Act Now virality threshold, `get_retweeters(tweet_id)` is called once and all returned User IDs are persisted. This is the amplifier-quality regression dataset.

### 6.2 Signal processing
7. **Three-layer ticker extraction**: cashtag regex → standalone uppercase with false-positive filter → spaCy NER (`en_core_web_sm`) → Yahoo Finance resolver for ORG entities.
8. **Ticker whitelist**: all extractions validated against **S&P 500 + Russell 3000** (GitHub CSV dataset) before scoring.
9. **Directional scoring via Claude Haiku**: LLM call classifies `direction` (LONG/SHORT/NEUTRAL/AMBIGUOUS), `conviction_level`, `key_claim`, `argument_quality`, `time_horizon`, `market_moving_potential`. Pydantic-validated. Score=0 sentinel on parse failure.
10. **Five-factor conviction scoring model** with **config-driven weights** (stored in DB config rows, not hardcoded):
    - Factor 1 — Influencer credibility (1–10, seeded manually per DATA-SOURCES.md)
    - Factor 2a — Post virality absolute (1–10, for Act Now)
    - Factor 2b — Post virality velocity (views/hour, for Watch List)
    - Factor 3 — Directional consensus (1–10, more posters same direction on same ticker → higher)
    - Factor 4 — Amplifier quality (1–10, monitored-account retweeters + follower tiers)
    - Factor 5 — Stock liquidity modifier (0.8×–1.3× multiplier by market-cap class)
11. **Two-tier virality logic**:
    - **Tier 1 / Act Now**: posts above configurable absolute threshold. **Starting values: 50,000 views OR 500 reposts** (thresholds are configurable, not hardcoded).
    - **Tier 2 / Watch List**: posts below threshold but with high views/hour velocity.
12. **Conflict handling in the morning alert**:
    - **Same poster, same direction, multiple posts on same ticker**: use the **highest-virality** post.
    - **Same poster, conflicting direction**: use the **most recent** post; tag the signal block with `⚠️ Direction changed`; apply a conviction-score penalty.
    - **3+ different posters on same ticker with mixed directions**: group by direction. Each direction group becomes its own signal block. Both blocks appear in the alert with `⚠️ Conflicted — opposing view exists` tag. Directional consensus score reflects the count within each direction group.

### 6.3 Outcome computation
13. **Two return calculations per signal** (evening pass):
    - `overnight_return = (today_close − prev_close) / prev_close` — pure signal capture.
    - `tradeable_return = (today_close − today_open) / today_open` — actual return if entered at open.
    - `prev_close` resolved via NYSE trading calendar (handles weekends AND public holidays).
14. **Excess/vol score as first-class metric** (replaces binary win/loss entirely):
    - `excess_vol_score = (stock_return − SPY_return) / stock_20d_vol`
    - Signed, continuous. Positive = stock generated vol-adjusted alpha; negative = stock underperformed market on vol-adjusted basis.
    - `stock_return` = overnight return (primary — the alert captured the overnight move).
    - SPY return measured over the same window.
    - `stock_20d_vol` = 20-trading-day realized volatility of the stock at signal time.
    - SPY return and 20d vol stored alongside for transparency in the evening message.
15. **30-day scorecard**: **per-poster (NOT per-symbol)**, ranked by **average excess/vol score across all their signals**. No win-rate percentages anywhere in PoC output.

### 6.4 Delivery (WhatsApp only — no web UI at PoC)
16. **Morning alert** (~9:00 AM ET, via Twilio WhatsApp with CallMeBot fallback):
    - Act Now section: **maximum 5 signals displayed**, ordered by conviction score descending.
    - Watch List section: maximum 5 signals displayed, ordered by views/hour descending.
    - Per signal block: `DIRECTION $TICKER (Market Cap Class)`, conviction dots `●●●●○`, poster handle, inline corroboration/conflict tags, quote fragment ≤ 150 chars. Win-rate fraction not shown at PoC (excess/vol is the metric); poster handle + conviction dots are the trust surface.
    - Always-send rule: the message ships on every trading day even with zero signals.
17. **Evening summary** (~4:30–5:00 PM ET):
    - **Per-stock outcome block shows three metrics**: overnight return, tradeable return, excess/vol score — with `(SPY: +X% | vol: X%)` shown in parentheses for transparency.
    - SHORT signals always annotated `_(short = gain)_` / `_(short went up)_` on negative moves.
    - Watch List outcomes shown separately (monitored only, no scorecard impact).
    - 30-day scorecard: per-poster ranking by **average excess/vol score** across all their signals.
    - `⚠️ Sample still building` warning until 20+ trading days of data.
    - Always-send rule: ships on every trading day even with zero outcomes.
18. **Regulatory disclaimer footer** on every message: `_This is information about public posts, not investment advice. Do your own research._`
19. **Delivery abstraction**: `MessageDelivery` interface with `send(text: str) -> bool` contract. Twilio WhatsApp Sandbox is primary; CallMeBot is automatic fallback.

### 6.5 Data architecture
20. **SQLite via Turso free tier** — see TDD §2.4 for the persistence decision. Avoids GitHub Actions ephemeral-runner data loss without switching to Postgres.
21. **Multi-tenant schema**: `user_id` and `tenant_id` columns on every table, defaulting to 1 for all PoC rows.
22. **Scoring weights and thresholds as DB-stored config** (not hardcoded): five factor weights, virality thresholds, conflict penalty, market-cap bucket boundaries.
23. **Raw data persistence**: posts, engagement metrics, per-factor scores, retweeter identities, SPY/vol context, all outcome metrics. This IS the commercial asset.

---

## 7. Scope — What's OUT

- **Web dashboard / UI**: PoC is WhatsApp-only.
- **Public accuracy leaderboard web page**: MVP scope. At PoC, the data foundation (signal records + excess/vol per poster) is built; the public page itself is not.
- **Watch List → Act Now graduation / intraday re-alerts**: if a Watch List signal crosses the threshold between 9:00–9:30 AM, no second message is sent at PoC. Deferred to MVP.
- **LinkedIn, Substack, YouTube, podcast monitoring**: MVP scope.
- **Reply-based correction flow** (e.g., "ignore $TICKER"): MVP candidate, not PoC.
- **Intraday trading signals** and **options flow** as a 6th confirmation signal: MVP/Beta.
- **Automated trade execution**: never in scope.
- **Auth, billing, multi-user UI**: Beta scope.
- **Weight auto-recalibration / feedback-loop retraining**: MVP scope. PoC only stores the raw regression dataset.
- **Win-rate percentage metric** / binary "hit" definition: removed entirely. Replaced by excess/vol score.
- **Historical dataset licensing / external API tier**: Beta scope.
- **Commercial launch of any kind**: Beta scope, and only after the securities-attorney consult (§3 regulatory precondition).
- **Portfolio management, position sizing, stop losses**: out of scope at every phase.

---

## 8. UX-SPEC Override Decisions

UX-SPEC.md was authored before the user reviewed the PRD draft. During review, the user made the following decisions that override, extend, or replace specific UX-SPEC statements. They are collected here so an implementer has a single source of truth for every deviation. When this section and UX-SPEC.md conflict, this section governs. When this section and the individual §6 requirements conflict, §6 governs.

**Override 1 — Win-rate replaced by excess/vol score**
*UX-SPEC says*: Track record was framed around win-rate fractions like "17/25"; binary hit/miss underpinned the trust metric (see UX-SPEC supersede banner).
*PRD decision*: Win-rate is removed entirely. The trust metric for every poster is the continuous `excess_vol_score = (stock_return − SPY_return) / stock_20d_vol`. No fractions, no hit/miss labels anywhere in PoC output.
*PRD anchor*: §6.14, §6.15, §7 (Scope OUT)

**Override 2 — 30-day scorecard rolls up per poster, not per symbol**
*UX-SPEC says*: UX-SPEC's scorecard section described a "30-day scorecard" without explicitly fixing the aggregation axis; examples leaned toward per-poster but the contract was ambiguous.
*PRD decision*: The 30-day scorecard aggregates per poster, never per symbol. Ranking key is `mean(excess_vol_score)` across all of that poster's signals in the window.
*PRD anchor*: §6.15

**Override 3 — Excess/vol shown per stock in the evening outcome block**
*UX-SPEC says*: UX-SPEC's outcome block format (before supersede) showed two return lines per stock — overnight and tradeable.
*PRD decision*: Evening outcome shows three metrics per stock — overnight return, tradeable return, excess/vol score — with `(SPY: +X% | vol: X%)` shown in parentheses for transparency.
*PRD anchor*: §6.17

**Override 4 — Excess/vol `building…` display threshold is 5 signals, not 20**
*UX-SPEC says*: Open UX Question #7 resolved the threshold at 5 signals per poster before a σ value is shown; prior drafts had suggested 20.
*PRD decision*: Display `30d avg excess/vol: building…` until a poster has 5 or more scored signals. No σ value is shown at N<5.
*PRD anchor*: §6.16 (per-signal trust surface); resolves UX-SPEC Open Question #7

**Override 5 — `⚠️ Sample still building` scorecard warning threshold is 20 trading days**
*UX-SPEC says*: UX-SPEC referenced "< 20 days" as the warning trigger in the scorecard mock but did not pin the unit (calendar vs trading days) at the PRD contract level.
*PRD decision*: The `⚠️ Sample still building` warning renders until 20 trading days of signal data have accumulated (NYSE calendar). Calendar days are not used.
*PRD anchor*: §6.17

**Override 6 — Direction conflict handling: same-direction grouped, opposite-direction tagged `⚠️ Conflicted`**
*UX-SPEC says*: UX-SPEC did not specify how the renderer handles 3+ posters on the same ticker with mixed directions.
*PRD decision*: When 3+ posters post on the same ticker with mixed directions, posters are grouped by direction. Each direction group emits one signal block; both blocks appear in the alert and both get the `⚠️ Conflicted — opposing view exists` tag. F3 directional consensus is counted within each group, not across the union.
*PRD anchor*: §6.12

**Override 7 — Direction-flip penalty set to 0.0 (configurable), tag-only behavior**
*UX-SPEC says*: UX-SPEC did not define a numerical penalty for same-poster direction flips.
*PRD decision*: `scoring_config.direction_flip_penalty` defaults to 0.0 at PoC. The `⚠️ Direction changed` tag still renders whenever `direction_flip=True`; no score is deducted until the operator writes a non-zero value to the config row. The deduction mechanism is wired end-to-end so activation is a single DB update.
*PRD anchor*: §6.12 (conflict handling); implementation at TDD §2.3 ScoringEngine and ConflictResolver

**Override 8 — Corroboration format shows the second poster's handle and quote, not just a count**
*UX-SPEC says*: Early UX-SPEC drafts rendered corroboration as a count tag (e.g., `CORROBORATED — 2 posters`) without displaying the second voice.
*PRD decision*: When 2 posters agree on a ticker + direction, the Act Now signal block shows the second poster's `@handle`, their 30d avg excess/vol, and a ≤150-char quote fragment underneath the primary poster's block — not only a count. The count tag still appears inline but is supplemented by the full second voice.
*PRD anchor*: §6.16 (signal block format); see UX-SPEC mock lines 109–113

**Override 9 — Always-send rule is a hard requirement, not a UX preference**
*UX-SPEC says*: UX-SPEC framed always-send as a strong recommendation ("silence is ambiguous") and flagged it as Open UX Question #6 for PRD confirmation.
*PRD decision*: Always-send is a hard PoC requirement. Both the morning alert and evening summary ship on every trading day — no signals is an explicit message, never silence.
*PRD anchor*: §6.16, §6.17, Success Criterion C3

**Override 10 — Excess/vol parenthetical format is `_(vs. SPY / vol)_`**
*UX-SPEC says*: UX-SPEC showed the σ value followed by the italic tag `_(vs. SPY / vol)_` in the outcome block mock but did not contractually pin the wording.
*PRD decision*: Evening outcome rows render excess/vol as `+Xσ _(vs. SPY / vol)_`, with SPY return and 20d vol shown separately in parentheses on the metric line for transparency.
*PRD anchor*: §6.17; see UX-SPEC mock lines 163–165

**Override 11 — `⚠️ Direction changed` tag renders regardless of penalty value**
*UX-SPEC says*: UX-SPEC did not define a direction-flip tag at all.
*PRD decision*: Whenever a signal has `direction_flip=True` (same poster reversed direction within the collection window), the signal block renders a `⚠️ Direction changed` tag. This is independent of the penalty value — even at `direction_flip_penalty=0.0`, the tag still shows so the user sees the conviction signal.
*PRD anchor*: §6.12; implementation at TDD §2.3 ConflictResolver

**Override 12 — Watch List graduation: no mid-session upgrade; hold until next morning**
*UX-SPEC says*: Open UX Question #5 asked whether a Watch List signal crossing the threshold between 9:00–9:30 AM should trigger a second message.
*PRD decision*: No intraday re-alert at PoC. If a Watch List signal graduates to Act Now after the 9:00 AM alert, the event is deferred — no second message is sent. The user sees the graduation the following morning. Intraday re-alerts are MVP scope.
*PRD anchor*: §7 (Scope OUT); resolves UX-SPEC Open Question #5

**Override 13 — Prev-close resolution uses NYSE trading calendar, handles weekends and holidays**
*UX-SPEC says*: Open UX Question #3 asked what `prev_close` should be for weekend or multi-day-old posts (e.g., "Use Friday close?").
*PRD decision*: `prev_close` is resolved via `pandas_market_calendars.previous_trading_day()` on the NYSE schedule — this correctly handles weekends AND US public holidays (e.g., a Monday post after Good Friday uses Thursday close, not Friday). Ad-hoc weekday arithmetic is prohibited anywhere in the pipeline.
*PRD anchor*: §6.3, §6.13; resolves UX-SPEC Open Question #3

**Override 14 — Conviction display uses filled-tick emoji + percentage, not dot notation**
*UX-SPEC says*: Conviction was rendered as a 5-slot dot gauge `●●●●○` in every signal block; empty circles filled out the gauge so the denominator was always visible.
*PRD decision*: Conviction renders as filled ticks only plus a percentage score — e.g. `✅✅✅ - 61%` — with no empty markers. The tick count encodes the rounded conviction bucket; the percentage is the underlying score. Decided during Milestone 1 user review (2026-04-18).
*Rationale*: User found emoji + percentage more readable and immediately interpretable than dot notation; the denominator is implicit and the numeric score removes the ambiguity dots leave when two signals round to the same bucket.
*PRD anchor*: §6.16 (morning alert signal block format); supersedes the `●●●●○` contract in §6.16

**Override 15 — Inline corroboration count tag removed**
*UX-SPEC says*: Corroborated Act Now signals carried an inline `CORROBORATED — N posters` tag on the signal block, supplementing the second-voice display from Override 8.
*PRD decision*: The inline corroboration count tag is removed. When multiple poster handles are listed under a signal, corroboration is self-evident from the rendered list and no separate label is emitted. Override 8's second-voice display (handle + 30d avg excess/vol + quote fragment) remains in force — only the redundant count tag is dropped. Decided during Milestone 1 user review (2026-04-18).
*Rationale*: With the second voice already rendered explicitly, the `CORROBORATED — N posters` tag duplicated visible information and reduced readability.
*PRD anchor*: §6.16 (morning alert signal block format); narrows Override 8

**Override 16 — Per-message disclaimer footer removed at PoC (reinstatement required pre-distribution)**
*UX-SPEC says*: Every outbound WhatsApp message carried the footer `_This is information about public posts, not investment advice. Do your own research._`
*PRD decision*: The disclaimer footer is removed from both the morning alert and the evening summary for the remainder of the PoC. Decided during Milestone 1 user review (2026-04-18).
*Rationale*: Removed for PoC personal-use readability only. PRD §11 cites the disclaimer as the control for regulatory-action risk. Must be reinstated before any non-personal-use distribution (MVP Beta or shared access).
*PRD anchor*: §6.18 (disclaimer footer contract); §11 Risks and Mitigations (regulatory-action row); supersedes §6.18 for PoC scope only

> When UX-SPEC.md and this section conflict, this section governs. When this section and the individual §6 requirements conflict, §6 governs.

---

## 9. User Workflow

**Trading day morning (~9:00 AM ET)**:
1. User wakes up, opens WhatsApp.
2. Reads the morning alert: date header → Act Now (≤5 signals) → Watch List (≤5 signals) → footer.
3. For each flagged ticker, checks poster handle, conviction dots, corroboration/conflict tags, and quote fragment.
4. Decides whether to open a position, set a watch alert, or ignore. Market opens at 9:30 AM ET.

**Trading day evening (~4:30–5:00 PM ET)**:
5. User opens WhatsApp on evening summary arrival.
6. Reads per-stock outcome blocks — overnight return, tradeable return, excess/vol score for each flagged stock (with SPY return and 20d vol shown in parentheses).
7. Scans the 30-day per-poster scorecard ranked by average excess/vol score.
8. Builds a longitudinal sense of which posters generate vol-adjusted alpha. Trust accrues (or erodes) over ~20 trading days.

**No action required between messages.** The user is a passive recipient. No reply parsing, no interaction surface beyond reading.

**Days with no signals**: both messages still ship, with explicit "no signals" copy per the always-send rule.

**Non-trading days** (weekends, US market holidays): no messages sent. The NYSE trading calendar governs.

---

## 10. Assumptions

1. **twikit remains functional** throughout PoC validation (~4 weeks). If X patches against it, the `SocialMediaSource` interface allows a one-file swap to tweepy + Basic API ($100/month) at MVP.
2. **A dedicated throwaway X account** (separate from personal) is used for twikit login, per ToS-risk mitigation in RESEARCH-REPORT §9.
3. **Twilio WhatsApp Sandbox** is activated by the user (manual join-message step) **before Milestone 1 can be demoed end-to-end**. Flagged in TASKS.md as a human prerequisite.
4. **yfinance OHLC data** is accurate and fresh within pipeline tolerance. Freshness assertion retries once, then falls back to Alpha Vantage (free 25 req/day).
5. **Turso free tier** (SQLite-compatible) is sufficient for PoC volume: ~30 accounts × ~10 posts/run × multiple runs/day × 4 weeks ≈ a few thousand rows.
6. **The 30 primary accounts are representative enough** to surface at least one actionable signal per week. If inactive, the 15-account backup list fills the gap.
7. **Manual credibility seeds** (1–10 per account, per DATA-SOURCES.md) are good enough for PoC. MVP recalibrates from the regression dataset.
8. **The user's personal phone number** is the only message recipient at PoC.
9. **The S&P 500 + Russell 3000 whitelist** captures the full universe of tickers the user cares about. Tickers outside this set are dropped as extraction noise (a supplement for FNMA/FMCC-style OTC names is maintained).
10. **NYSE trading calendar is sufficient** for determining prev_close and collection windows. Canadian / European holidays do not apply.

---

## 11. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| twikit ToS violation → X account suspension | Medium | High | Dedicated throwaway account; `SocialMediaSource` interface for one-file swap to tweepy; polling capped at 2h cadence. |
| Twilio Sandbox silent-fail (credit exhausted, session expired) | Medium | Medium | `MessageDelivery` interface with CallMeBot fallback; startup health-check sends a test message before ingestion runs. |
| yfinance returns stale OHLC | Medium | High | Freshness assertion on every fetch; retry once; Alpha Vantage fallback; log `price_data_source` per signal. |
| Post deletion before fetch (Burry-pattern) | High | Medium | 2-hour polling cadence; store full post text at first fetch; `deleted=True` flag retains the signal for scoring. |
| Ticker extraction false positives at 30-account scale | Medium | Medium | Three-layer pipeline; configurable false-positive filter; S&P 500 + Russell 3000 whitelist; `confidence=LOW` flag on spaCy-only extractions. |
| Claude Haiku misclassifies direction | Low-Medium | Medium | Pydantic validation; zero-score sentinel on parse failure; store raw LLM response for MVP audit. |
| GitHub Actions ephemeral runner destroys SQLite between runs | High (if local SQLite used) | High | **Turso free-tier hosted SQLite** — decided at design gate; no file-commit kludge. |
| Primary account goes inactive mid-PoC | Medium | Low | Backup promotion at pipeline startup; 15 backups available. |
| Regulatory action against "Act Now" framing | Low at PoC (personal use) | High at Beta | Disclaimer footer on every message; securities-attorney consult mandatory before Beta; frame all output as "information," not "recommendations." |
| Low signal volume (fewer than 1 actionable signal / week) | Medium | Medium | The raw data store is still valuable as a regression dataset; extend validation to 6–8 weeks if needed. |
| Twilio rate limit / per-phone compliance hit | Low | Low at PoC | Only 2 messages/trading day/phone; CallMeBot fallback; log delivery receipts. |

---

## 12. Future Considerations

**MVP (post-PoC daily use)**:
- **Public accuracy leaderboard web page** (the commercial signal instrument surface).
- Watch List → Act Now graduation (second message if signal crosses threshold 9:00–9:30 AM).
- Swap twikit → tweepy + Basic API tier.
- Weight recalibration from the regression dataset (gradient boosting or logistic regression on `excess_vol_score`).
- LinkedIn and Substack monitoring as additional `SocialMediaSource` plugins.
- Reply-based correction flow (`ignore $TICKER`).

**Beta (commercial validation)**:
- Securities-attorney consult (regulatory precondition).
- Multi-tenant activation (user_id/tenant_id populated from auth).
- Billing (retail tier $35–$50/mo, RIA tier $150–$400/mo).
- Web dashboard for subscribers.
- API tier for quant/algo buyers ($500–$2K/month).
- Intraday signals and options flow confirmation.

**Long-term**:
- Historical dataset licensing ($10K–$50K/year) once 12–18 months of operation accumulated.
- Podcast transcript and earnings-call feeds as signal sources.
- Platform diversification in response to X pricing/policy shifts.
