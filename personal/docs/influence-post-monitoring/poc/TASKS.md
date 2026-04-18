# Task Breakdown — Influence Post Monitoring

> **Status**: Active
> **Last Updated**: 2026-04-17
> **Depends on**: PRD.md, TDD.md, DATA-SOURCES.md (all approved)

---

## Progress Summary

| Status | Count |
|--------|-------|
| Done | 14 |
| In Progress | 0 |
| Not Started | 6 |
| Blocked | 0 |

---

## Sprint 1: Project Scaffolding and Database Foundation

### TASK-001: Project scaffolding and directory structure
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline
- **Complexity**: Low
- **Depends on**: None
- **Estimated Effort**: S (< 2 hours)
- **Context**: Establishes the directory layout defined in TDD.md Section 8 and installs all pinned dependencies. This is the foundation every subsequent task builds on.
- **Description**: Create the project directory structure under `projects/influence-post-monitoring/`, initialize a Python 3.11 venv, write `requirements.txt` with all pinned dependencies from TDD.md Section 3, create `.env.example` with all env var placeholders, and create `.gitignore` (includes `.env`, `data/twitter_cookies.json`, `data/signals.db`, `logs/`).
- **Acceptance Criteria**:
  - [x] Directory structure matches TDD.md Section 8 exactly (all `__init__.py` files present)
  - [x] `requirements.txt` lists all dependencies with pinned versions: twikit 2.3.3, yfinance (pinned), finvizfinance 1.3.0, spacy 3.8.13, anthropic, pydantic v2, pydantic-settings, resend 2.28.1, APScheduler 3.11.2, httpx, pytest
  - [x] `venv` activates cleanly with `source venv/bin/activate && pip install -r requirements.txt` producing no errors
  - [x] `python -m spacy download en_core_web_sm` succeeds
  - [x] `.env.example` contains all env vars from TDD.md Section 7 with placeholder values
  - [x] `.gitignore` excludes `.env`, `data/twitter_cookies.json`, `data/signals.db`, `logs/`, `venv/`, `__pycache__/`
  - [x] `config/investors_seed.json` contains all 17 active investor profiles from DATA-SOURCES.md seed list
  - [x] `config/prompts/scoring_prompt.txt` contains the scoring system prompt from DATA-SOURCES.md Source 5
  - [x] `config/false_positive_filter.json` contains the uppercase ticker false-positive word list
  - [x] `config/scoring_weights_seed.json` contains the 5 scoring component weights from TDD.md Section 2.3
- **Notes**: Do not create GitHub repo yet — that happens at TASK-001 completion per CLAUDE.md task completion checklist.

---

### TASK-002: Database schema and repository layer
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline
- **Complexity**: Medium
- **Depends on**: TASK-001
- **Estimated Effort**: M (2-4 hours)
- **Context**: All tables must include `tenant_id` from day one (multi-tenancy requirement from CLAUDE.md and TDD.md). The `signals` table schema is the commercial asset — every sub-score column must exist from the start, even those filled later.
- **Description**: Implement `db/schema.sql` with all CREATE TABLE statements from TDD.md Section 2.4. Implement `db/repository.py` with a `DatabaseRepository` class covering all read/write operations needed by the pipeline. Seed the database with the default tenant, scoring weights, and investor profiles from config files.
- **Acceptance Criteria**:
  - [x] `schema.sql` defines all 8 tables: `tenants`, `investor_profiles`, `posts`, `signals`, `engagement_snapshots`, `index_membership`, `scoring_weights`, `daily_summaries`, `api_usage`
  - [x] All tables have `tenant_id INTEGER NOT NULL DEFAULT 1` except `index_membership`, `api_usage`, and `engagement_snapshots`
  - [x] `posts.external_id` has a UNIQUE index (deduplication)
  - [x] `posts` table includes ML-first social context columns: `bookmark_count`, `quote_tweet_id`, `is_thread`, `thread_position`, `hashtags` (JSON), `mentioned_users` (JSON), `url_links` (JSON), `media_type`, `language`, `follower_count_at_post`, `following_count_at_post`
  - [x] `signals` table includes all sub-score columns (`score_credibility`, `score_conviction`, `score_argument`, `score_engagement`, `score_historical`), return windows (`return_5d`, `return_10d`, `return_30d`), market context (`prev_close_price`, `high_price`, `low_price`, `volume`, `avg_volume_30d`, `volume_ratio`, `sp500_return_pct`, `vix_at_signal`, `sector_return_pct`), stock context (`market_cap_at_signal`, `sector`, `industry`), `morning_rank`, `llm_raw_response`, `llm_input_tokens`, `llm_output_tokens`
  - [x] `engagement_snapshots` table captures periodic engagement metric snapshots per post
  - [x] `DatabaseRepository` has methods: `upsert_investor_profile`, `insert_post`, `insert_signal`, `insert_engagement_snapshot`, `get_signals_for_date`, `update_signal_prices`, `update_signal_market_context`, `update_investor_accuracy`, `insert_daily_summary`, `get_investor_by_handle`, `log_api_usage`
  - [x] `python -m influence_monitor.db.repository --init` seeds the DB from config files without error
  - [x] After seeding: `SELECT COUNT(*) FROM investor_profiles` returns 17; `SELECT COUNT(*) FROM scoring_weights` returns 5
  - [x] `INSERT OR IGNORE` used for post deduplication (re-fetching same post is a no-op)
