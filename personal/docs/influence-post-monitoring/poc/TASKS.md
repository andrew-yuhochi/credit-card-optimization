# Task Breakdown — Influence Post Monitoring

> **Status**: Active
> **Phase**: PoC
> **Last Updated**: 2026-04-19
> **Depends on**: PRD.md, TDD.md, DATA-SOURCES.md (all drafted 2026-04-18)
> **Supersedes**: 2026-04-17 TASKS.md (email-based 20-task PoC — fully rebuilt)

## Progress Summary

| Status | Count |
|--------|-------|
| Done | 17 |
| In Progress | 0 |
| To Do | 12 |
| Blocked | 0 |

---

## Milestone 1: First WhatsApp Alert End-to-End (hardcoded data)

> **Goal**: Prove the WhatsApp delivery path works before any pipeline is built. User receives a formatted morning alert on their phone using hardcoded sample signals. Validates the Twilio setup, the message format, and the always-send + disclaimer footer rules.
> **Acceptance Criteria**: (1) User's phone receives a formatted morning alert (Act Now + Watch List, conviction score, warning emojis, poster strategy, views/hr + posted time). (2) User's phone receives the empty-state alert (`--demo-empty`) and approves the no-signals message. User approves both formats before building the real pipeline.
> **Demo Gallery**: `docs/influence-post-monitoring/poc/demos/milestone-1/`
> **Review Checkpoint**: User reviews both the full alert and the empty-state alert on device and approves before Milestone 2 begins. Run `/milestone-complete influence-post-monitoring`.
> **Status**: To Do

### PRE-001: Twilio account + WhatsApp Sandbox activation (human prerequisite)
- **Status**: Done (2026-04-18)
- **Agent**: none — manual user process
- **Complexity**: Low
- **Depends on**: None
- **Context**: Twilio WhatsApp Sandbox requires manual activation — a human must create the Twilio trial account and register their personal phone as a sandbox participant by sending a `join <code>` message. This cannot be automated and must complete before any code-level messaging work is possible.
- **Description**: User creates a Twilio trial account at console.twilio.com, navigates to Messaging → Try it out → Send a WhatsApp message, and from their personal WhatsApp sends the `join <sandbox-code>` message to `+1 (415) 523-8886`. User captures the Account SID, Auth Token, and Sandbox sender number into a local `.env`. User also obtains a CallMeBot API key by sending the CallMeBot bootstrap message from the same phone.
- **Acceptance Criteria**:
  - [ ] Twilio trial account created; ~$15 credit visible in console
  - [ ] User's phone number registered as a WhatsApp sandbox participant (confirmation message received)
  - [ ] `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_SANDBOX_NUMBER` (`whatsapp:+14155238886`), `RECIPIENT_PHONE_E164` captured in local notes
  - [ ] CallMeBot API key obtained and captured as `CALLMEBOT_API_KEY`
- **Demo Artifact**: Screenshot of the sandbox confirmation message on the user's WhatsApp saved to `docs/influence-post-monitoring/poc/demos/milestone-1/PRE-001-sandbox-join.png` (phone number redacted).
- **Notes**: This task is a pre-implementation human prerequisite. No code is written. The user reports back with the credentials captured when done; TASK-001 cannot begin until PRE-001 is complete.

### TASK-001: Project scaffolding + config + MessageDelivery interface
- **Status**: Done (2026-04-18)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: PRE-001
- **Context**: Establishes the directory layout in TDD §8, the `Settings` class (pydantic-settings), the `MessageDelivery` ABC at `delivery/base.py`, and both concrete implementations (`TwilioWhatsAppDelivery`, `CallMeBotDelivery`). All four exist together because the delivery path is the Milestone 1 deliverable — the user must see a real WhatsApp message.
- **Description**: Create `projects/influence-post-monitoring/` with full directory structure per TDD §8. Write `requirements.txt` with pinned versions (twikit 2.3.3, yfinance, finvizfinance 1.3.0, pandas_market_calendars, spacy 3.8.13, anthropic, pydantic v2, pydantic-settings, twilio, httpx, libsql-client, APScheduler 3.11.2, pytest, pytest-cov). Create `.env.example` with all env vars from TDD §7. Create `.gitignore` (includes `.env`, `data/twitter_cookies.json`, `data/*.db`, `logs/`, `venv/`). Implement `influence_monitor/config.py` with `Settings`. Implement `delivery/base.py` with `MessageDelivery` ABC. Implement `delivery/twilio_whatsapp.py` with `TwilioWhatsAppDelivery.send(text) -> bool` + retry logic. Implement `delivery/callmebot.py` with `CallMeBotDelivery.send(text) -> bool` as the fallback. Implement `delivery/registry.py` with `DELIVERY_REGISTRY`.
- **Acceptance Criteria**:
  - [ ] Directory structure matches TDD §8 (all `__init__.py` present)
  - [ ] `requirements.txt` pins all dependencies from TDD §3
  - [ ] `venv && pip install -r requirements.txt && python -m spacy download en_core_web_sm` all succeed
  - [ ] `.env.example` contains every env var from TDD §7 with placeholder values
  - [ ] `MessageDelivery` ABC defines `send(text: str) -> bool`
  - [ ] `TwilioWhatsAppDelivery` reads `TWILIO_*` env vars and the `RECIPIENT_PHONE_E164`; calls `Client(sid, token).messages.create(from_=sandbox_number, to=recipient, body=text)`
  - [ ] On Twilio 4xx/5xx or exception: returns `False`, logs ERROR, does not raise
  - [ ] `CallMeBotDelivery.send()` issues an HTTP GET to the CallMeBot endpoint with URL-encoded body + API key
  - [ ] `DELIVERY_REGISTRY` maps `"twilio"` → `TwilioWhatsAppDelivery`, `"callmebot"` → `CallMeBotDelivery`
  - [ ] Unit tests (mocked HTTP): Twilio success returns True, Twilio 4xx returns False, CallMeBot success returns True
  - [ ] Integration test (requires `.env`): `python -m influence_monitor.delivery.twilio_whatsapp --test-message "hello"` sends a real message and returns True
- **Demo Artifact**: Screenshot of the `"hello"` test message delivered to the user's WhatsApp, saved to `docs/influence-post-monitoring/poc/demos/milestone-1/TASK-001-test-message.png`.
- **Notes**: Per CLAUDE.md GitHub Rule #2, this is the first task in the PoC — create the `andrew-yuhochi/influence-post-monitoring` public GitHub repo at first task completion, before pushing. README includes the `> Built with [Claude Code](https://claude.ai/code)` line.

### TASK-002: Morning alert renderer + end-to-end hardcoded demo
- **Status**: Done (2026-04-18)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-001
- **Context**: The morning alert format is the keystone UX — it determines whether the user will read and trust the system. Rendering from hardcoded fixture data first (no twikit, no Claude, no DB) lets the user validate the format in a real WhatsApp message before any ingestion pipeline is built. This is the Milestone 1 user-observable deliverable.
- **Description**: Implement `rendering/morning_renderer.py` with a `render_morning(signals: list[RenderedSignal], collection_time: datetime, accounts_count: int) -> str` function per PRD §6.16 and UX-SPEC.md + the UX-SPEC override decisions in PRD §8. Signal blocks include `DIRECTION $TICKER (Market Cap Class)`, conviction dots (`●●●●○` mapped from 0–10 score), poster handle, inline corroboration/conflict tags (`⚠️ Direction changed`, `⚠️ Conflicted — opposing view exists`, `CORROBORATED — N posters`), quote fragment ≤150 chars. Empty states: no Act Now → `"No posts above threshold overnight."`; no signals anywhere → explicit no-signals message. Footer: `_This is information about public posts, not investment advice. Do your own research._`. Implement CLI `python -m influence_monitor.rendering.morning_renderer --demo` that builds a hardcoded fixture (FNMA + NFLX + AAPL Act Now, NOVA + RIVN Watch List) and sends via `TwilioWhatsAppDelivery`.
- **Acceptance Criteria**:
  - [ ] `render_morning` produces output matching the UX-SPEC.md Full morning alert mock structure
  - [ ] Act Now section caps at 5 signals, ordered by conviction score descending
  - [ ] Watch List section caps at 5 signals, ordered by views/hour descending
  - [ ] Conviction dots: 5 filled for ≥9.0 score, 4 for ≥7.0, 3 for ≥5.0, 2 for ≥3.0, 1 for ≥1.0, 0 otherwise
  - [ ] `CORROBORATED — N posters` rendered when `corroboration_count >= 2`
  - [ ] `⚠️ Direction changed` rendered when `direction_flip=True`
  - [ ] `⚠️ Conflicted — opposing view exists` rendered when `conflict_group='opposing_exists'`
  - [ ] Empty-Act-Now message rendered correctly
  - [ ] Full no-signals message rendered correctly (empty both sections)
  - [ ] Disclaimer footer present on every message
  - [ ] Output stays under 4,000 chars even with 10 max-length signals
  - [ ] Unit tests cover all five rendering scenarios (full, Act Now empty, all empty, direction flip, conflict)
  - [ ] `python -m influence_monitor.rendering.morning_renderer --demo` sends a real WhatsApp message with hardcoded fixture and returns success
- **Demo Artifact**: Screenshot of the hardcoded morning alert delivered to WhatsApp, saved to `docs/influence-post-monitoring/poc/demos/milestone-1/TASK-002-morning-alert.png`. Phone number and Twilio sandbox number redacted.
- **Notes**: Output format must be plain text with WhatsApp markdown-lite only. No HTML. No markdown tables. Unicode symbols render natively.

---

## Milestone 2: Ingestion + Scoring Pipeline (Act Now tier only)

> **Goal**: Pipeline fetches posts from 3 real accounts (Ackman, Burry, Chanos — activist + deleter + short), extracts tickers, scores with Claude Haiku, applies the five-factor model, and classifies signals into Act Now tier. Evening outcome computation comes in Milestone 3.
> **Acceptance Criteria**: `python -m influence_monitor.pipeline morning --accounts 3` runs end-to-end without crashes; signals appear in the Turso DB; WhatsApp morning alert arrives with real data (even if limited); user can query `signals` table and verify all five factor scores are populated.
> **Demo Gallery**: `docs/influence-post-monitoring/poc/demos/milestone-2/`
> **Review Checkpoint**: User reviews at least 2 days of real morning alerts + inspects the DB to confirm the raw data capture. Approves before Milestone 3 begins.
> **Depends on**: Milestone 1 review passed
> **Status**: To Do