- **Notes**: Use `aiosqlite` for async operations. Use raw SQL (no ORM). Connection string sourced from `settings.database_path`.

---

## Sprint 2: Social Media Ingestion

### TASK-003: SocialMediaSource interface and twikit ingestion
- **Status**: Done (2026-04-16)
- **Agent**: data-pipeline
- **Complexity**: High
- **Depends on**: TASK-002
- **Estimated Effort**: L (4-8 hours)
- **Context**: twikit is the highest-risk component (ToS violation, account suspension, X patches). The `SocialMediaSource` ABC must be established first so that the official API swap path (TASK is a stub in this sprint) requires only one module swap. Credential storage for twikit is sensitive — cookies must be gitignored.
- **Description**: Implement `ingestion/base.py` with the `SocialMediaSource` ABC and `RawPost` dataclass. Implement `ingestion/twitter_twikit.py` with `TwitterIngestor`. Implement `ingestion/registry.py` with `SOURCE_REGISTRY`. Create stub files for `twitter_official.py`, `substack.py`, `congressional.py`.
- **Acceptance Criteria**:
  - [x] `SocialMediaSource` ABC defines `fetch_recent_posts(author_handle, since, max_count)` and `source_type()` abstract methods
  - [x] `RawPost` dataclass contains all fields from TDD.md Section 2.1 with correct types, including ML-first social context fields: `bookmark_count`, `quote_tweet_id`, `is_thread`, `thread_position`, `hashtags`, `mentioned_users`, `url_links`, `media_type`, `language`, `follower_count_at_post`, `following_count_at_post`
  - [x] `TwitterIngestor` authenticates via `client.login()` on first run, saves cookies; uses `client.load_cookies()` on subsequent runs
  - [x] `TwitterIngestor.fetch_recent_posts()` filters results to only posts after the `since` parameter
  - [x] `TwitterIngestor.fetch_recent_posts()` stores full tweet object as JSON in `RawPost.raw_payload`
  - [x] Per-account failure logs a WARNING and continues; does not crash the full fetch
  - [x] `IngestorError` is raised when fewer than `settings.min_accounts_threshold` (13) accounts succeed
  - [x] `SOURCE_REGISTRY` maps `"twitter_twikit"` to `TwitterIngestor`
  - [ ] Integration test (manual): run against 3 real accounts and verify `RawPost` objects are returned with non-null `text`, `external_id`, `posted_at`
  - [x] `data/twitter_cookies.json` is in `.gitignore` and is never committed
- **Notes**: Requires a real Twitter account's credentials in `.env`. Test with 3 accounts before running against all 17 to avoid triggering rate limits during development.

---

### TASK-004: Equity symbol whitelist loader
- **Status**: Done (2026-04-16)
- **Agent**: data-pipeline
- **Complexity**: Low
- **Depends on**: TASK-001
- **Estimated Effort**: S (< 2 hours)
- **Context**: All ticker extraction results must be validated against a known US equity universe before entering the scoring pipeline. This whitelist is the final gate against false-positive tickers.
- **Description**: Implement `extraction/equity_whitelist.py`. Downloads (or reads from `data/`) the S&P 500 constituents CSV from the GitHub dataset URL. Optionally loads a Russell 3000 symbol list. Exposes a `SymbolWhitelist` class with a `contains(ticker: str) -> bool` method.
- **Acceptance Criteria**:
  - [x] `SymbolWhitelist.load()` reads `data/sp500_constituents.csv` if present; downloads from GitHub URL if not
  - [x] `SymbolWhitelist.contains("AAPL")` returns `True`
  - [x] `SymbolWhitelist.contains("CEO")` returns `False`
  - [x] `SymbolWhitelist.contains("FNMA")` returns `True` (OTC/pink sheets may not be in S&P 500 — ensure FNMA is handled; expand to Russell 3000 list or maintain a manual supplement)
  - [x] Whitelist loads in under 2 seconds
  - [x] Unit tests: 10 tickers that should pass, 10 common false positives that should fail
- **Notes**: FNMA and FMCC are OTC-traded and not in S&P 500. Include a `data/manual_supplement.txt` file for hand-curated tickers that are monitored but not in major indices.

---

## Sprint 3: Ticker Extraction

### TASK-005: Three-layer ticker extraction pipeline
- **Status**: Done (2026-04-16)
- **Agent**: data-pipeline
- **Complexity**: Medium
- **Depends on**: TASK-004
- **Estimated Effort**: M (2-4 hours)
- **Context**: The three-layer pipeline (regex cashtag → uppercase regex → spaCy NER → Yahoo Finance resolver) is the core NLP component. False positives degrade signal quality; false negatives miss opportunities. The whitelist is the final gate for all layers.
- **Description**: Implement `extraction/ticker_extractor.py` with `TickerExtractor` class. All three layers from TDD.md Section 2.2. Returns a list of `ExtractedTicker` Pydantic models with confidence levels.
- **Acceptance Criteria**:
  - [x] Layer 1 (cashtag regex) extracts `FNMA` from `"$FNMA is massively undervalued"` with confidence `HIGH`
  - [x] Layer 2 (uppercase regex) extracts `TSLA` from `"TSLA could be a 10x"` with confidence `MEDIUM`
  - [x] Common false positives (`CEO`, `IPO`, `ETF`, `GDP`, `FED`) are NOT extracted by Layer 2
  - [x] Layer 3 (spaCy NER) extracts `AAPL` from `"Apple is a strong buy"` via Yahoo Finance resolver → `AAPL`
  - [x] Layer 3 correctly handles `"Fannie Mae"` → `FNMA` via Yahoo Finance resolver
  - [x] All extracted tickers are validated against `SymbolWhitelist` before being returned
  - [x] Tickers extracted only by NER (confidence `LOW`) are flagged and not surfaced in morning email (but stored in DB)
  - [x] Unit tests cover: cashtag extraction, uppercase extraction, NER extraction, false-positive filtering, whitelist gating, deduplication across layers
  - [x] Test against the 4 sample texts from RESEARCH-REPORT.md Section 10.4 and verify expected outputs
- **Notes**: Load spaCy model once at `TickerExtractor.__init__()`, not on each call. Yahoo Finance resolver should cache name→ticker lookups to avoid repeated API calls.

---

## Sprint 4: LLM Scoring

### TASK-006: LLM client interface and Claude Haiku implementation
- **Status**: Done (2026-04-16)
- **Agent**: data-pipeline
- **Complexity**: Medium
- **Depends on**: TASK-001
- **Estimated Effort**: M (2-4 hours)
- **Context**: The Claude Haiku client is the most expensive external dependency (~$0.20/month) but provides the conviction-level and argument-quality scores that no simpler model can produce. Pydantic validation of every response is mandatory — model output inconsistency is a known risk.
- **Description**: Implement `scoring/llm_client.py` with `LLMClient` ABC and `PostScore` Pydantic model. Implement `scoring/claude_client.py` with `ClaudeHaikuClient`. System prompt loaded from `config/prompts/scoring_prompt.txt`.
- **Acceptance Criteria**:
  - [x] `LLMClient` ABC defines `score_post(post_text: str, author_handle: str) -> PostScore`
  - [x] `PostScore` Pydantic model validates all fields from DATA-SOURCES.md Source 5: `tickers`, `direction`, `conviction_level` (0–5), `key_claim`, `argument_quality`, `time_horizon`, `market_moving_potential`, `rationale`
  - [x] `ClaudeHaikuClient` reads system prompt from `config/prompts/scoring_prompt.txt`, not from code
  - [x] `ClaudeHaikuClient` uses JSON instruction in system prompt (Anthropic SDK does not support `response_format` param — JSON enforced via prompt + Pydantic validation)
  - [x] On Pydantic validation failure: logs raw response at WARNING, returns zero-score sentinel (`conviction_level=0`, `direction="AMBIGUOUS"`)
  - [x] On `anthropic.APIError`: retries once after 5 seconds; returns sentinel on second failure
  - [x] Every API call logs `provider`, `input_tokens`, `output_tokens`, `latency_ms`, `status` to `api_usage` table
  - [x] Integration test: score 10 sample posts from `tests/fixtures/sample_posts.json` and verify all return valid `PostScore` objects (no Pydantic errors)
  - [x] `ANTHROPIC_API_KEY` read from `settings`, not hardcoded
- **Notes**: Use `claude-haiku-4-5` model or latest Haiku at time of implementation. Store the model version used in `signals.llm_model_version` for future re-scoring comparisons.

---

### TASK-007: Scoring engine (composite score computation)
- **Status**: Done (2026-04-16)
- **Agent**: data-pipeline
- **Complexity**: Medium
- **Depends on**: TASK-006, TASK-002
- **Estimated Effort**: M (2-4 hours)
- **Context**: The composite score determines what the user sees each morning. Weights are stored in the `scoring_weights` DB table (not code constants) so they can be tuned without redeployment. The engagement normalization uses a rolling max-observed value to prevent any single viral post from skewing all scores.
- **Description**: Implement `scoring/scoring_engine.py` with `ScoringEngine`. Loads component weights from `scoring_weights` DB table. Computes the 5-component composite score for each (post, ticker) pair.
- **Acceptance Criteria**:
  - [x] `ScoringEngine` loads weights from `scoring_weights` table on initialization (not hardcoded)
  - [x] All 5 sub-scores (credibility, conviction, argument, engagement, historical) computed and stored in `signals` table
  - [x] `conviction_level < 2` or `direction in ["NEUTRAL", "AMBIGUOUS"]` → `composite_score = 0.0`
  - [x] Engagement normalization: `(view_count + 5 * repost_count) / max_observed_30d`, clamped to [0, 1]. When `view_count` is NULL: use median engagement for that investor
  - [x] `composite_score` is in range `[0.0, 10.0]`
  - [x] All sub-scores stored in `signals.score_credibility`, `.score_conviction`, etc.
  - [x] Unit tests: verify each sub-score component independently with known inputs and expected outputs
  - [x] Unit test: verify weights from DB are used (mock DB returning different weights and assert composite score changes accordingly)
- **Notes**: `ScoringEngine` does not call Claude or twikit — it receives a `PostScore` and a `RawPost` already stored in DB. Keep it pure and testable.

---

## Sprint 5: Market Data and Index Membership