### TASK-003: Turso-hosted SQLite schema + repository layer
- **Status**: Done (2026-04-19)
- **Agent**: architect (phase review), data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-001
- **Context**: Schema from TDD §2.4 with multi-tenant `user_id`+`tenant_id` on every table. The `signals` table is the commercial asset — every sub-score column (F1–F5 plus outcome columns) must exist from day one, even those filled by later tasks. Turso free tier is the cloud host; `libsql-client` is a drop-in replacement for sqlite3. Local `data/signals.db` fallback when `TURSO_URL` is unset.
- **Description**: Create `db/schema.sql` with all CREATE TABLE from TDD §2.4 (tenants, users, accounts, posts, engagement_snapshots, retweeters, price_cache, scoring_config, signals, messages_sent, daily_summaries, api_usage). Implement `db/repository.py` with `SignalRepository` — connection management (Turso or local SQLite via `libsql_client`), and all read/write methods referenced by later tasks. Implement `--init` CLI flag that creates schema, seeds the default tenant, the default user (from `.env` `RECIPIENT_PHONE_E164`), all 45 accounts from `config/accounts.json`, and `scoring_config` from `config/scoring_config_seed.json`. Also create `tests/fixtures/sample_signals.json` (10 pre-scored, pre-classified signal records covering all key rendering scenarios) and `tests/fixtures/sample_outcomes.json` (same records with outcome data populated). These fixture files are the basis for `--use-fixtures` mode in the orchestrators (TASK-010b, TASK-013) — allowing deliverables to be tested without real overnight signals.
- **Acceptance Criteria**:
  - [ ] `schema.sql` creates all 11 tables from TDD §2.4
  - [ ] `accounts`, `posts`, `signals`, `messages_sent`, `daily_summaries`, `users`, `scoring_config` all have `user_id` (where applicable) AND `tenant_id` columns defaulting to 1
  - [ ] `accounts` table includes `consecutive_failures INTEGER NOT NULL DEFAULT 0` and `last_failure_at DATETIME` columns (for `AccountRegistry` debounce in TASK-004)
  - [ ] `posts (source_type, external_id)` has UNIQUE constraint
  - [ ] `signals` includes every factor column (`score_credibility`, `score_virality_abs`, `score_virality_vel`, `score_consensus`, `score_amplifier`, `liquidity_modifier`) AND outcome columns (`prev_close`, `today_open`, `today_close`, `overnight_return`, `tradeable_return`, `spy_return`, `stock_20d_vol`, `excess_vol_score`, `price_data_source`)
  - [ ] `signals` includes `direction_flip`, `conflict_group`, `penalty_applied`, `final_score`, `tier`, `morning_rank`
  - [ ] `libsql_client` is used for Turso; falls back to `sqlite3` on local `data/signals.db` when `TURSO_URL` is unset
  - [ ] `python -m influence_monitor.db.repository --init` seeds DB without error
  - [ ] After seeding: `SELECT COUNT(*) FROM accounts WHERE status='primary'` = 30, `status='backup'` = 15, `SELECT COUNT(*) FROM scoring_config` = 17 (5 weights + 4 virality/penalty thresholds + 1 vol lookback + 2 registry ops + 5 liquidity modifiers)
  - [ ] `tests/fixtures/sample_signals.json` created with 10 pre-classified signal records covering: FNMA LONG ACT_NOW (corroborated 2 posters), NFLX SHORT ACT_NOW, AAPL LONG ACT_NOW, NOVA LONG WATCH, RIVN SHORT WATCH, direction-flip ACT_NOW (with `direction_flip=True`), multi-poster conflicted TSLA (with `conflict_group='opposing_exists'`), neutral/unscored, high-virality Watch-only, low-conviction ACT_NOW
  - [ ] `tests/fixtures/sample_outcomes.json` contains the same 10 records plus `overnight_return`, `tradeable_return`, `spy_return`, `stock_20d_vol`, `excess_vol_score` populated for all ACT_NOW and WATCH signals (covering positive, negative, and SHORT-annotated cases)
  - [ ] `scoring_config` seed values match DATA-SOURCES.md §Virality threshold + operational config starting values exactly: `direction_flip_penalty=0.0`, `vol_lookback_days=20`, `max_consecutive_failures=3`, `retry_rest_minutes=30`, `watch_velocity_floor=1000`, `virality_views_threshold=50000`, `virality_reposts_threshold=500`, liquidity modifiers per TDD §2.4 (0.8/0.9/1.0/1.15/1.3)
  - [ ] Repository exposes methods: `insert_post`, `insert_engagement_snapshot`, `insert_retweeter`, `upsert_account`, `update_account_failure` (increment `consecutive_failures` + set `last_failure_at`), `reset_account_failures` (set to 0), `rename_account_handle` (update handle in place), `insert_signal`, `update_signal_outcome`, `get_signals_for_date`, `get_scoring_config`, `log_message_sent`, `log_api_usage`, `upsert_daily_summary`
- **Demo Artifact**: Output of `sqlite3 data/signals.db '.schema signals'` + `SELECT COUNT(*) FROM accounts GROUP BY status;` + `SELECT key, value FROM scoring_config ORDER BY key;` saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-003-schema.txt`.
- **Notes**: `libsql_client` is the Turso-provided SQLite-compatible client. Seed `config/accounts.json` from the DATA-SOURCES.md §Monitored Accounts table (all 45 entries, including B14 Josh Wolfe and B15 Mark Yusko). `config/scoring_config_seed.json` includes all 17 scoring keys — weights, virality thresholds, direction flip penalty (seeded to 0.0), vol lookback (seeded to 20), registry ops (max_consecutive_failures, retry_rest_minutes), and liquidity modifiers — and must be identical to the DATA-SOURCES.md table.

### TASK-004: SocialMediaSource ABC + twikit ingestion + AccountRegistry
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: High
- **Depends on**: TASK-003
- **Context**: twikit is the highest-risk PoC component (ToS violation, suspension, X patches). The `SocialMediaSource` ABC is established first so the MVP swap to the official API is one file. The `AccountRegistry` is the account validation and backup promotion component called at pipeline startup — it keeps exactly 30 primaries active. Critically, it debounces transient failures (`consecutive_failures` counter) AND tries to resolve renamed handles BEFORE promoting a backup — account disappearances in practice are often renames, not deletions. The throwaway X account credentials are sensitive; `data/twitter_cookies.json` is gitignored.
- **Description**: Implement `ingestion/base.py` (`SocialMediaSource` ABC + `RawPost` + `Retweeter` dataclasses; add `search_user(display_name) -> list[User]` to the ABC to support handle rediscovery). Implement `ingestion/twitter_twikit.py` (`TwitterTwikitSource` with login, cookie persistence, `fetch_recent_posts`, `fetch_retweeters`, `search_user`). Implement `ingestion/account_registry.py` per TDD §2.1 — the full handle-resolution + consecutive-failure sequence. Implement `ingestion/registry.py` (`SOURCE_REGISTRY`). Create stub `ingestion/twitter_official.py` for MVP swap. Add `engagement_snapshots` INSERT on every post fetch.
- **Acceptance Criteria**:
  - [ ] `SocialMediaSource` ABC defines `fetch_recent_posts`, `fetch_retweeters`, `search_user`, `source_type`
  - [ ] `RawPost` includes all fields from TDD §2.1 (engagement metrics, `raw_payload`, `posted_at`, `fetched_at`)
  - [ ] `TwitterTwikitSource` authenticates via `client.login()` on first run, saves cookies; subsequent runs use `load_cookies()`
  - [ ] `fetch_recent_posts` filters to posts with `posted_at >= since` and respects `max_count`
  - [ ] Full tweet JSON stored in `RawPost.raw_payload`
  - [ ] `fetch_retweeters` returns up to 100 Retweeter objects from `client.get_retweeters(tweet_id)`
  - [ ] `search_user(display_name)` returns candidate User objects for handle rediscovery (twikit `client.search_user` or equivalent)
  - [ ] Per-account fetch failure logs WARNING, increments `accounts.consecutive_failures`, updates `last_failure_at`, and continues; does not raise
  - [ ] Successful fetch resets `accounts.consecutive_failures = 0`
  - [ ] `AccountRegistry.validate_and_promote()` executes the 5-step handle-resolution sequence per TDD §2.1 when `consecutive_failures >= scoring_config.max_consecutive_failures` (default 3): (a) check handle reachability, (b) if unreachable, search by `display_name`, (c) if a credible rename match is found, UPDATE `accounts.handle` with old→new handle logged at INFO — **NO backup promotion**, (d) only if name search yields no match → mark `status='inactive'` + promote next backup by `backup_rank` + log WARNING
  - [ ] "Credible rename match" heuristic is documented in code: exact `display_name` match + verified badge + follower count within 50% of last-known value
  - [ ] Retry debounce: registry respects `scoring_config.retry_rest_minutes` (default 30) between successive attempts on a failing account (tracked via `last_failure_at`)
  - [ ] After validation, `SELECT COUNT(*) FROM accounts WHERE status='primary'` = 30 unless all backups exhausted (log ERROR in that case)
  - [ ] `engagement_snapshots` row inserted on every post fetch
  - [ ] `data/twitter_cookies.json` listed in `.gitignore` and not committed
  - [ ] Unit tests (mocked twikit): post fetch, per-account transient failure → increment counter (no promotion), repeated failures → name search → rename path (handle updated, no promotion), repeated failures → name search → no match → backup promotion, all-backups-exhausted ERROR path, successful fetch resets counter
  - [ ] Integration test (requires throwaway X account): fetch 3 posts from @BillAckman successfully; verify `consecutive_failures=0` after success
- **Demo Artifact**: Console log + DB query output showing 3 posts fetched from @BillAckman with all fields populated, saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-004-ingestion.txt`.
- **Notes**: Test against 3 accounts only in initial runs (Ackman, Burry, Chanos) to minimize suspension risk during dev. Scale to 30 after Milestone 3 validation. The handle-resolution sequence is implemented even in the 3-account run so it can be unit-tested; a synthetic "renamed" fixture exercises the path without needing an actual renamed account.

### TASK-005: Trading calendar + post collection window
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Low
- **Depends on**: TASK-001
- **Context**: `pandas_market_calendars` is authoritative for every date decision in the project (prev_close, collection window, `is_trading_day`, forward-N-trading-days). No ad-hoc `datetime.weekday()` arithmetic anywhere — doing it naively would break on US holidays. This is used by the ingestion window filter (TASK-004), the outcome engine (Milestone 3), and the scorecard aggregator (Milestone 4).
- **Description**: Implement `market_data/trading_calendar.py` with `TradingCalendar` class wrapping `pandas_market_calendars.get_calendar("NYSE")`. Methods: `is_trading_day(date) -> bool`, `previous_trading_day(date) -> date`, `next_trading_day(date) -> date`, `trading_days_after(date, n) -> date`, `trading_days_between(start, end) -> list[date]`, `collection_window(send_time_et) -> tuple[datetime, datetime]` (returns previous-close datetime to send-time datetime).
- **Acceptance Criteria**:
  - [ ] Uses `pandas_market_calendars.get_calendar("NYSE")`
  - [ ] `is_trading_day(date(2026, 7, 4))` returns `False` (Independence Day)
  - [ ] `is_trading_day(date(2026, 4, 18))` returns `False` (Saturday)
  - [ ] `is_trading_day(date(2026, 4, 3))` returns `False` (Good Friday 2026)
  - [ ] `previous_trading_day(date(2026, 4, 20))` returns `2026-04-17` (Monday → prior Thursday, Fri was Good Friday)
  - [ ] `collection_window(datetime(2026, 4, 21, 9, 0, tz=ET))` returns `(prev_close_datetime, send_datetime)` with prev_close = 2026-04-20 16:00 ET
  - [ ] `trading_days_after(date(2026, 1, 1), 5)` correctly skips weekends and MLK Day
  - [ ] Unit tests: weekend crossing, Good Friday, Memorial Day, Thanksgiving, Christmas, day-after-Thanksgiving early close (not handled at PoC — close = 16:00 always; documented)
- **Demo Artifact**: Python REPL output showing 10 representative date queries (weekends, holidays, prev_close at month-boundaries), saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-005-calendar.txt`.
- **Notes**: Early-close trading days (day after Thanksgiving, Christmas Eve) are treated as 16:00 ET close at PoC — the small data error is acceptable; documented in the class docstring.

### TASK-006: Ticker extraction (3-layer + whitelist)
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-001
- **Context**: Three-layer pipeline (cashtag → uppercase + false-positive filter → spaCy NER → Yahoo Finance resolver → whitelist) per TDD §2.2. The whitelist is the final gate — extractions outside the S&P 500 + Russell 3000 + supplement (FNMA/FMCC) are dropped. spaCy NER uses `en_core_web_sm` v3.8.13 which misses some names (e.g., "GameStop") — Layer 1 and 2 catch most explicit mentions.
- **Description**: Implement `extraction/equity_whitelist.py` (`SymbolWhitelist.load()` reads or downloads S&P 500 + Russell 3000 + supplement; `contains(ticker) -> bool`). Implement `extraction/ticker_extractor.py` (`TickerExtractor` with all three layers + Yahoo Finance ORG-name resolver; returns `ExtractedTicker` Pydantic models with `HIGH`/`MEDIUM`/`LOW` confidence). Whitelist-validate every extraction. Deduplicate across layers. Load spaCy model once at init.
- **Acceptance Criteria**:
  - [ ] `SymbolWhitelist` loads S&P 500 from `data/sp500.csv` (or downloads), Russell 3000 from `data/russell3000.csv`, supplement from `data/supplement.txt`
  - [ ] `contains("AAPL")` = True; `contains("CEO")` = False; `contains("FNMA")` = True (via supplement)
  - [ ] Layer 1 extracts `FNMA` from `"$FNMA is massively underpriced"` with confidence HIGH
  - [ ] Layer 2 extracts `TSLA` from `"TSLA could 10x"` with confidence MEDIUM
  - [ ] Layer 2 does NOT extract: CEO, IPO, ETF, GDP, CPI, FED, SEC, NYSE, USD
  - [ ] Layer 3 extracts `AAPL` from `"Apple is a strong buy"` (via Yahoo Finance resolver) with confidence LOW
  - [ ] Layer 3 resolves `"Fannie Mae"` → `FNMA`
  - [ ] All extractions whitelist-validated before return
  - [ ] Unit tests cover: cashtag, uppercase, NER, false-positive filter, whitelist gating, dedup across layers
  - [ ] spaCy model loaded once at `TickerExtractor.__init__`
- **Demo Artifact**: Unit test output + a script that runs extraction on 5 real Ackman posts and prints extracted tickers + confidence, saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-006-extraction.txt`.
- **Notes**: Cache the Yahoo Finance name→ticker lookups in a per-process dict to avoid repeated API calls within a single run.