### TASK-008: Market data client (yfinance + Alpha Vantage fallback)
- **Status**: Done (2026-04-16)
- **Agent**: data-pipeline
- **Complexity**: Medium
- **Depends on**: TASK-001
- **Estimated Effort**: M (2-4 hours)
- **Context**: yfinance's silent stale-data failure is the most dangerous data quality risk in the pipeline. The freshness assertion is mandatory on every fetch. Alpha Vantage is the fallback but has a 25-request/day free tier — use sparingly.
- **Description**: Implement `market_data/base.py` with `MarketDataClient` ABC. Implement `market_data/yfinance_client.py` with `YFinanceClient` including the freshness assertion. Implement `market_data/alpha_vantage_client.py` with `AlphaVantageClient`.
- **Acceptance Criteria**:
  - [x] `MarketDataClient` ABC defines `fetch_open(ticker: str, date: date) -> float` and `fetch_close(ticker: str, date: date) -> float`
  - [x] `YFinanceClient.fetch_open()` calls `yf.Ticker(ticker).history(period="5d")` and asserts `hist.index[-1].date() == date`
  - [x] `YFinanceClient` raises `DataFreshnessError` on staleness; raises `DataUnavailableError` on empty response
  - [x] `AlphaVantageClient` implements the same interface using `GLOBAL_QUOTE` endpoint; `ALPHA_VANTAGE_API_KEY` from settings
  - [x] `YFinanceClient` batch fetch: `fetch_batch_close(tickers: list[str], date: date) -> dict[str, float]` uses `yf.download()` for efficiency
  - [x] On `DataFreshnessError`: retry once after 60 seconds, then fall back to `AlphaVantageClient`; log fallback to `api_usage` table
  - [x] Unit tests: mock yfinance returning today's data (pass), yesterday's data (fail → fallback), empty DataFrame (fail → fallback)
  - [ ] Integration test (manual): fetch OHLC for 5 tickers and verify prices match expected range
- **Notes**: Pin the exact yfinance version. Test the freshness assertion on a market holiday to verify it does not trigger a false alarm.

---

### TASK-009: Index membership resolver and cache
- **Status**: Done (2026-04-17)
- **Agent**: data-pipeline
- **Complexity**: Low
- **Depends on**: TASK-002
- **Estimated Effort**: S (< 2 hours)
- **Context**: Index tier (S&P 500 / NDX / Russell 2000 / MICRO) is displayed on every signal card in the morning email. Resolution uses a cache-first strategy: DB cache → S&P 500 CSV → finvizfinance live call. Refreshed weekly.
- **Description**: Implement `market_data/index_resolver.py` with `IndexMembershipResolver`. Cache-first lookup: check `index_membership` table, fall back to S&P 500 CSV, fall back to finvizfinance live call. Implement a weekly refresh job method.
- **Acceptance Criteria**:
  - [x] `IndexMembershipResolver.resolve(ticker: str) -> str` returns one of: `"SP500"`, `"NDX"`, `"RUT"`, `"MICRO"`
  - [x] SP500 CSV is loaded at init time and populates `index_membership` table if entries are stale or missing
  - [x] Cache hit (ticker in `index_membership` with `last_updated` within 7 days) does not call finvizfinance
  - [x] Cache miss calls finvizfinance; stores result in `index_membership` table
  - [x] finvizfinance failure returns `"MICRO"` as safe default (log WARNING)
  - [x] `IndexMembershipResolver.refresh_weekly()` method refreshes all cached entries older than 7 days
  - [x] Unit tests: AAPL → SP500, GME → MICRO (not in any major index), TSLA → SP500 or NDX
  - [x] `FNMA` resolves to `"MICRO"` (OTC, not in S&P 500 — confirm with finvizfinance response)
- **Notes**: Nasdaq 100 membership is not in the S&P 500 CSV. For NDX: maintain a manual `data/ndx100_symbols.txt` file seeded from a current NDX constituent list.

---

## Sprint 6: Signal Aggregation

### TASK-010: Corroboration detector and signal aggregator
- **Status**: Done (2026-04-17)
- **Agent**: data-pipeline
- **Complexity**: Medium
- **Depends on**: TASK-007
- **Estimated Effort**: M (2-4 hours)
- **Context**: Corroboration ("if 2+ credible persons have similar posts on the same day") was explicitly named by the user as a distinct signal amplifier, not just a score boost. It gets a visible "CORROBORATED" tag in the email — it is a qualitative shift, not just a multiplier.
- **Description**: Implement `scoring/corroboration.py` with `CorroborationDetector` and `scoring/aggregator.py` with `SignalAggregator`. The detector groups signals by (ticker, direction, date) and applies the corroboration multiplier. The aggregator ranks by final score and returns the top N.
- **Acceptance Criteria**:
  - [x] `CorroborationDetector.detect(signals: list[Signal]) -> list[Signal]` sets `corroboration_count` and `corroboration_bonus` on each signal
  - [x] Signals with 2+ distinct investors (same ticker, same direction, same date): `corroboration_count >= 2`, `corroboration_bonus = settings.corroboration_multiplier` (default 1.5)
  - [x] `final_score = composite_score * corroboration_bonus`
  - [x] `corroboration_bonus` is read from `scoring_weights` or `settings`, not hardcoded
  - [x] `SignalAggregator.rank(signals: list[Signal], top_n: int) -> list[Signal]` returns signals sorted by `final_score` descending, deduplicated by ticker (highest score per ticker kept)
  - [x] Unit test: 3 investors posting LONG FNMA on same day → all three have `corroboration_count=3`
  - [x] Unit test: 1 investor LONG FNMA + 1 investor SHORT FNMA → no corroboration (directions differ)
  - [x] Unit test: same investor posts FNMA twice → still `corroboration_count=1` (distinct investors only)
  - [x] Unit test: top_n=10 with 15 signals → returns 10 highest-scored, correctly ranked