### TASK-007: Claude Haiku client + directional scoring
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-001
- **Context**: Claude Haiku is the most expensive external dep (~$0.25/month) but produces the conviction-level and direction classification. Pydantic validation of every response is mandatory — parse failures return a zero-score sentinel rather than crashing. System prompt lives in `config/prompts/scoring_prompt.txt` (DATA-SOURCES.md §Source 5), not in code. **Important:** `llm_client.py` (`LLMClient` ABC + `PostScore` Pydantic model) already exists from a prior cut. `claude_client.py` also exists with ~158 lines but contains a wiring bug — it calls `await self._repo.log_api_usage(...)` against the current **synchronous** repository. This task rewrites `claude_client.py` to call the sync method directly (no asyncio) and verifies prompt loading against the current prompt file.
- **Description**: The existing `scoring/claude_client.py` must be rewritten (not created from scratch). Remove all `async`/`await` — `SignalRepository` is synchronous. Retain the existing prompt-loading, Pydantic validation, sentinel logic, and retry logic; only fix the sync/async mismatch and align the `PostScore` model with current TDD §2.3. Verify `scoring/llm_client.py` already exposes `LLMClient` ABC + `PostScore` Pydantic model with fields (`tickers`, `direction`, `conviction_level`, `key_claim`, `argument_quality`, `time_horizon`, `market_moving_potential`, `rationale`) and `zero_sentinel()` classmethod — if schema has drifted from DATA-SOURCES.md §Source 5, update it. Rewrite `scoring/claude_client.py` (`ClaudeHaikuClient`) to: read prompt once from `config/prompts/scoring_prompt.txt`, call `anthropic.Anthropic(api_key=settings.anthropic_api_key).messages.create(...)`, Pydantic-validate response, log to `api_usage` via the **synchronous** `repo.log_api_usage(...)` call (no asyncio.get_event_loop), retry once on `anthropic.APIError` after 5s, return `PostScore.zero_sentinel()` on parse/validation fail. Remove the existing `async`/`await` wrapping around `_log_usage`.
- **Implementation Checklist**:
  - **Schema**: `api_usage` row with columns `provider`, `endpoint`, `input_tokens`, `output_tokens`, `latency_ms`, `status`, `error_message` — all already exist in `schema.sql` (lines 227-237). No additions.
  - **Wire**: rewrite existing file at `scoring/claude_client.py` — do not create new. `ClaudeHaikuClient` is instantiated inside the TASK-010b `PipelineOrchestrator.__init__` and its `score_post(post.text, post.author_handle)` is called from the morning pipeline step 5. No wiring in this task — TASK-010b does the wiring.
  - **Call site**: N/A (this task produces the class; callers appear in TASK-008 tests and TASK-010b orchestrator).
  - **Imports affected**: any caller using async interface must be updated — no caller may `await client.score_post(...)` or `await client._log_usage(...)`. `scoring/claude_client.py` currently imports `DatabaseRepository` (line 19) — OK, `DatabaseRepository` is aliased to `SignalRepository` in `db/repository.py` line 619. Keep either name but prefer `SignalRepository` for consistency with TASK-003 and TASK-004. If renamed, update imports in: `scoring/claude_client.py`, any test file that imports `ClaudeHaikuClient` — currently only `tests/test_llm_client.py` (verify).
  - **Runtime files**: `config/prompts/scoring_prompt.txt` — **exists** (16 lines). The existing file at that path must remain and match the schema in DATA-SOURCES.md §Source 5 — verify the JSON schema description in the prompt still asks for the 8 `PostScore` fields; if not, update the prompt before writing tests.
- **Acceptance Criteria**:
  - [ ] `LLMClient` ABC defines `score_post(post_text, author_handle) -> PostScore` and `model_version() -> str`
  - [ ] `PostScore` validates `tickers`, `direction`, `conviction_level` (0–5), `key_claim`, `argument_quality`, `time_horizon`, `market_moving_potential`, `rationale`
  - [ ] System prompt read from `config/prompts/scoring_prompt.txt` at `ClaudeHaikuClient.__init__` time, not inline, not per-call
  - [ ] Model: `claude-haiku-4-5-20251001` (or the latest Haiku release as pinned in the constant at the top of `claude_client.py`)
  - [ ] On Pydantic fail: logs raw response WARNING (truncated to first 500 chars), returns `PostScore.zero_sentinel()` (`conviction_level=0`, `direction="AMBIGUOUS"`, empty `tickers`)
  - [ ] On `anthropic.APIError`: retries once after 5s; `zero_sentinel()` on second fail
  - [ ] Every call logged to `api_usage` with `provider='anthropic'`, `endpoint=<model_name>`, `latency_ms`, `input_tokens`, `output_tokens`, `status` — via **synchronous** `repo.log_api_usage(...)` (no `asyncio.get_event_loop`, no `await`)
  - [ ] No `async`/`await` anywhere in `claude_client.py` — all calls to `SignalRepository` are synchronous
  - [ ] `claude_client.py` has zero references to `asyncio`, `await`, or `loop.create_task` (sync-only)
  - [ ] Unit tests cover: valid JSON response → PostScore parsed; markdown-fenced JSON → unwrapped + parsed; malformed JSON → zero_sentinel + WARNING; APIError → retry → success on 2nd; APIError twice → zero_sentinel; every path hits `repo.log_api_usage` exactly once (asserted with mock)
  - [ ] Integration test (requires `ANTHROPIC_API_KEY`): score 5 real posts; all return valid `PostScore`; zero parse errors; 5 rows in `api_usage` with `status='ok'`
- **Demo Artifact**: Output of scoring 5 fixture posts (including the FNMA Ackman example) with PostScore serialized as JSON, saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-007-scoring.json`.
- **Notes**: Store `llm_model_version`, raw response, token counts on every `signals` row for MVP audit and re-scoring (the `signals` table already has `llm_model_version`, `llm_raw_response`, `llm_input_tokens`, `llm_output_tokens` columns — these are populated by TASK-008, not this task).

### TASK-008: Five-factor scoring engine + conflict resolver + signal classifier
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: High
- **Depends on**: TASK-003, TASK-006, TASK-007
- **Context**: The scoring engine combines Claude's output with the credibility seed (F1), virality (F2a/F2b), consensus (F3), amplifier (F4 — only for Act Now, see TASK-009), and liquidity (F5). All weights read from `scoring_config` table (not hardcoded). Conflict resolver handles same-poster repeats/flips and multi-poster mixed-direction splits per PRD §6.12. Classifier assigns ACT_NOW / WATCH / UNSCORED using virality thresholds. **Important:** the current `scoring/scoring_engine.py` (187 lines) is a LEGACY 5-component engine (credibility/conviction/argument/engagement/historical) from the old email-based PoC — it must be fully rewritten. Legacy `scoring/corroboration.py` (102 lines) and `scoring/aggregator.py` (58 lines) implement a different consensus model and must be DELETED in this task (their roles are subsumed by the new F3 consensus factor + ConflictResolver). The stubs `scoring/conflict_resolver.py`, `scoring/classifier.py`, `scoring/amplifier.py` are all 1-line placeholders awaiting implementation.
- **Description**: Before implementing the new engine, delete legacy files: `influence_monitor/scoring/scoring_engine.py` (old 5-component model), `influence_monitor/scoring/corroboration.py`, `influence_monitor/scoring/aggregator.py`. These are replaced entirely by `ScoringEngine` + `ConflictResolver`. Rewrite `scoring/scoring_engine.py` — new `ScoringEngine` class that accepts weights from `scoring_config` (5 keys: `weight_credibility`, `weight_virality_abs`, `weight_virality_vel`, `weight_consensus`, `weight_amplifier`), computes F1..F5 and composite `conviction_score`, persists all sub-scores. Implement `scoring/conflict_resolver.py` (same-poster highest-virality selection for same-direction repeats; most-recent + `direction_flip=True` + penalty for same-poster flips; per-direction signal emission with `conflict_group='opposing_exists'` for 3+ posters mixed direction). Implement `scoring/classifier.py` (thresholds from `scoring_config`: `virality_views_threshold`, `virality_reposts_threshold`, `watch_velocity_floor`; `classify(post) -> 'ACT_NOW' | 'WATCH' | 'UNSCORED'`). Persist all factor scores individually on the `signals` row via `repo.insert_signal(**kwargs)`.
- **Implementation Checklist**:
  - **Schema**: `signals` row will populate these columns (all EXIST in `schema.sql` lines 129-187): `score_credibility`, `score_virality_abs`, `score_virality_vel`, `score_consensus`, `score_amplifier`, `liquidity_modifier`, `conviction_score`, `direction_flip`, `conflict_group`, `penalty_applied`, `final_score`, `tier`, `morning_rank`, `llm_model_version`, `llm_raw_response`, `llm_input_tokens`, `llm_output_tokens`, `extraction_confidence`, `direction`, `conviction_level`, `argument_quality`, `time_horizon`, `market_moving_potential`, `key_claim`, `rationale`, `market_cap_class`, `engagement_views`, `engagement_reposts`, `views_per_hour`, `ticker`. All present. No schema changes.
  - **Wire**: `ScoringEngine` is instantiated in TASK-010b `PipelineOrchestrator.__init__` and called at morning pipeline step 6 (build signals, F1/F2/F3/F5). `ConflictResolver` called at step 7. `Classifier` called at step 8. F4 (amplifier) is wired by TASK-009. Every factor-scoring call must round-trip through `repo.insert_signal(**kwargs)` with ALL factor columns populated as kwargs (the repo method is generic `**kwargs`, so unknown columns silently go into the INSERT — do NOT rely on that; pass only known columns).
  - **Call site**: The old `SignalAggregator.rank()` and `CorroborationDetector.detect_and_tag()` are called from `pipeline.py` lines 460-461 — those callers will be removed when TASK-010a reduces `pipeline.py` to a stub (and TASK-010b writes the new orchestrator). No intermediate shim is needed.
  - **Imports affected**: grep for imports of `corroboration`, `aggregator`, `ScoringEngine` (old) across the codebase and remove/update them; `pipeline.py` imports these — note it will be fully replaced in TASK-010b so stale imports there are acceptable until then. **Renames/deletions**: `SignalAggregator`, `CorroborationDetector`, legacy `Signal` dataclass, legacy `ScoredSignal` dataclass. Files that currently import these and MUST be updated: `influence_monitor/pipeline.py` (lines 50-52 — will be replaced in TASK-010b; stale imports there are acceptable until TASK-010b), `tests/test_corroboration.py` (DELETE this test file — no replacement needed; ConflictResolver has its own test), `tests/test_scoring_engine.py` (REWRITE — asserts change entirely for F1..F5 model). Also update `scoring/claude_client.py` no-op (doesn't import these). Verify via `grep -r "CorroborationDetector\|SignalAggregator"` before finalizing.
  - **Runtime files**: Reads `scoring_config` from DB (seeded by TASK-003 — already Done). No file I/O beyond the DB.
- **Acceptance Criteria**:
  - [ ] Legacy files deleted: `scoring/corroboration.py`, `scoring/aggregator.py`; `scoring/scoring_engine.py` replaced (not amended) with new F1–F5 implementation
  - [ ] `scoring/corroboration.py` and `scoring/aggregator.py` **deleted**; no remaining imports of `CorroborationDetector`, `SignalAggregator`, or legacy `Signal`/`ScoredSignal` dataclasses anywhere in `influence_monitor/` or `tests/` (except files being rewritten)
  - [ ] `ScoringEngine` loads weights from `scoring_config` table via `repo.get_scoring_config(tenant_id=1)` (synchronous); keys: `weight_credibility`, `weight_virality_abs`, `weight_virality_vel`, `weight_consensus`, `weight_amplifier`
  - [ ] All five sub-scores (F1 credibility, F2a virality_abs, F3 consensus, F4 amplifier, F5 liquidity) computed; the non-applicable tier's optional factors are left as `None` on the persisted row (e.g., F2b virality_vel is NULL for ACT_NOW; F4 amplifier is NULL until TASK-009 populates it)
  - [ ] F2b (virality_vel) computed only for WATCH tier; F4 (amplifier) populated only for ACT_NOW after TASK-009
  - [ ] `conviction_level < 2` or `direction in ["NEUTRAL", "AMBIGUOUS"]` → `conviction_score = 0`, `tier = 'UNSCORED'`, all F-scores = 0
  - [ ] `ConflictResolver`: same-poster repeats → highest-virality retained, others dropped
  - [ ] `ConflictResolver`: same-poster flip → `direction_flip=True` (always set), `penalty_applied = scoring_config.direction_flip_penalty` (default 0.0 — tag-only at PoC, non-zero values immediately activate penalty deduction with no code change), most-recent retained
  - [ ] Test case: with `direction_flip_penalty=0.0` (default), a flipped signal renders the `⚠️ Direction changed` tag but its `final_score == conviction_score` (no deduction)
  - [ ] Test case: with `direction_flip_penalty=2.0` (simulated DB update), the same flipped signal produces `final_score = conviction_score - 2.0`
  - [ ] `ConflictResolver`: 3+ posters on same ticker mixed direction → one signal per direction group, `conflict_group='opposing_exists'` on each
  - [ ] `classify` returns ACT_NOW when `views >= virality_views_threshold` OR `reposts >= virality_reposts_threshold`
  - [ ] `classify` returns WATCH when below threshold but `views_per_hour >= watch_velocity_floor`
  - [ ] Unit tests: single post scoring, same-poster repeat, same-poster flip, 3-poster mixed, threshold crossings, all weights DB-driven
- **Demo Artifact**: Output of scoring 6 fixture posts (including one flip scenario and one 3-poster mixed scenario) showing all factor scores, tier assignment, and conflict handling, saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-008-scoring.txt`.
- **Notes**: ScoringEngine must be pure — receives `PostScore` + `RawPost` + account credibility, does not call external services. Testable in isolation. Legacy tests `test_corroboration.py` and the existing `test_scoring_engine.py` assertion body must be removed or rewritten; the test-validator pass should surface any stale asserts.

### TASK-009: Amplifier fetcher + market-cap resolver
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-004, TASK-008
- **Context**: Amplifier quality (F4) is fetched only for ACT_NOW candidates (~5–10/day) to respect twikit rate limits. Each retweeter is persisted in the `retweeters` table at fetch time (amplifier regression dataset for MVP). Cross-reference with the `accounts` table — any monitored account in the retweeter list = strong signal. Market-cap resolver uses `finvizfinance` with a weekly cache in the `price_cache` table. **Important:** both `scoring/amplifier.py` and `market_data/market_cap_resolver.py` are currently 1-line stubs awaiting implementation. The legacy `market_data/index_resolver.py` (208 lines) is NOT a substitute for `MarketCapResolver` — it's a separate S&P/Russell membership tier classifier from the old design; leave it alone in this task but it will need to be deleted or deprecated by TASK-010a.
- **Description**: Implement `scoring/amplifier.py` (`AmplifierFetcher.fetch_and_score(post, source)` → calls `source.fetch_retweeters`, persists all to `retweeters` with `is_monitored` set by cross-ref against `accounts`; applies the TDD §2.3 formula: `min(10, monitored_count*3 + high_follower_count*1.5 + mid_follower_count*0.5)` with tiers from `scoring_config`). Implement `market_data/market_cap_resolver.py` (`MarketCapResolver.resolve(ticker)` → `price_cache` hit within 7 days returns cached; else finvizfinance call + insert; on failure returns `"Micro"`). Map cap class to liquidity modifier (0.8× Mega / 0.9× Large / 1.0× Mid / 1.15× Small / 1.3× Micro) from `scoring_config`. Also add two new methods to `SignalRepository`: `get_cached_market_cap(ticker) -> float | None` and `upsert_price_cache(ticker, market_cap, fetched_at)`. Add two missing `scoring_config` seed rows: `amplifier_high_follower_tier` (value: `100000`) and `amplifier_mid_follower_tier` (value: `10000`). Update the seed count assertion in `tests/test_repository.py::test_scoring_config_seed_count` from 17 to 19.
- **Implementation Checklist**:
  - **Schema**: `retweeters` table has columns `post_id`, `retweeter_external_id`, `retweeter_handle`, `followers_count`, `is_verified`, `is_monitored`, `fetched_at` (schema.sql lines 85-97) — all present. `price_cache` table has `ticker`, `market_cap_b`, `market_cap_class`, `sector`, `industry`, `last_updated` (lines 100-108) — all present. No schema changes.
  - **Wire**: `AmplifierFetcher` is called from TASK-010b `PipelineOrchestrator.run_morning()` step 9 — **only** for signals classified as `ACT_NOW` by TASK-008 Classifier. `MarketCapResolver` is called from TASK-010b orchestrator step 6 (ScoringEngine F5 computation) — for EVERY signal, not just ACT_NOW, because liquidity_modifier applies to the composite conviction score regardless of tier. Both wirings live in TASK-010b's orchestrator; this task exposes the classes only.
  - **Call site**: N/A (no callers yet — TASK-010b adds them).
  - **Imports affected**: `AmplifierFetcher` consumes `SocialMediaSource` from `ingestion/base.py` (already defines `fetch_retweeters`) and calls `repo.insert_retweeter(...)` (already implemented in `repository.py` line 404). `MarketCapResolver` takes the repo in its constructor and calls a new method `repo.get_cached_market_cap(ticker, max_age_days=7) -> dict | None` and `repo.upsert_price_cache(ticker, market_cap_b, market_cap_class, sector, industry)` — **these two methods do NOT yet exist in `repository.py`** and must be added as part of this task (NEW repo methods).
  - **Runtime files**: `scoring_config` seed rows `liq_mega`, `liq_large`, `liq_mid`, `liq_small`, `liq_micro` already present (seeded by TASK-003 — verified against `config/scoring_config_seed.json`). Follower-tier thresholds `amplifier_high_follower_tier` and `amplifier_mid_follower_tier` are NOT in the current 17 seeded keys — the TDD-aligned default thresholds (high=100000, mid=10000) must be either (a) hardcoded with a comment pointing to where to add to seed later, or (b) added to `config/scoring_config_seed.json` as 2 new keys and the seeded-count assertion in TASK-003's test updated from 17 → 19. **Decision: add to seed.** Update `config/scoring_config_seed.json` + the count check in `tests/test_repository.py::test_scoring_config_seed_count` accordingly.
- **Acceptance Criteria**:
  - [ ] `AmplifierFetcher.fetch_and_score(post, source)` fetches up to ~100 retweeters via `source.fetch_retweeters`
  - [ ] All retweeters persisted to `retweeters` table via `repo.insert_retweeter(...)` with `is_monitored` flag set by cross-ref against `accounts.external_id`
  - [ ] Amplifier score in [0, 10] per TDD §2.3 formula
  - [ ] Called only for ACT_NOW signals (gated in `PipelineOrchestrator`, enforced in tests)
  - [ ] `MarketCapResolver.resolve` returns one of: Mega, Large, Mid, Small, Micro
  - [ ] 7-day cache via new `repo.get_cached_market_cap` / `repo.upsert_price_cache` methods in `price_cache`; cache miss calls finvizfinance
  - [ ] finvizfinance failure returns `"Micro"` + WARNING log (does not raise)
  - [ ] Market-cap string parsing: `"3911.50B"` → 3_911_500 (millions); `"498.22M"` → 498; `""` → None → Micro
  - [ ] Liquidity modifier applied to conviction_score per class (read from `scoring_config.liq_mega` etc.)
  - [ ] Unit tests: amplifier formula with 0/1/3 monitored matches; cap-class parsing edge cases; cache hit/miss; finvizfinance failure fallback
  - [ ] `config/scoring_config_seed.json` grows by 2 keys (`amplifier_high_follower_tier=100000`, `amplifier_mid_follower_tier=10000`); `tests/test_repository.py::test_scoring_config_seed_count` updated from 17 → 19
- **Demo Artifact**: DB dump showing `retweeters` rows from a real Act Now Ackman post + the computed `score_amplifier`, saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-009-amplifier.txt`.
- **Notes**: Follower tier thresholds (high 100K+, mid 10K-50K) are in `scoring_config` and configurable.

### TASK-010a: Legacy pipeline cleanup (delete email/calendar/scorecard/index_resolver)
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-007, TASK-008, TASK-009
- **Context**: Before the new orchestrator can be written (TASK-010b), the legacy code it would collide with must be removed. The current `influence_monitor/pipeline.py` (603 lines) is a fully async email-based orchestrator that imports from `influence_monitor.email.*`, `influence_monitor.calendar`, `CorroborationDetector`, `SignalAggregator`, `IndexMembershipResolver`, and `ScorecardEngine`. Leaving this file in place while TASK-010b is written risks collisions on common module paths and confused imports. This task performs the deletion pass AND reduces `pipeline.py` to a thin, non-functional stub (a single `main()` that raises `NotImplementedError("TASK-010b")`) so that `pytest` collection still runs and the repo imports still resolve. This is a pure-removal task — no new pipeline behavior is introduced here.
- **Description**: DELETE `influence_monitor/email/` directory (base.py, sendgrid_provider.py, resend_provider.py, registry.py, renderer.py, and any others). DELETE `influence_monitor/calendar.py` (the correct calendar is `market_data/trading_calendar.py`). DELETE `influence_monitor/scorecard/` directory (legacy; the new scorecard lives in TASK-012's `outcome/scorecard_aggregator.py`). DELETE `influence_monitor/market_data/index_resolver.py` (legacy; not in current TDD). DELETE legacy test files that target the removed modules: `tests/test_email_provider.py`, `tests/test_index_resolver.py`, `tests/test_scorecard_engine.py`. REWRITE `influence_monitor/pipeline.py` to a stub — remove all legacy imports and classes, leave a single `main()` that logs `"pipeline orchestrator not yet implemented — see TASK-010b"` and raises `NotImplementedError`. Mark legacy test files `tests/test_pipeline.py` and `tests/test_integration.py` with a module-level `pytest.skip(allow_module_level=True)` and a `# TASK-010b: rewrite` comment; do NOT delete these yet — TASK-010b will rewrite them against the new orchestrator. After this task, `pytest` must collect and run cleanly with the two skipped modules and no import errors anywhere in the package.
- **Implementation Checklist**:
  - **Schema**: No schema changes.
  - **Wire**: No new wiring. The stub `pipeline.py` exposes only `main()` that raises `NotImplementedError`.
  - **Call site**: No callers in PoC code (GitHub Actions wiring is TASK-014, after TASK-010b).
  - **Imports affected**: **Deletions**: `influence_monitor.email.*`, `influence_monitor.calendar.HolidayCalendar/_easter/_nyse_holidays/_observe`, `influence_monitor.scorecard.*`, `influence_monitor.market_data.index_resolver.IndexMembershipResolver`. **Test files DELETED**: `tests/test_email_provider.py`, `tests/test_index_resolver.py`, `tests/test_scorecard_engine.py`. **Test files SKIPPED (not deleted, rewritten in TASK-010b)**: `tests/test_pipeline.py`, `tests/test_integration.py`. Verify with `grep -rn "influence_monitor.email\|influence_monitor.calendar\|influence_monitor.scorecard\|IndexMembershipResolver\|HolidayCalendar"` — only matches allowed after this task are inside the two skipped test modules (which TASK-010b will rewrite) and the TASKS.md/PRD.md/TDD.md docs.
  - **Runtime files**: None written, none read at runtime (stub only).
- **Acceptance Criteria**:
  - [ ] `influence_monitor/email/` directory removed
  - [ ] `influence_monitor/calendar.py` removed
  - [ ] `influence_monitor/scorecard/` directory removed
  - [ ] `influence_monitor/market_data/index_resolver.py` removed
  - [ ] `tests/test_email_provider.py`, `tests/test_index_resolver.py`, `tests/test_scorecard_engine.py` deleted
  - [ ] `tests/test_pipeline.py` and `tests/test_integration.py` marked `pytest.skip(allow_module_level=True)` with `# TASK-010b: rewrite` comment
  - [ ] `influence_monitor/pipeline.py` reduced to a stub `main()` that raises `NotImplementedError("TASK-010b")`
  - [ ] `pytest` collects and runs cleanly: no `ImportError`, no `ModuleNotFoundError`, two collected-but-skipped modules
  - [ ] `grep -rn "from influence_monitor.email\|from influence_monitor.calendar\|from influence_monitor.scorecard\|IndexMembershipResolver\|HolidayCalendar\|CorroborationDetector\|SignalAggregator" influence_monitor/` returns no matches (production code is clean of legacy references)