- **Notes**: Store corroboration data in `signals.corroboration_count` and `signals.corroboration_bonus` in DB — this is needed for the evening scorecard and future analysis.

---

## Sprint 7: Email Generation and Delivery

### TASK-011: Email provider interface and Resend implementation
- **Status**: Done (2026-04-17)
- **Agent**: data-pipeline
- **Complexity**: Low
- **Depends on**: TASK-001
- **Estimated Effort**: S (< 2 hours)
- **Context**: Email delivery is abstracted behind `EmailProvider` ABC so that swapping Resend to SendGrid or SES at Phase 2 is a single-file change. The Resend free tier (3,000/month) is sufficient for PoC.
- **Description**: Implement `email/base.py` with `EmailProvider` ABC. Implement `email/resend_provider.py` with `ResendEmailProvider`. Create `EMAIL_REGISTRY`.
- **Acceptance Criteria**:
  - [x] `EmailProvider` ABC defines `send(to: str, subject: str, html_body: str, text_body: str) -> str` (returns message_id)
  - [x] `ResendEmailProvider` reads `RESEND_API_KEY` from settings
  - [x] `ResendEmailProvider.send()` calls `resend.Emails.send()` with both `html` and `text` fields populated
  - [x] On send failure: retry once after 30 seconds, then raise `EmailDeliveryError` (do not retry further — avoid duplicate emails)
  - [x] `ResendEmailProvider.send()` logs `provider='resend'`, `status`, `latency_ms` to `api_usage` table
  - [x] `EMAIL_REGISTRY` maps `"resend"` to `ResendEmailProvider`; `SendGridEmailProvider` stub exists
  - [ ] Integration test (manual): send a test email to `settings.recipient_email` and verify receipt
- **Notes**: Sender domain must be verified in Resend dashboard before first use. Add setup instructions to README. Manual integration test deferred — requires verified Resend domain.

---

### TASK-012: Morning watchlist email renderer
- **Status**: Done (2026-04-17)
- **Agent**: data-pipeline
- **Complexity**: Medium
- **Depends on**: TASK-010, TASK-009, TASK-011
- **Estimated Effort**: M (2-4 hours)
- **Context**: The signal card is the atomic UX unit. Every field was chosen deliberately in UX-SPEC.md. Plain-text-first rendering is non-negotiable — mobile at 7 AM is the primary context. The renderer must correctly handle edge cases: no signals, <10 signals, Burry posts that have since been deleted.
- **Description**: Implement `email/renderer.py` for the morning watchlist. Render both HTML and plain-text versions. Implement all edge case states from UX-SPEC.md. Subject line format from UX-SPEC.md conventions section.
- **Acceptance Criteria**:
  - [x] Renders signal cards in the format from UX-SPEC.md wireframe: rank, direction badge, ticker, index tier, poster name, quote fragment (max 2–3 lines), track record badge, signal strength dots (●●●●○), corroboration flag
  - [x] Track record badge shows `"Track record: building..."` when `investor_profiles.total_calls < 5`
  - [x] Track record shows `"{X}/{N} ({pct}%)"` when `total_calls >= 5`
  - [x] Signal strength dots: 5 levels mapped from composite score 0–10 (`●○○○○` to `●●●●●`)
  - [x] Corroboration shown as `"CORROBORATED — N posters"` when `corroboration_count >= 2`
  - [x] No-signals email renders the "No Signals Overnight" template from UX-SPEC.md
  - [x] Subject line follows the convention: `Influence Monitor — {N} Signals Today [{Mon DD}] | Top: {TICKER} ({DIR}, {BARS})`
  - [x] Plain-text version is complete and readable without HTML rendering (no information loss)
  - [x] No CSS dependency for any required information — Unicode circles render as plain text fallback
  - [x] Quote fragment uses stored post text from DB (never a live API call) — Burry deletion protection
  - [x] SHORT signals display direction badge explicitly; SHORT stocks that drop are correctly labeled as HIT on scorecard (SHORT direction badge rendered in morning email; HIT/MISS labeling deferred to TASK-013 scorecard)
  - [x] Unit tests: render with 10 signals (normal), 0 signals (no-signal email), 3 signals (fewer-than-10 email), one post with deleted text (graceful handling)
- **Notes**: Email template files in `email/templates/`. The renderer reads from DB (new `get_morning_watchlist` repo method), not from in-memory objects, so it can be run independently for testing. HTML body wraps the plain-text body in `<pre>` with minimal inline styles — no load-bearing CSS. User-controlled content is HTML-escaped.

---