- **Demo Artifact**: `git log --stat` output showing the deletions + a clean `pytest -q` transcript with the two expected skips, saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-010a-cleanup.txt`.
- **Notes**: This is a surgical deletion task — no new behavior. It exists as its own task so that TASK-010b begins against a clean codebase and so the deletion diff is reviewable independently of the new-orchestrator diff (which is large). If test-validator surfaces incidental test breakage caused by removed symbols being imported from unexpected places, fix those imports in this task; do not defer to TASK-010b.

### TASK-010b: Morning pipeline orchestrator (new, end-to-end 3-account demo)
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: High
- **Depends on**: TASK-002, TASK-004, TASK-005, TASK-006, TASK-007, TASK-008, TASK-009, TASK-010a
- **Context**: With the legacy code removed by TASK-010a, this task wires all Milestone 2 components into a new synchronous `PipelineOrchestrator.run_morning(run_date)`. First end-to-end run is against 3 accounts only (Ackman, Burry, Chanos) to validate the pipeline before scaling to 30. Real-data WhatsApp message replaces the hardcoded Milestone 1 fixture. Always-send rule honored: empty-signals message ships even when no signals are found. **Important:** the orchestrator is synchronous from the outside; the `source.fetch_recent_posts` twikit calls are async internally and must be wrapped with `asyncio.run()` at the ingestion boundary only — the orchestrator API stays sync.
- **Description**: WRITE `influence_monitor/pipeline.py` from scratch (replacing the stub left by TASK-010a) — `PipelineOrchestrator` with `run_morning(run_date: date, account_limit: int | None = None, dry_run: bool = False, use_fixtures: bool = False)`. Steps: (1) validate accounts via `AccountRegistry`, (2) `source.fetch_recent_posts` for each active account in collection window via `TradingCalendar`, (3) insert posts + engagement_snapshots, (4) extract tickers per post, (5) Claude-score each, (6) build signals via ScoringEngine (F1/F2a/F2b/F3/F5 at this stage), (7) apply ConflictResolver, (8) classify into ACT_NOW/WATCH/UNSCORED, (9) for ACT_NOW: AmplifierFetcher (F4), (10) persist signals, (11) render morning alert top-5 ACT_NOW + top-5 WATCH, (12) send via `TwilioWhatsAppDelivery` with CallMeBot fallback, (13) write `daily_summaries` and `messages_sent` rows. `account_limit=3` for the initial milestone demo; full run later via TASK-011 defaults change. CLI: `python -m influence_monitor.pipeline morning [--account-limit N] [--dry-run] [--use-fixtures]`. `--use-fixtures`: bypasses steps 1–9 entirely (no twikit, no Claude), inserts records from `tests/fixtures/sample_signals.json` directly into the `signals` table with all factor scores pre-populated, then executes steps 10–13 (classify → render → send). REWRITE `tests/test_pipeline.py` and `tests/test_integration.py` (removing the skip markers added in TASK-010a) against the new synchronous orchestrator API.
- **Implementation Checklist**:
  - **Schema**: `posts` (all columns — already present), `engagement_snapshots` (post_id, snapshot_at, view_count, repost_count, reply_count, like_count — present), `signals` (full row including all F1..F5 + outcome NULLs — present), `daily_summaries` (summary_date, run_type, accounts_active, accounts_fetched, posts_fetched, signals_scored, signals_act_now, signals_watch, pipeline_status, error_message, duration_seconds — present), `messages_sent` (kind, delivery, status, body_preview, provider_id, error_message — present). No schema changes.
  - **Wire**: This task IS the wiring. Every component from TASK-002/-004/-005/-006/-007/-008/-009 gets instantiated in `PipelineOrchestrator.__init__` and called in order in `run_morning()`. The CLI entry point is `if __name__ == "__main__": main()` at the bottom of the new `pipeline.py`; `main()` parses `sys.argv`, constructs `Settings()`, `SignalRepository(settings)`, all pipeline components, and invokes `orchestrator.run_morning(...)`. Signal delivery goes through `delivery/registry.py::DELIVERY_REGISTRY["twilio"]` with `delivery/registry.py::DELIVERY_REGISTRY["callmebot"]` as fallback on False return.
  - **Call site**: N/A (top-level orchestrator; no other code calls it in PoC — GitHub Actions will invoke the CLI in TASK-014).
  - **Imports affected**: **Test files rewritten here** (skip markers removed): `tests/test_pipeline.py`, `tests/test_integration.py`. New assertions target the synchronous `PipelineOrchestrator`, fixtured `SignalRepository`, and `DELIVERY_REGISTRY` delivery paths. Verify nothing in the production `influence_monitor/` tree references any deleted module (TASK-010a guarantees this; re-grep here as a safety check before finalizing).
  - **Runtime files**: `tests/fixtures/sample_signals.json` — **exists** (376 lines, 10 pre-scored records; created in TASK-003). `--use-fixtures` mode must read this file and insert records via `repo.insert_signal(**kwargs)` — every JSON field that maps to a `signals` column gets passed as a kwarg. Fields that do not map to columns (e.g., `_comment`, `post_text`, `posted_at`, `account_handle`, `corroboration_count`) must be FILTERED OUT before the insert, with `post_text`/`posted_at`/`account_handle` used instead to first INSERT a row into `posts` (so the signal's `post_id` FK is valid) and to look up the `account_id` by handle. Also requires `.env` with Twilio + CallMeBot credentials; `data/signals.db` or Turso; `config/prompts/scoring_prompt.txt` (read transitively by `ClaudeHaikuClient`).
- **Acceptance Criteria**:
  - [ ] New `pipeline.py` is fully synchronous (no `async def` at module level); any async twikit call is wrapped in `asyncio.run()` at the ingestion call-site only
  - [ ] `run_morning` executes the 13 steps in order; each step logs START/DONE at INFO level
  - [ ] Non-trading-day short-circuit (via `TradingCalendar.is_trading_day`): no fetch, no message, log INFO and exit
  - [ ] Empty-signals day: "no signals" WhatsApp message still ships (always-send rule)
  - [ ] AmplifierFetcher called only for ACT_NOW signals (assert in test via mock call-count)
  - [ ] All signals persisted with F1, F2a/F2b (tier-appropriate), F3, F5 populated; F4 populated only for ACT_NOW
  - [ ] `daily_summaries` row upserted with `pipeline_status`, `accounts_fetched`, `signals_scored`, `signals_act_now`, `signals_watch`, `duration_seconds`
  - [ ] On `AccountRegistry` all-inactive: operational WhatsApp sent, `pipeline_status='failed'`, error logged to `daily_summaries.error_message`
  - [ ] On any unhandled exception: operational WhatsApp sent, traceback logged via `logger.exception`, no partial morning alert delivered
  - [ ] `--dry-run` renders to stdout without sending WhatsApp or writing to `signals`/`messages_sent`/`daily_summaries`
  - [ ] `--account-limit 3` demo: pipeline runs end-to-end against 3 real accounts (Ackman, Burry, Chanos); WhatsApp arrives on user's phone
  - [ ] `--use-fixtures`: reads `tests/fixtures/sample_signals.json`, inserts all required `posts` rows, then `signals` rows with all factor scores set; then runs classification (no-op since tiers are pre-set) → rendering → delivery; sends a real WhatsApp with realistic signal blocks (no twikit or Claude credentials required)
  - [ ] `python -m influence_monitor.pipeline morning --use-fixtures` completes successfully on any day, with or without organic signals
  - [ ] `tests/test_pipeline.py` and `tests/test_integration.py` rewritten: skip markers from TASK-010a removed; full assertions against the new orchestrator pass
  - [ ] No test or production file references `EmailProvider`, `HolidayCalendar`, `ScorecardEngine`, `IndexMembershipResolver`, `CorroborationDetector`, or `SignalAggregator` (grep-verified)
- **Demo Artifact**: Three artifacts: (a) CLI log of the 3-account dry-run saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-010b-dryrun.txt`; (b–d) screenshots of the real WhatsApp morning alert (3 screens) saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-010b-live-1.PNG`, `TASK-010b-live-2.PNG`, `TASK-010b-live-3.PNG`.
- **Notes**: Operational failure messages go to the same recipient phone — the user is both operator and user at PoC. `pipeline.py` is the CLI entry point. Because this task replaces the stub left by TASK-010a with a real orchestrator, the test-validator pass here is the gate for Milestone 2 — a clean `pytest` run with the rewritten `test_pipeline.py` + `test_integration.py` is required before Milestone 3 begins.

### TASK-010c: Conflict block renderer + restore 5-signal cap
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Low
- **Depends on**: TASK-010b
- **Context**: User approved during Milestone 2 deliverable review (2026-04-19). Promoted from BL-004. Two changes: (1) Restore the `[:5]` cap on ACT_NOW display slots that was accidentally removed in a prior fix. (2) When exactly 2 ACT_NOW signals share a ticker with opposing directions (LONG vs SHORT), collapse them into a single conflict block that counts as 1 toward the 5-slot cap. Conflict block header: `📈📉 $TICKER (CapTier)`; each sub-signal shows its score bar and poster handle; post excerpts shown at the bottom in backtick formatting.
- **Description**: In `rendering/morning_renderer.py`: add `_are_opposing()` + `_group_act_now_signals()` helpers; add `_render_conflict_block()` renderer; update `render_morning()` to group signals before sorting/capping (apply `[:5]` to grouped slots). Conflict detection uses `MorningSignal.direction` field values `LONG`/`SHORT` (and `BUY`/`SELL`). Non-conflicted signals retain existing single-block format. WATCH LIST cap unchanged. Add tests in `tests/test_pipeline.py` covering: opposing pair → one conflict block, conflict block counts as 1 slot toward 5-cap, 3+ signals or same-direction pair → not grouped.
- **Acceptance Criteria**:
  - [x] Two ACT_NOW signals for the same ticker with opposing directions → rendered as one conflict block
  - [x] Conflict block counts as 1 toward the 5-slot ACT_NOW display cap
  - [x] Three signals for same ticker (2 same direction + 1 opposing) → rendered as separate slots, not grouped
  - [x] `[:5]` cap restored on sorted ACT_NOW slots
  - [x] WATCH LIST cap and rendering unchanged
  - [x] All existing tests still pass
- **Demo Artifact**: none — renderer fix; correctness visible in `TASK-010b-dryrun.txt` (conflict block format) and 401-test clean run (2026-04-19).

---

## Milestone 3: Evening Outcome + Excess/Vol Score + Scorecard

> **Goal**: After-market run fetches OHLC + SPY context, computes overnight/tradeable returns AND excess/vol score for every Act Now + Watch List signal from the morning. User receives the evening WhatsApp summary with three metrics per stock plus the 30-day per-poster scorecard ranked by average excess/vol.
> **Acceptance Criteria**: `python -m influence_monitor.pipeline evening` runs after close; WhatsApp arrives with per-stock outcome blocks (overnight / tradeable / excess-vol) and the scorecard. User validates the SPY-parenthetical transparency line and the `⚠️ Sample still building` warning behavior.
> **Demo Gallery**: `docs/influence-post-monitoring/poc/demos/milestone-3/`
> **Review Checkpoint**: User reviews at least 2 evening summaries and confirms the three-metric display is readable. Approves before Milestone 4.
> **Depends on**: Milestone 2 review passed
> **Status**: To Do

### TASK-011: Market data client (yfinance + Alpha Vantage fallback) + SPY + configurable stock vol
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-005
- **Context**: yfinance silent-stale-data is the #1 data-quality risk. Freshness assertion on every fetch is mandatory. Alpha Vantage is the fallback with 25 req/day — use sparingly. Also fetches SPY for the excess-return computation and the prior-`vol_lookback_days` vol window for each stock (default 20, configurable via `scoring_config.vol_lookback_days`). **Important:** `market_data/base.py` (43 lines, `MarketDataClient` ABC + `DataFreshnessError` / `DataUnavailableError`), `market_data/yfinance_client.py` (160 lines), and `market_data/alpha_vantage_client.py` (94 lines) already exist. The existing `YFinanceClient` exposes `fetch_open`, `fetch_close`, `fetch_ohlcv`, `fetch_batch_close`, `fetch_with_retry` — but **does NOT have `fetch_stock_vol` or `fetch_spy_return`**. This task ADDS those two methods (plus updates the ABC) without regressing the existing methods.
- **Description**: Update `market_data/base.py` ABC to include `fetch_stock_vol(ticker, target_date, lookback_days)` and `fetch_spy_return(target_date)` as abstract methods. Extend `market_data/yfinance_client.py` with: (a) `fetch_stock_vol(ticker, target_date, lookback_days) -> float | None` that pulls `lookback_days` trading days of history ending at `target_date` via `yf.Ticker(ticker).history(period=...)`, computes daily-return stdev, and returns `None` on unavailability; (b) `fetch_spy_return(target_date) -> float | None` that resolves `prev_trading_day` via the `TradingCalendar` built in TASK-005, fetches SPY close on both days, and returns `(today_close - prev_close) / prev_close`. Extend `market_data/alpha_vantage_client.py` to implement the same two methods (vol via daily time series, spy_return via GLOBAL_QUOTE or TIME_SERIES_DAILY on SPY). The lookback is passed as a parameter — callers read `scoring_config.vol_lookback_days` and pass it in; the client does not hardcode 20.
- **Implementation Checklist**:
  - **Schema**: Reads nothing and writes nothing directly. When fallback fires, `repo.log_api_usage(provider='yfinance_fallback', ...)` inserts an `api_usage` row (columns already exist). No schema changes.
  - **Wire**: `YFinanceClient` + `AlphaVantageClient` are constructed in TASK-010b `PipelineOrchestrator.__init__` and passed to `OutcomeEngine` (TASK-012). `fetch_stock_vol` and `fetch_spy_return` are called from `OutcomeEngine.compute_and_store` in TASK-012, not from anywhere in the morning pipeline.
  - **Call site**: New callers live in TASK-012's `OutcomeEngine`. Existing callers of `fetch_ohlcv`/`fetch_close`/`fetch_batch_close` from the legacy `pipeline.py` will be gone after TASK-010a strips that file to a stub — do not preserve any legacy call shapes for their sake. Verify with `grep -rn "fetch_ohlcv\|fetch_close\|fetch_batch_close"` that only TASK-012 callers remain.
  - **Imports affected**: No class renames. The `MarketDataClient` ABC grows by two abstract methods — all concrete subclasses (`YFinanceClient`, `AlphaVantageClient`) must implement them to avoid instantiation errors. If any test or mock implements the ABC directly (e.g., a `FakeMarketDataClient` in `tests/test_market_data.py`), those mocks must gain stubs for the new methods too. Grep the tests directory for `MarketDataClient`.
  - **Runtime files**: `TradingCalendar` (TASK-005, `market_data/trading_calendar.py`) is used for `previous_trading_day` resolution. No file I/O. Alpha Vantage API key read from `settings.alpha_vantage_api_key` — must be present in `.env.example` (verify — it is as of TASK-001).
- **Acceptance Criteria**:
  - [ ] `MarketDataClient` ABC has `fetch_stock_vol(ticker, target_date, lookback_days)` and `fetch_spy_return(target_date)` as abstract methods; both `YFinanceClient` and `AlphaVantageClient` implement them
  - [ ] Existing `fetch_open`, `fetch_close`, `fetch_ohlcv`, `fetch_batch_close`, `fetch_with_retry` methods remain on `YFinanceClient` and their existing tests continue to pass unchanged
  - [ ] `fetch_stock_vol` takes `lookback_days` as a required parameter (no default of 20 in the client)
  - [ ] `YFinanceClient.fetch_ohlcv` continues to assert `hist.index[-1].date() == target_date`; raises `DataFreshnessError` on stale (no regression)
  - [ ] On `DataFreshnessError`: retry once (60s), then fall back to `AlphaVantageClient`; log `provider='yfinance_fallback'` to `api_usage`
  - [ ] `fetch_stock_vol(ticker, target_date, lookback_days)` returns daily-return stdev over the prior `lookback_days` trading days of the ticker at `target_date`; uses `TradingCalendar.trading_days_between` for date alignment; returns `None` on insufficient data (logged at WARNING)
  - [ ] `fetch_spy_return(target_date)` returns `(today_close - prev_close) / prev_close` for SPY using `TradingCalendar.previous_trading_day`; returns `None` on fetch failure
  - [ ] Batch `fetch_batch_close(tickers, target_date)` remains functional for efficiency
  - [ ] Unit tests: mock yfinance returning today (pass), yesterday (fail + fallback), empty (fail + fallback); stdev computation on known-vol sample for `lookback_days=20` AND a second non-default value (e.g., 10) to confirm the parameter threads through; SPY return on weekend-crossing and Good-Friday-crossing dates
- **Demo Artifact**: CLI output showing `fetch_ohlcv` for AAPL + `fetch_spy_return` + `fetch_stock_vol(lookback_days=20)` for 3 real tickers, saved to `docs/influence-post-monitoring/poc/demos/milestone-3/TASK-011-market-data.txt`.
- **Notes**: Pin yfinance version. Annualize vs. keep daily vol is a modeling choice — we keep daily stdev (matches the daily overnight return numerator; excess/vol is then dimensionally `daily_return / daily_return` which is unitless and interpretable). Documented in the function docstring. The `stock_20d_vol` column name in `signals` is retained for schema stability even if the lookback is retuned; the actual lookback used on any given day is recoverable via `scoring_config.vol_lookback_days` at query time.

### TASK-012: Outcome engine + scorecard aggregator
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-011, TASK-003
- **Context**: Per PRD §6.13–14 and the critical decision updates: overnight_return uses `TradingCalendar.previous_trading_day(today)` for prev_close — handles weekends AND holidays. Excess/vol replaces win-rate entirely: `(stock_return - spy_return) / stock_vol` where the vol lookback window is read from `scoring_config.vol_lookback_days` (default 20). Scorecard aggregator groups by poster (not ticker) and averages excess/vol across the 30-day window. Idempotent for safe re-runs. **Important:** both `outcome/outcome_engine.py` and `outcome/scorecard_aggregator.py` are currently 1-line stubs — this task creates them from scratch. The legacy `scorecard/scorecard_engine.py` (416 lines) implemented a completely different metric scheme (win-rate / sector-relative returns) against the old email design; it will have been DELETED by TASK-010a before this task starts, so there is no legacy code to migrate.
- **Description**: Implement `outcome/outcome_engine.py` (`OutcomeEngine.compute_and_store(signal_date)` — for every signal where `excess_vol_score IS NULL`: read `vol_lookback_days` from `scoring_config`; fetch today_open + today_close via `market_client.fetch_ohlcv`, prev_close via `market_client.fetch_close(ticker, prev_trading_day)` where `prev_trading_day = TradingCalendar.previous_trading_day(signal_date)`, spy_return via `market_client.fetch_spy_return(signal_date)`, stock_vol via `market_client.fetch_stock_vol(ticker, signal_date, lookback_days=vol_lookback_days)`; compute and persist `overnight_return`, `tradeable_return`, `spy_return`, `stock_20d_vol`, `excess_vol_score`, `price_data_source` via `repo.update_signal_outcome(signal_id, ...)` — the column name `stock_20d_vol` is retained for schema stability even when the actual lookback is not 20). Implement `outcome/scorecard_aggregator.py` (`ScorecardAggregator.top_n_posters(as_of, window_days=30, top_n=5)` returns rows of `{handle, avg_excess_vol, n_signals}` sorted desc). `⚠️ Sample still building` is emitted when `trading_days_with_signals < 20`.
- **Implementation Checklist**:
  - **Schema**: Reads `signals` columns `id`, `ticker`, `direction`, `signal_date`, `excess_vol_score` (filter NULL), `account_id`, `tier`. Writes via `repo.update_signal_outcome` which updates `prev_close`, `today_open`, `today_close`, `overnight_return`, `tradeable_return`, `spy_return`, `stock_20d_vol`, `excess_vol_score`, `price_data_source`, `outcome_fetched_at`. All columns already exist in `schema.sql` (lines 168-178). ScorecardAggregator reads `signals` joined on `accounts.handle` — the existing `repo.get_signals_for_date` already JOINs `accounts`. A new repo method `repo.get_signals_for_date_range(start_date, end_date)` must be added to the repository for the 30-day scorecard query (does not currently exist — verified by grep of `repository.py`).
  - **Wire**: `OutcomeEngine` is instantiated in TASK-013 `PipelineOrchestrator.__init__` and called from `run_evening()` as the first substantive step after the non-trading-day short-circuit. `ScorecardAggregator` is called by TASK-013 `run_evening()` after `compute_and_store` completes, feeding the `render_evening` function.
  - **Call site**: N/A (no callers in this task; TASK-013 wires them).
  - **Imports affected**: No renames. `OutcomeEngine.__init__(market_client: MarketDataClient, repo: SignalRepository, trading_calendar: TradingCalendar)`. `ScorecardAggregator.__init__(repo: SignalRepository, trading_calendar: TradingCalendar)`. Both modules import the repo's NEW method `get_signals_for_date_range` — if that method isn't added here, the evening pipeline will fail at runtime.
  - **Runtime files**: None. All inputs come from the DB and the market-data client. `scoring_config.vol_lookback_days` read via `repo.get_scoring_config(tenant_id=1)` (already implemented; returns dict including `vol_lookback_days` seeded to 20.0).
- **Acceptance Criteria**:
  - [ ] `OutcomeEngine.compute_and_store` is idempotent (skips signals with non-null `excess_vol_score`)
  - [ ] `prev_close` resolved via `TradingCalendar.previous_trading_day` — Monday correctly uses Friday close, Tuesday after Good Friday correctly uses Thursday close
  - [ ] `overnight_return`, `tradeable_return`, `spy_return`, `stock_20d_vol`, `excess_vol_score` persisted to `signals` with 6 decimal places (via `round(x, 6)` before insert)
  - [ ] On any price fetch fail: `price_data_source='unavailable'`, outcome columns NULL, signal excluded from scorecard
  - [ ] `SignalRepository.get_signals_for_date_range(start_date, end_date, tenant_id=1)` added to `db/repository.py`; returns joined signal+account rows within the inclusive date range
  - [ ] `ScorecardAggregator.top_n_posters` returns top 5 by avg excess/vol across all scored signals from each poster in window; returns empty list when no signals have `excess_vol_score IS NOT NULL`
  - [ ] Returns `n_signals` count alongside avg (for transparency in "building..." state)
  - [ ] `ScorecardAggregator` exposes `trading_days_with_signals(as_of, window_days=30) -> int` so renderer can emit the `⚠️ Sample still building` warning when `< 20`
  - [ ] Unit tests: LONG + up stock → positive excess_vol; SHORT + up stock → negative excess_vol (correct sign); price fetch fail → NULL + unavailable marker; idempotency (re-run leaves non-null rows untouched); weekend-crossing prev_close; Good-Friday-crossing prev_close; empty-signals → empty scorecard (no crash)
- **Demo Artifact**: Console output showing `compute_and_store` run against a simulated Friday → Monday weekend (fixture data) producing correct excess_vol values, saved to `docs/influence-post-monitoring/poc/demos/milestone-3/TASK-012-outcome.txt`.
- **Notes**: No win-rate metric anywhere. No binary is_hit. Excess/vol is the only quality metric.

### TASK-013: Evening summary renderer + full pipeline orchestration
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-012, TASK-010b
- **Context**: Evening summary per PRD §6.17 + UX-SPEC.md + the UX-SPEC override decisions in PRD §8: three metrics per stock (overnight / tradeable / excess-vol with SPY and 20d-vol in parentheses). SHORT annotations `_(short = gain)_` on negative moves. Watch List shown separately. 30-day scorecard is per-poster ranked by average excess/vol. `⚠️ Sample still building` warning when <20 days. Always-send: ships on every trading day even with zero outcomes. `PipelineOrchestrator.run_evening` wires fetch → compute → render → send. **Important:** `rendering/evening_renderer.py` is currently a 1-line stub. TASK-010b will have rewritten `pipeline.py` into a synchronous orchestrator — this task adds the `run_evening(...)` method to that same file.
- **Description**: Implement `rendering/evening_renderer.py` (`render_evening(outcomes, scorecard_rows, trading_days_scored, as_of_date) -> str` or `-> list[str]` if multi-message split is needed at 4000 chars). Add `PipelineOrchestrator.run_evening(run_date, dry_run=False, use_fixtures=False)` method to the new `pipeline.py` (from TASK-010b) — calls OutcomeEngine + ScorecardAggregator + EveningRenderer + `TwilioWhatsAppDelivery` with CallMeBot fallback. Always-send message when no outcomes. Extend the CLI to: `python -m influence_monitor.pipeline evening [--dry-run] [--use-fixtures]`. `--use-fixtures`: inserts records from `tests/fixtures/sample_outcomes.json` (pre-computed outcome data) into the `signals` table, then runs ScorecardAggregator → render → send. Allows M3 deliverables to be validated with a real WhatsApp on any day.
- **Implementation Checklist**:
  - **Schema**: Reads all outcome columns populated by TASK-012 (`overnight_return`, `tradeable_return`, `spy_return`, `stock_20d_vol`, `excess_vol_score`, `price_data_source`) plus the signal metadata (`ticker`, `direction`, `tier`, `account_id`, `signal_date`) — all exist. Writes `messages_sent` row via `repo.log_message_sent(kind='evening', ...)` (method exists) and upserts `daily_summaries` row with `run_type='evening'`, `avg_excess_vol`, etc. All columns exist in schema.
  - **Wire**: `EveningRenderer` instantiated in `PipelineOrchestrator.__init__` (the TASK-010b orchestrator). `run_evening` is added as a new method on the same `PipelineOrchestrator` class. The CLI `main()` in `pipeline.py` dispatches to `run_morning` or `run_evening` based on `sys.argv[1]`. Delivery goes through the same `DELIVERY_REGISTRY` as morning.
  - **Call site**: `PipelineOrchestrator.run_evening` is invoked by the CLI `main()` in `pipeline.py` and by the GitHub Actions `evening_summary.yml` workflow (TASK-014). No other callers.
  - **Imports affected**: `from influence_monitor.rendering.evening_renderer import render_evening` in `pipeline.py`. `from influence_monitor.outcome.outcome_engine import OutcomeEngine` and `from influence_monitor.outcome.scorecard_aggregator import ScorecardAggregator` in `pipeline.py`. No renames.
  - **Runtime files**: `tests/fixtures/sample_outcomes.json` — **exists** (475 lines; 10 records with outcome columns populated; created in TASK-003). `--use-fixtures` mode must read this file and (a) upsert `posts` rows (using `posted_at`, `account_handle` → lookup `account_id`), (b) upsert `signals` rows with all columns including outcome data, then (c) skip OutcomeEngine (outcomes already set) and proceed to ScorecardAggregator → render → delivery. The fixture JSON schema includes `_comment`, `post_text`, `posted_at`, `account_handle`, `corroboration_count` — these must be filtered out before the INSERT just as in TASK-010b's `--use-fixtures`.
- **Acceptance Criteria**:
  - [ ] Per-stock outcome block shows three metrics: `+X.X% overnight / +X.X% tradeable / +X.XX excess-vol (SPY: +X.X% | vol: X.X%)`
  - [ ] SHORT + negative move → `_(short = gain)_` annotation; SHORT + positive → `_(short went up)_`
  - [ ] Watch List outcomes shown in a separate section ("Watch List (monitored only)")
  - [ ] 30-day per-poster scorecard: top 5 by avg excess_vol desc; each row shows `@Handle — avg excess-vol +X.XX (N signals)`
  - [ ] `⚠️ Sample still building — treat as watchlist only (< 20 days)` shown when `trading_days_scored < 20` (value from `ScorecardAggregator.trading_days_with_signals`)
  - [ ] Empty-outcomes day: "No outcomes to report today." still ships (always-send)
  - [ ] Disclaimer footer policy matches PRD §8 (removed for PoC personal-use per Milestone 1 override — verify with user before adding back)
  - [ ] `run_evening` trigger on non-trading days short-circuits without sending
  - [ ] Integration test (dry-run): full evening run against a seeded DB with sample signals produces a correctly formatted message under 4,000 chars
  - [ ] `--use-fixtures`: inserts `sample_outcomes.json` records into `signals` table (via `posts` insert then `signals` insert — excluding non-column JSON fields); runs ScorecardAggregator → render → delivery; sends real WhatsApp with all three metrics and scorecard visible
  - [ ] `python -m influence_monitor.pipeline evening --use-fixtures` completes successfully on any day, with or without organic signals
  - [ ] Live test: real evening WhatsApp arrives (use `--use-fixtures` if no organic outcomes exist)
  - [ ] `daily_summaries` upserted with `run_type='evening'`, `avg_excess_vol`, `pipeline_status='ok'` on success
- **Demo Artifact**: Screenshot of a real evening WhatsApp summary on the user's phone — use `--use-fixtures` if no organic outcomes exist that day — saved to `docs/influence-post-monitoring/poc/demos/milestone-3/TASK-013-evening.png`. Plus a dry-run sample text at `TASK-013-sample.txt`.
- **Notes**: Message length budget: target <40 lines; hard cap 4,000 chars. The disclaimer footer was removed during Milestone 1 per PRD §8 override — do not add it back without user sign-off (the PRD §8 override explicitly flags re-evaluation before any non-personal-use distribution).

---

## Milestone 4: Full 30-Account Production + Scheduling

> **Goal**: Pipeline runs unattended on schedule against the full 30 primary accounts (with backup promotion). User receives morning + evening WhatsApp messages every trading day for a ~4-week validation window.
> **Acceptance Criteria**: After 5 consecutive trading days, user confirms the morning alert arrives before 9:00 AM ET and the evening summary arrives between 4:30–5:30 PM ET on every trading day, with no manual intervention.
> **Demo Gallery**: `docs/influence-post-monitoring/poc/demos/milestone-4/`
> **Review Checkpoint**: 5 trading days of reliable automated delivery before PoC validation begins in earnest.
> **Depends on**: Milestone 3 review passed
> **Status**: To Do

### TASK-014: GitHub Actions scheduling workflows + Turso deployment
- **Status**: To Do
- **Agent**: data-pipeline (impl), architect (phase review)
- **Complexity**: Medium
- **Depends on**: TASK-013
- **Context**: GitHub Actions cron runs the pipeline unattended. Three workflows: market-hours poll (every 2h during 9 AM–5 PM ET), morning send (9:00 AM ET), evening send (4:45 PM ET). Turso hosts the DB so data persists across ephemeral runners. DST handling: cron runs at both EST and EDT UTC offsets OR uses a single UTC schedule with ET-aware early-exit logic inside the pipeline.
- **Description**: Create `.github/workflows/market_hours_poll.yml`, `morning_alert.yml`, `evening_summary.yml`. Configure all secrets via `${{ secrets.* }}`. Verify Turso DB connection from Actions runner. Handle EST/EDT DST: use UTC cron but pipeline checks `is_trading_day` + ET-local time boundaries before running. Add a `poll` CLI subcommand to `pipeline.py` if it does not exist (the market-hours poll re-runs ingestion + classification only, no delivery — used to keep `engagement_snapshots` fresh between morning and evening).
- **Implementation Checklist**:
  - **Schema**: `engagement_snapshots` (written by `poll` subcommand — columns `post_id`, `snapshot_at`, `view_count`, `repost_count`, `reply_count`, `like_count` — all exist). No schema changes. Turso-side: the workflows must be able to write to the Turso DB over the wire — the existing `repository.py::_LibSQLBackend` (lines 53-85) already supports this.
  - **Wire**: Workflows invoke `python -m influence_monitor.pipeline <subcommand>` as the only command. No Python code wiring needed beyond adding a `poll` subcommand to the new `pipeline.py` CLI main() if missing. Workflow secrets map 1:1 to `.env` keys (via `env:` block in each job step).
  - **Call site**: The GitHub Actions runner is the caller. Locally, `python -m influence_monitor.pipeline [morning|evening|poll] [--dry-run]` is the entry — `morning` and `evening` are added by TASK-010b/-013; `poll` is added here.
  - **Imports affected**: None beyond TASK-010b/-013. If `poll` subcommand is added, `pipeline.py` must route `main()` to a new method (`PipelineOrchestrator.run_poll()` or similar) that re-fetches posts without re-scoring or re-sending.
  - **Runtime files**: Workflows reference `requirements.txt` (exists), `en_core_web_sm` spaCy model (downloaded at runtime), `config/accounts.json`, `config/scoring_config_seed.json`, `config/prompts/scoring_prompt.txt`, `config/false_positive_filter.json`, `data/sp500.csv` + `data/russell3000.csv` + `data/supplement.txt` (the latter two are downloaded-on-demand by `SymbolWhitelist.load` — `sp500_constituents.csv` currently exists as legacy name, `supplement.txt` exists, `russell3000.csv` does NOT — verify whitelist download-on-demand still works from the Actions runner with no cached copy). `data/twitter_cookies.json` is gitignored — twikit login must happen in an initial `workflow_dispatch` job or the cookies must be committed to GitHub Secrets as a multi-line secret (document the choice in this task).
- **Acceptance Criteria**:
  - [ ] `market_hours_poll.yml`: cron every 2h UTC covering 9 AM–5 PM ET; pipeline internally checks ET-local hours to early-exit outside window
  - [ ] `morning_alert.yml`: cron `0 13 * * 1-5` (EST: 8 AM ET — buffer for processing; pipeline sends at 9:00 AM ET sharp by waiting if needed)
  - [ ] `evening_summary.yml`: cron `45 20 * * 1-5` (EST: 3:45 PM ET — buffer for price availability; pipeline sends 4:45 PM ET)
  - [ ] All workflows: `pip install -r requirements.txt` + `python -m spacy download en_core_web_sm` + set `TURSO_URL` + `TURSO_TOKEN`
  - [ ] All secrets from TDD §7 registered in GitHub Actions Secrets: `TWIKIT_USERNAME`, `TWIKIT_EMAIL`, `TWIKIT_PASSWORD`, `ANTHROPIC_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_SANDBOX_NUMBER`, `CALLMEBOT_API_KEY`, `RECIPIENT_PHONE_E164`, `TURSO_URL`, `TURSO_TOKEN`, `ALPHA_VANTAGE_API_KEY`, `TWITTER_COOKIES_JSON` (multi-line, optional)
  - [ ] `continue-on-error: false` so failures surface in Actions UI
  - [ ] `workflow_dispatch` trigger available on all three for manual runs
  - [ ] Documented DST caveat per TDD §7: on March (spring-forward) and November (fall-back) transition days, UTC cron fires will drift 1 hour in ET; pipeline's internal ET-local-time check early-exits outside the target window. Acceptable for PoC — no code change. README captures the caveat.
  - [ ] `poll` subcommand added to `pipeline.py` main() (if not already present) that fetches posts + writes engagement_snapshots without sending
  - [ ] Twikit cookie persistence strategy documented: either (a) one-time `workflow_dispatch` auth run that writes cookies back to a secret, or (b) cookies committed as a multi-line secret. Document the chosen path in `projects/influence-post-monitoring/README.md`.
- **Demo Artifact**: Screenshot of GitHub Actions showing 3 successful scheduled runs (one each of poll + morning + evening), saved to `docs/influence-post-monitoring/poc/demos/milestone-4/TASK-014-actions.png`.
- **Notes**: Turso free tier covers PoC comfortably; README documents the setup (create DB, capture `libsql://` URL and token).