### TASK-013: Evening scorecard email renderer
- **Status**: Done (2026-04-17)
- **Agent**: data-pipeline
- **Complexity**: Medium
- **Depends on**: TASK-012
- **Estimated Effort**: M (2-4 hours)
- **Context**: The evening scorecard is both the daily feedback loop and the commercial signal instrument. The running track record panel in the footer must persist correctly from the first trading day. SHORT signal HIT/MISS logic (negative return = HIT for short) is a quiet source of bugs — must be explicit.
- **Description**: Implement the evening scorecard renderer in `email/renderer.py`. Performance table, running track record stats footer, edge case handling for halted stocks and no watchlist days.
- **Acceptance Criteria**:
  - [x] Performance table ranks signals by `return_pct` descending (after SHORT correction: for SHORT signals, negate `return_pct` for ranking purposes so the "best" SHORT is most negative)
  - [x] Each row shows: rank (by performance), ticker, direction, open-to-close return, morning rank, HIT/MISS label
  - [x] SHORT signals with negative `return_pct`: label `"✓ HIT  (short = gain)"`
  - [x] SHORT signals with positive `return_pct`: label `"✗ MISS  (short went up)"`
  - [x] Running track record footer: total signals scored, directional hit rate, avg gain on correct, avg loss on incorrect, corroborated signal accuracy, top performer this month
  - [x] Track record age caveat shown when trading days < 20
  - [x] Halted/price-missing stocks flagged as `"HALTED — no price data"` and excluded from hit rate
  - [x] No-watchlist scorecard (quiet night) renders the appropriate message from UX-SPEC.md
  - [x] Subject line: `Scorecard [{Mon DD}] — {X}/{N} correct | Best: {TICKER} {±%} (was #{rank})`
  - [x] Plain-text version complete and correct
  - [x] Unit tests: all-hits day, all-misses day, mixed day, day with halted stock, quiet-night scorecard
- **Notes**: `EveningScorecardRenderer` added to `email/renderer.py`. New repo methods: `get_evening_scorecard_signals`, `get_running_stats`, `get_trading_days_scored`, `get_first_scored_date`, `get_top_performer_month`. Trading-days count sourced from scored signals (not `daily_summaries`) since TASK-014 not yet built. Separator between hits and misses uses `"─ " * 27` pattern.

---

## Sprint 8: Scorecard Engine and Historical Accuracy

### TASK-014: Scorecard engine (returns, HIT/MISS, accuracy tracking)
- **Status**: Done (2026-04-17)
- **Agent**: data-pipeline
- **Complexity**: Medium
- **Depends on**: TASK-008, TASK-002
- **Estimated Effort**: M (2-4 hours)
- **Context**: The scorecard engine is the core of the track record commercial asset. It must correctly handle SHORT signal HIT logic, update per-investor rolling accuracy, and produce the daily summary row that feeds the track record panel. All updates must be idempotent (safe to re-run if evening pipeline retries).
- **Description**: Implement `scorecard/scorecard_engine.py` with `ScorecardEngine`. Fetches close prices, computes returns, updates HIT/MISS, updates investor rolling accuracy, writes daily summary.
- **Acceptance Criteria**:
  - [x] `ScorecardEngine.run_evening(signal_date: date)` is idempotent — skips signals where `close_price IS NOT NULL`; `upsert_daily_summary` updates existing row
  - [x] `return_pct` computed as `(close_price - open_price) / open_price * 100`; stored with 4 decimal places
  - [x] `is_hit` set correctly for LONG and SHORT; `NULL` when price data unavailable
  - [x] Market context fields populated: `high_price`, `low_price`, `volume`, `avg_volume_30d`, `volume_ratio`
  - [x] Regime context fields populated: `sp500_return_pct` (^GSPC), `vix_at_signal` (^VIX), `sector_return_pct` (sector ETF via `_SECTOR_ETF` mapping)
  - [x] Stock context fields populated: `market_cap_at_signal`, `sector`, `industry` (yfinance ticker info)
  - [x] `investor_profiles.rolling_accuracy_30d` updated via `compute_investor_rolling_accuracy(30d)`
  - [x] `investor_profiles.total_calls` and `total_hits` updated via `get_investor_lifetime_stats`
  - [x] `daily_summaries` row upserted with `summary_date`, `signals_surfaced`, `daily_hit_rate`, `pipeline_status`
  - [x] On price fetch failure: `update_signal_prices(signal_id)` called with no kwargs (NULLs); counted as error, excluded from hit rate
  - [x] Unit tests: LONG HIT, LONG MISS, SHORT HIT, SHORT MISS, NULL open_price skipped, fetch failure, idempotency, daily_hit_rate, one investor update per investor
- **Notes**: `prev_close_price` not populated in this task (requires a prior-day close fetch — deferred to pipeline orchestrator TASK-015). Sector ETF map covers all GICS sectors.

---

## Sprint 9: Pipeline Orchestration and Scheduling