### TASK-015: Full 30-account live run + account validation verification
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-014
- **Context**: Remove the `account_limit=3` safeguard and run against all 30 primaries. `AccountRegistry` validates all handles and promotes backups for any inactive primary. Twitter suspension risk increases at scale — polling stays at 2h cadence.
- **Description**: Remove `--account-limit` default from pipeline. Run full morning + evening pipeline against all 30 primaries for 5 consecutive trading days. Verify `AccountRegistry` correctly handles any inactive primary (e.g., Citron reduced activity, placeholder B14). Log all promotions to `accounts.status` changes.
- **Implementation Checklist**:
  - **Schema**: Reads `accounts` rows where `status='primary'`; writes status transitions via `repo.upsert_account(...)` (method exists, line 261 of `repository.py`). Also uses `repo.update_account_failure`, `repo.reset_account_failures`, `repo.rename_account_handle` — all exist. No schema changes.
  - **Wire**: No new wiring — this task is a configuration/behavior change: remove the hardcoded `account_limit=3` default in `PipelineOrchestrator.run_morning()` (added in TASK-010b) so that the full primary set is processed by default. `AccountRegistry.validate_and_promote()` is already invoked as step 1 of `run_morning()` from TASK-010b.
  - **Call site**: Callers of `PipelineOrchestrator.run_morning` are the CLI `main()` and the GitHub Actions workflows. Both pass `--account-limit` through from the user — when omitted, `account_limit=None` now processes all primaries.
  - **Imports affected**: None.
  - **Runtime files**: Depends on `config/accounts.json` containing all 45 entries (30 primary + 15 backup) — **verify by count** (`jq length config/accounts.json` → expect 45). Depends on every listed primary handle being currently live on Twitter at the time of the run — `AccountRegistry` handles the rest via the 5-step resolution sequence implemented in TASK-004.
- **Acceptance Criteria**:
  - [ ] Morning pipeline processes all 30 active accounts within the 9:00 AM ET send deadline
  - [ ] Any inactive primary is promoted by `AccountRegistry` on startup; logged via WARNING
  - [ ] `accounts` table shows `status` transitions for inactive primaries → `status='inactive'`; promoted backup → `status='primary'`
  - [ ] 5 consecutive trading days of successful morning + evening sends with zero manual intervention
  - [ ] No twikit suspension or 429 errors during the 5-day run (if any occur: documented in `BACKLOG.md` and acceptance relaxed to 3 successful days)
  - [ ] `daily_summaries` shows `pipeline_status='ok'` on all 5 days
  - [ ] User's phone receives 10 messages (5 morning + 5 evening) over the validation window
- **Demo Artifact**: Screenshots of the 10 messages arranged in a grid + a DB export of `daily_summaries` for the 5-day window, saved to `docs/influence-post-monitoring/poc/demos/milestone-4/TASK-015-5day-run.png` and `TASK-015-summaries.csv`.
- **Notes**: If Burry (account #12) is inactive during this window: validate that his backup promotion works. If the throwaway X account gets suspended: TASK moves to Blocked; user creates a new throwaway or accelerates the MVP tweepy swap.

---

## Milestone 5: Hardening, Testing, Documentation

> **Goal**: Integration tests, security review, and README complete. Known-good state ready for 4-week personal-use PoC validation.
> **Acceptance Criteria**: `pytest` passes with 80%+ coverage on core modules. Security review is clean. README is complete with setup, runbook, and Phase 2 notes. `PHASE-REVIEW.md` drafted at PoC close.
> **Demo Gallery**: `docs/influence-post-monitoring/poc/demos/milestone-5/`
> **Review Checkpoint**: User approves the README and security review before final PoC sign-off.
> **Depends on**: Milestone 4 review passed
> **Status**: To Do

### TASK-016: End-to-end integration tests + sample fixtures
- **Status**: To Do
- **Agent**: test-validator
- **Complexity**: Medium
- **Depends on**: TASK-015
- **Context**: Integration tests validate the full pipeline end-to-end with mocked external deps. Fixtures cover: high-conviction LONG (FNMA-style), high-conviction SHORT (Burry-style), neutral post, direction-flip scenario, 3-poster mixed-direction scenario, Burry-deleted post, price-data-unavailable case. **Note:** `tests/fixtures/sample_posts.json` (72 lines) already exists from the old email-based PoC cut — contents must be reviewed and expanded to 10 entries covering the scenarios listed below.
- **Description**: Expand `tests/fixtures/sample_posts.json` to 10 realistic post fixtures (append or replace existing entries as needed). Implement end-to-end tests: morning pipeline with all scenarios → render → assert content; evening pipeline with price fixtures → assert excess_vol + scorecard. Rewrite the existing legacy `tests/test_integration.py` (currently imports `DatabaseRepository` and old orchestrator APIs) against the new synchronous `PipelineOrchestrator` from TASK-010b/-013.
- **Implementation Checklist**:
  - **Schema**: `:memory:` SQLite test DB uses the same `schema.sql` via `repo.init_schema()` — no schema changes. Fixture inserts go through `repo.insert_post` → `repo.insert_signal` → `repo.update_signal_outcome` as implemented in earlier tasks.
  - **Wire**: No production wiring — this task is test code only. Tests instantiate `PipelineOrchestrator` with mocked `source` (twikit), mocked `llm_client` (Claude), mocked `market_client` (yfinance), and mocked `delivery` (Twilio). The real `repo`, `ticker_extractor`, `scoring_engine`, `conflict_resolver`, `classifier`, `outcome_engine`, `scorecard_aggregator`, `renderers` are used unmocked.
  - **Call site**: N/A.
  - **Imports affected**: Test file `tests/test_integration.py` currently imports `DatabaseRepository`, `EmailProvider`, etc. — REWRITE. Delete or rewrite any test under `tests/` that still imports from the removed `influence_monitor.email.*`, `influence_monitor.calendar`, `influence_monitor.scorecard.*`, or `influence_monitor.market_data.index_resolver`. Grep the tests directory before writing new tests: `grep -rn "from influence_monitor.email\|from influence_monitor.calendar\|from influence_monitor.scorecard\|IndexMembershipResolver"` — zero matches expected after TASK-010a finishes.
  - **Runtime files**: `tests/fixtures/sample_posts.json` (**exists**, needs expansion), `tests/fixtures/sample_signals.json` (exists, 10 records), `tests/fixtures/sample_outcomes.json` (exists, 10 records). No new runtime files.
- **Acceptance Criteria**:
  - [ ] `sample_posts.json` has 10 fixtures covering: Ackman-FNMA LONG, Burry SHORT, neutral, direction flip (same poster), 3-poster mixed, deleted post, high virality, low virality (Watch only), multi-ticker post, corroboration (2 posters same ticker same direction)
  - [ ] Morning pipeline test: fixtures → Claude mock → scoring → classify → render → assert top ticker, tier, corroboration tag
  - [ ] Evening pipeline test: signals + price fixtures → outcome → scorecard → render → assert three-metric format + `Sample still building` when `days<20`
  - [ ] Conflict-resolution test: direction flip scenario → `⚠️ Direction changed` tag rendered
  - [ ] Multi-poster test: 3 posters mixed → both direction blocks rendered with `⚠️ Conflicted`
  - [ ] Price-unavailable test: outcome row renders `— price data unavailable`
  - [ ] **Edge case — malformed LLM response**: Claude mock returns malformed JSON → pipeline assigns zero-score sentinel (score=0.0, direction=NEUTRAL), signal is not classified as ACT_NOW or WATCH, no exception raised
  - [ ] **Edge case — common-word ticker**: Post containing "IT" (common word) → `TickerExtractor` whitelist filter suppresses it; no IT signal emitted
  - [ ] **Edge case — tier boundary score**: Signal with `final_score` exactly at the ACT_NOW/WATCH boundary → assigned to the correct tier (assert boundary value maps to the lower tier per classifier spec)
  - [ ] **Edge case — post with 10+ ticker mentions**: Extraction runs without crash; all valid tickers extracted up to the extractor's internal cap
  - [ ] `pytest --cov=influence_monitor tests/` passes with ≥80% coverage on `extraction/`, `scoring/`, `outcome/`, `rendering/`
  - [ ] `pytest tests/` runs with no live-credential requirements (all external deps mocked)
  - [ ] No test file imports from `influence_monitor.email`, `influence_monitor.calendar`, `influence_monitor.scorecard`, or `IndexMembershipResolver` (grep-verified)
- **Demo Artifact**: Output of `pytest --cov` with coverage report + the fixture file, saved to `docs/influence-post-monitoring/poc/demos/milestone-5/TASK-016-tests.txt` and `TASK-016-fixtures.json`.
- **Notes**: Use `unittest.mock.patch` for twikit, Claude, yfinance, Twilio. Store test DB in `:memory:` SQLite.

### TASK-017: README + setup documentation
- **Status**: To Do
- **Agent**: content-writer
- **Complexity**: Low
- **Depends on**: TASK-016
- **Context**: README is the onboarding surface — must include the "Built with Claude Code" attribution, complete setup (Twilio sandbox activation, twikit auth, Turso DB setup, GitHub Actions secrets), the daily runbook, and MVP migration notes (tweepy swap, public leaderboard page). **Note:** `projects/influence-post-monitoring/README.md` (~8 KB) already exists from the old email-based PoC. It mentions email providers, a stale directory tree, and stale CLI commands. This task REWRITES it for the WhatsApp-based architecture — not just edits around the edges.
- **Description**: Rewrite `projects/influence-post-monitoring/README.md` with: project description, `> Built with [Claude Code](https://claude.ai/code)` line, setup guide, architecture overview, configuration reference, known limitations, MVP migration notes.
- **Implementation Checklist**:
  - **Schema**: N/A (documentation only).
  - **Wire**: N/A.
  - **Call site**: N/A.
  - **Imports affected**: N/A.
  - **Runtime files**: None written. References to `projects/influence-post-monitoring/README.md` (the file being rewritten), `.env.example`, `requirements.txt`, `config/accounts.json`, `config/scoring_config_seed.json`, `config/prompts/scoring_prompt.txt` — all exist. The README directory tree must match the **post-TASK-010a/-010b** code layout (no `email/`, no `calendar.py`, no `scorecard/`, no `index_resolver.py`). Verify layout via `ls influence_monitor/` at the time of writing.
- **Acceptance Criteria**:
  - [ ] README begins with project description + `> Built with [Claude Code](https://claude.ai/code)` directly below (per CLAUDE.md GitHub Rule #4)
  - [ ] Setup: clone, venv, `pip install -r requirements.txt`, spaCy model download, `.env` from `.env.example`
  - [ ] Twilio WhatsApp Sandbox setup walkthrough (with console links)
  - [ ] twikit throwaway-account + `python -m influence_monitor.pipeline auth` (or equivalent) step for initial cookie save
  - [ ] Turso account setup + `TURSO_URL` / `TURSO_TOKEN` capture
  - [ ] GitHub Actions secrets list (matches TASK-014's secret list)
  - [ ] Database init command: `python -m influence_monitor.db.repository --init`
  - [ ] Dry-run commands: `--dry-run` morning and evening; `--use-fixtures` variants
  - [ ] Architecture overview (2-para summary of the pipeline components) reflecting the new modules (delivery, ingestion, extraction, scoring F1..F5, outcome, rendering) — NOT the old email/calendar/scorecard modules
  - [ ] Known limitations: twikit ToS, Burry-deletion pattern, yfinance staleness, DST handling caveat, twikit cookie refresh procedure
  - [ ] MVP migration notes: `SOCIAL_SOURCE=twitter_official` tweepy swap, public leaderboard page plan, weight recalibration via SQL (`UPDATE scoring_config SET value=... WHERE key=...`)
  - [ ] Regulatory disclaimer prominent: "This is information about public posts, not investment advice."
  - [ ] No references to email providers, SendGrid, Resend, or `HolidayCalendar` (grep-verified)
- **Demo Artifact**: The finished README.md (link to file).
- **Notes**: No marketing copy. No emojis. Technical documentation only.

### TASK-018: Security review + PHASE-REVIEW.md
- **Status**: To Do
- **Agent**: architect
- **Complexity**: Low
- **Depends on**: TASK-017
- **Context**: Security review is the architect's gate before PoC → MVP. Covers CLAUDE.md security rules + architect-specific PII review, rate-limit abuse check, data-flow audit. `PHASE-REVIEW.md` summarizes the PoC: what worked, what didn't, what to promote from BACKLOG, Beta-decision commercial-signal reading.
- **Description**: Conduct security review against CLAUDE.md + TDD §5. Write `docs/influence-post-monitoring/poc/PHASE-REVIEW.md` per the phase-review template.
- **Implementation Checklist**:
  - **Schema**: N/A (review task; writes no code or data).
  - **Wire**: N/A.
  - **Call site**: N/A.
  - **Imports affected**: N/A.
  - **Runtime files**: Reads all project files for review. Writes `docs/influence-post-monitoring/poc/PHASE-REVIEW.md` (per template at `docs/templates/PHASE-REVIEW-TEMPLATE.md` — verify template exists before starting). Also reads `docs/influence-post-monitoring/poc/BACKLOG.md` (may or may not exist yet — if absent, note "no backlog items accrued during PoC" in the review).
- **Acceptance Criteria**:
  - [ ] No secrets in code or `.env.example` (grep for `TWIKIT_PASSWORD`, `TWILIO_AUTH_TOKEN`, `ANTHROPIC_API_KEY`, `TURSO_TOKEN` in py/json/yaml)
  - [ ] `data/twitter_cookies.json` confirmed gitignored + absent from `git log`
  - [ ] All external API responses Pydantic-validated (Claude) or defensively accessed (twikit, yfinance)
  - [ ] Ticker whitelist validation confirmed active
  - [ ] yfinance freshness assertion confirmed active
  - [ ] No `print()` in production code
  - [ ] PII storage review: user phone number is the only PII; Turso-encrypted-at-rest; no redistribution
  - [ ] Rate-limit abuse check: twikit ~1,500 req/day; Twilio ~2 msg/day; Claude ~1,500/month — all well within provider limits
  - [ ] Data-flow audit: inbound public data only; outbound Twilio API; no webhook attack surface; no third-party redistribution
  - [ ] `PHASE-REVIEW.md` exists with: what worked, what didn't, what's in BACKLOG, commercial-signal reading (avg excess/vol of top poster over PoC window), MVP readiness, Beta go/no-go assessment
- **Demo Artifact**: The `PHASE-REVIEW.md` file + the security-review checklist output, saved to `docs/influence-post-monitoring/poc/demos/milestone-5/TASK-018-review.txt`.
- **Notes**: This task gates the PoC → MVP transition. Do not declare PoC complete without it.

---

## Completed Milestones Log

### ✅ Milestone 2 — Ingestion + Scoring Pipeline (Act Now tier only)
**Approved**: 2026-04-19 | **Outcome**: Approved with notes

**Tasks**: TASK-003, TASK-004, TASK-005, TASK-006, TASK-007, TASK-008, TASK-009, TASK-010a, TASK-010b, TASK-010c
**Demo Gallery**: `docs/influence-post-monitoring/poc/demos/milestone-2/`

**What shipped**: Full ingestion → scoring → delivery pipeline end-to-end. SQLite schema + repo layer; twikit ingestion + AccountRegistry; trading calendar; 3-layer ticker extraction; Claude Haiku directional scoring; five-factor scoring engine (F1–F5) with DB-stored weights; amplifier fetcher; legacy module cleanup; synchronous morning orchestrator with `--use-fixtures` / `--dry-run` / `--account-limit` flags; conflict block renderer with 📈📉 grouped format and 5-signal cap. 401 tests passing.

**User notes**: "Current validation is most for the happy flow, should we add a new task to ensure major edge cases are covered?"

**Deviations accepted**: TASK-010c (conflict renderer) added mid-milestone after deliverable review — BA-confirmed ALIGNED. WhatsApp Sandbox 24-hour session window encountered; WhatsApp Message Templates noted as MVP requirement. PRD §8 override entries for format decisions still open — architect to close before Milestone 3 gate.

---

### ✅ Milestone 1 — First WhatsApp Alert End-to-End (hardcoded data)
**Approved**: 2026-04-19 | **Outcome**: Approved

**Tasks**: PRE-001, TASK-001, TASK-002
**Demo Gallery**: `docs/influence-post-monitoring/poc/demos/milestone-1/`

**What shipped**: Twilio + CallMeBot delivery layer; `render_morning` with full UX (Act Now / Watch List, market cap class, ✅ conviction score + %, 🔄/⚔️ warning emojis, multi-poster list, 150-char quote truncation, 2-message split at 4,000 chars, `❌ No signals for today.` empty state); `--demo` and `--demo-empty` CLI entrypoints. 343 tests passing.

**Deviations accepted**: Conviction dots replaced by ✅+%; CORROBORATED label removed (multi-poster list self-evident); disclaimer footer removed for PoC personal-use readability (must be re-evaluated before any non-personal-use distribution — PRD §8 override to be added by architect).