### TASK-015: Pipeline orchestrator (morning and evening entry points)
- **Status**: Done (2026-04-17)
- **Agent**: data-pipeline
- **Complexity**: High
- **Depends on**: TASK-003, TASK-005, TASK-006, TASK-007, TASK-010, TASK-012, TASK-013, TASK-014
- **Estimated Effort**: L (4-8 hours)
- **Context**: The orchestrator is the system's main entry point. It wires together all components in the correct order and handles all failure modes from TDD.md Section 6. Pipeline failures must never produce partial or misleading output — fail loudly with an operational notification email rather than sending a silent partial watchlist.
- **Description**: Implement `pipeline.py` with `PipelineOrchestrator`. Two public methods: `run_morning(run_date: date)` and `run_evening(run_date: date)`. Implement `HolidayCalendar` for market holiday detection. Wire all components. Implement operational failure notification email.
- **Acceptance Criteria**:
  - [ ] `run_morning()` executes in order: fetch posts → extract tickers → score posts → detect corroboration → rank signals → resolve index membership → render email → send email → write `daily_summaries` row
  - [ ] `run_evening()` executes in order: fetch close prices → compute returns → update accuracy → render scorecard → send email → update `daily_summaries`
  - [ ] `HolidayCalendar.is_trading_day(date) -> bool` returns `False` for weekends and US market holidays (NYSE calendar); no email sent on non-trading days
  - [ ] On `IngestorError` (< 13 accounts fetched): send operational failure email, do NOT send morning watchlist, write failed `daily_summaries` row
  - [ ] On any unhandled exception in `run_morning`: send operational failure email with exception type, message, and component; do NOT send partial watchlist
  - [ ] Open price fetch (9:31 AM) is a separate `run_open_prices(run_date: date)` method called by a separate GitHub Actions job
  - [ ] `python -m influence_monitor.pipeline morning` and `python -m influence_monitor.pipeline evening` are the CLI entry points
  - [ ] Dry-run mode: `python -m influence_monitor.pipeline morning --dry-run` renders email to stdout without sending or writing to DB
  - [ ] End-to-end test (manual): dry-run morning pipeline against live twikit data for 3 accounts and verify output
- **Notes**: Operational failure notification goes to `settings.recipient_email` with subject prefix `[Influence Monitor] Pipeline FAILED`.

---

### TASK-016: GitHub Actions scheduling workflows
- **Status**: Not Started
- **Agent**: data-pipeline
- **Complexity**: Low
- **Depends on**: TASK-015
- **Estimated Effort**: S (< 2 hours)
- **Context**: GitHub Actions is the scheduler. Estimated usage is 105 min/month vs. 2,000 min free limit — no cost concern. Database persistence across runs requires a hosted SQLite solution (Turso free tier) or artifact management.
- **Description**: Create `.github/workflows/morning_pipeline.yml` and `.github/workflows/evening_pipeline.yml`. Configure all required secrets. Set up database persistence (Turso free tier preferred over artifact-based).
- **Acceptance Criteria**:
  - [ ] Morning workflow triggers at cron `0 11 * * 1-5` (7:00 AM ET = 11:00 UTC)
  - [ ] Open price workflow triggers at cron `31 13 * * 1-5` (9:31 AM ET = 13:31 UTC)
  - [ ] Evening price fetch triggers at cron `5 20 * * 1-5` (4:05 PM ET = 20:05 UTC)
  - [ ] Evening send triggers at cron `30 21 * * 1-5` (5:30 PM ET = 21:30 UTC)
  - [ ] All workflows install dependencies via `pip install -r requirements.txt`
  - [ ] All workflows run `python -m spacy download en_core_web_sm` before pipeline execution
  - [ ] All secrets referenced as `${{ secrets.VARIABLE_NAME }}` — no secrets hardcoded in workflow files
  - [ ] GitHub repository secrets documented in README setup instructions: `ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `TWITTER_USERNAME`, `TWITTER_EMAIL`, `TWITTER_PASSWORD`, `DATABASE_URL`, `RECIPIENT_EMAIL`
  - [ ] Workflows include `continue-on-error: false` so failures are visible in Actions UI
  - [ ] Manual trigger (`workflow_dispatch`) available on all workflows for ad-hoc testing
- **Notes**: Turso free tier provides 8GB storage and 1B row reads/month — well within PoC needs. Alternatively, store SQLite file as workflow artifact with retention of 90 days. Document chosen approach in README.

---

## Sprint 10: Historical Accuracy and Testing

### TASK-017: Historical accuracy tracking and multi-horizon return backfill
- **Status**: Not Started
- **Agent**: data-pipeline
- **Complexity**: Low
- **Depends on**: TASK-014
- **Estimated Effort**: S (< 2 hours)
- **Context**: `signals.return_5d`, `signals.return_10d`, and `signals.return_30d` are in the schema from day one as forward-compatible columns. A nightly backfill job populates them for signals old enough to have the data. These columns support future ML model training, the API tier, and leaderboard features without schema migration.
- **Description**: Implement a `backfill_returns` method in `ScorecardEngine` that, for each signal older than 5/10/30 trading days with a NULL `return_5d`/`return_10d`/`return_30d`, fetches the close price on the Nth trading day after `signal_date` and computes the return.
- **Acceptance Criteria**:
  - [ ] `backfill_returns(as_of_date: date)` finds all signals where `return_5d IS NULL` and `signal_date <= as_of_date - 5 trading days`
  - [ ] Fetches close price for each ticker on `signal_date + 5 trading days` using `YFinanceClient`
  - [ ] Computes `return_5d = (close_5d - open_price) / open_price * 100`; stores in `signals.return_5d`
  - [ ] Same logic for `return_10d` (10 trading days) and `return_30d` (30 trading days)
  - [ ] Backfill is idempotent — safe to run multiple times without changing already-set values
  - [ ] Added to the evening pipeline (runs after scorecard computation)
  - [ ] Unit tests: signal from 6 days ago with NULL `return_5d` gets populated; signal from 3 days ago remains NULL; signal from 31 days ago with NULL `return_30d` gets populated
- **Notes**: Weekend and holiday counting uses `HolidayCalendar.trading_days_after(date, n)` helper method.

---

### TASK-018: End-to-end integration test and sample data fixtures
- **Status**: Not Started
- **Agent**: test-validator
- **Complexity**: Medium
- **Depends on**: TASK-015, TASK-016
- **Estimated Effort**: M (2-4 hours)
- **Context**: The integration test validates that the full morning and evening pipeline can run end-to-end with realistic fixtures without requiring live API credentials. This is the quality gate before marking the PoC as operational.
- **Description**: Create `tests/fixtures/sample_posts.json` with 10 realistic sample posts covering: high-conviction LONG (FNMA-style), high-conviction SHORT, neutral post, Burry-style deleted post, corroboration scenario (2 investors, same ticker). Implement end-to-end test using mock twikit and real Claude/yfinance (or all mocked for CI).
- **Acceptance Criteria**:
  - [ ] `tests/fixtures/sample_posts.json` contains 10 sample posts with realistic text, engagement metrics, and author handles
  - [ ] `pytest tests/` runs without requiring real API credentials (all external calls mocked)
  - [ ] Morning pipeline integration test: 10 sample posts → extract tickers → score → rank → render email → verify email content contains expected top ticker
  - [ ] Corroboration test: 2 posts about same LONG ticker → morning email shows "CORROBORATED" tag
  - [ ] Evening scorecard test: morning signals + injected price data → correct HIT/MISS → correct running stats
  - [ ] No-signal test: 0 qualifying posts → "no signals overnight" email rendered correctly
  - [ ] Test coverage on `extraction/`, `scoring/`, `scorecard/`, `email/` modules >= 80%
  - [ ] `pytest --cov=influence_monitor tests/` passes with >= 80% coverage on targeted modules
- **Notes**: Use `unittest.mock.patch` or pytest fixtures for mocking twikit, Claude, yfinance, and Resend. Store test DB in `:memory:` SQLite.

---

## Sprint 11: Documentation and Deployment

### TASK-019: README and setup documentation
- **Status**: Not Started
- **Agent**: content-writer
- **Complexity**: Low
- **Depends on**: TASK-018
- **Estimated Effort**: S (< 2 hours)
- **Context**: The README is the entry point for future setup (including Phase 2 onboarding). It must include the "Built with Claude Code" attribution required by CLAUDE.md and complete setup instructions including the twikit cookie setup procedure (which requires a one-time manual step).
- **Description**: Write `projects/influence-post-monitoring/README.md` with complete setup guide, architecture overview, configuration reference, and operational runbook.
- **Acceptance Criteria**:
  - [ ] README begins with project description followed immediately by `> Built with [Claude Code](https://claude.ai/code)`
  - [ ] Setup section covers: clone, venv creation, `pip install -r requirements.txt`, `python -m spacy download en_core_web_sm`, `.env` configuration from `.env.example`
  - [ ] twikit authentication setup: one-time `python -m influence_monitor.pipeline auth` step to generate `twitter_cookies.json`
  - [ ] Resend domain verification step documented
  - [ ] GitHub Actions secrets list with description of each
  - [ ] Database initialization: `python -m influence_monitor.db.repository --init`
  - [ ] Dry-run instructions: `python -m influence_monitor.pipeline morning --dry-run`
  - [ ] Architecture overview: 2-paragraph summary of the pipeline components
  - [ ] Known limitations section: twikit ToS, yfinance staleness risk, Hindenburg account status
  - [ ] Phase 2 migration notes: twikit → official API, SQLite → PostgreSQL swap instructions
- **Notes**: No marketing copy. No emojis. Plain, technical documentation.

---

### TASK-020: Final security review and pre-deployment checklist
- **Status**: Not Started
- **Agent**: architect
- **Complexity**: Low
- **Depends on**: TASK-019
- **Estimated Effort**: S (< 2 hours)
- **Context**: Security review before first live run. The twikit credentials and Twitter cookie file are particularly sensitive — equivalent to a Twitter account password. Any accidental commit of these would require immediate credential rotation.
- **Description**: Conduct security review against CLAUDE.md Security Rules and TDD.md Section 5. Verify `.gitignore` completeness, secret usage patterns, external input validation, and rate limiting compliance. Produce a checklist with pass/fail for each item.
- **Acceptance Criteria**:
  - [ ] `git grep -r "ANTHROPIC_API_KEY\|RESEND_API_KEY\|TWITTER_PASSWORD" -- '*.py' '*.json' '*.yaml'` returns no hardcoded secrets
  - [ ] `data/twitter_cookies.json` confirmed absent from git history and in `.gitignore`
  - [ ] `data/signals.db` confirmed absent from git history and in `.gitignore`
  - [ ] All external API responses validated through Pydantic models before use (Claude) or explicit field access with defaults (twikit)
  - [ ] Ticker whitelist validation confirmed active in `TickerExtractor` (arbitrary strings cannot reach scoring pipeline)
  - [ ] yfinance freshness assertion confirmed active in `YFinanceClient`
  - [ ] No `print()` statements in production code — `logging` module used throughout
  - [ ] `.env.example` contains no real values — all placeholders
  - [ ] GitHub Actions workflow files reference secrets via `${{ secrets.* }}` only
  - [ ] Rate limiting: twikit usage confirmed at <= 20 posts × 17 accounts × 2 runs/day = 680 requests/day
  - [ ] Review sign-off: architect approves for first live run
- **Notes**: This task gates the first live pipeline run. Do not run against real accounts until this task passes.

---

## Completed Tasks Log

<!-- Move completed tasks here with completion date in format: Done (YYYY-MM-DD) -->
