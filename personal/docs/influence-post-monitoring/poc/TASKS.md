# Task Breakdown — Influence Post Monitoring

> **Status**: Active
> **Phase**: PoC
> **Last Updated**: 2026-04-18
> **Depends on**: PRD.md, TDD.md, DATA-SOURCES.md (all drafted 2026-04-18)
> **Supersedes**: 2026-04-17 TASKS.md (email-based 20-task PoC — fully rebuilt)

## Progress Summary

| Status | Count |
|--------|-------|
| Done | 5 |
| In Progress | 0 |
| To Do | 13 |
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
- **Description**: Create `db/schema.sql` with all CREATE TABLE from TDD §2.4 (tenants, users, accounts, posts, engagement_snapshots, retweeters, price_cache, scoring_config, signals, messages_sent, daily_summaries, api_usage). Implement `db/repository.py` with `SignalRepository` — connection management (Turso or local SQLite via `libsql_client`), and all read/write methods referenced by later tasks. Implement `--init` CLI flag that creates schema, seeds the default tenant, the default user (from `.env` `RECIPIENT_PHONE_E164`), all 45 accounts from `config/accounts.json`, and `scoring_config` from `config/scoring_config_seed.json`. Also create `tests/fixtures/sample_signals.json` (10 pre-scored, pre-classified signal records covering all key rendering scenarios) and `tests/fixtures/sample_outcomes.json` (same records with outcome data populated). These fixture files are the basis for `--use-fixtures` mode in the orchestrators (TASK-010, TASK-013) — allowing deliverables to be tested without real overnight signals.
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
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Low
- **Depends on**: TASK-001
- **Context**: `pandas_market_calendars` is authoritative for every date decision in the project (prev_close, collection window, `is_trading_day`, forward-N-trading-days). No ad-hoc `datetime.weekday()` arithmetic anywhere — doing it naively would break on US holidays. This is used by the ingestion window filter (TASK-004), the outcome engine (Milestone 3), and the scorecard aggregator (Milestone 4).
- **Description**: Implement `market_data/trading_calendar.py` with `TradingCalendar` class wrapping `pandas_market_calendars.get_calendar("NYSE")`. Methods: `is_trading_day(date) -> bool`, `previous_trading_day(date) -> date`, `next_trading_day(date) -> date`, `trading_days_after(date, n) -> date`, `trading_days_between(start, end) -> list[date]`, `collection_window(send_time_et) -> tuple[datetime, datetime]` (returns previous-close datetime to send-time datetime).
- **Acceptance Criteria**:
  - [ ] Uses `pandas_market_calendars.get_calendar("NYSE")`
  - [ ] `is_trading_day(date(2026, 7, 4))` returns `False` (Independence Day)
  - [ ] `is_trading_day(date(2026, 4, 18))` returns `False` (Good Friday)
  - [ ] `previous_trading_day(date(2026, 4, 20))` returns `2026-04-17` (Monday → prior Thursday, Fri was Good Friday)
  - [ ] `collection_window(datetime(2026, 4, 21, 9, 0, tz=ET))` returns `(prev_close_datetime, send_datetime)` with prev_close = 2026-04-17 16:00 ET (Friday 4/17 was a trading day)
  - [ ] `trading_days_after(date(2026, 1, 1), 5)` correctly skips weekends and MLK Day
  - [ ] Unit tests: weekend crossing, Good Friday, Memorial Day, Thanksgiving, Christmas, day-after-Thanksgiving early close (not handled at PoC — close = 16:00 always; documented)
- **Demo Artifact**: Python REPL output showing 10 representative date queries (weekends, holidays, prev_close at month-boundaries), saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-005-calendar.txt`.
- **Notes**: Early-close trading days (day after Thanksgiving, Christmas Eve) are treated as 16:00 ET close at PoC — the small data error is acceptable; documented in the class docstring.

### TASK-006: Ticker extraction (3-layer + whitelist)
- **Status**: To Do
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
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-001
- **Context**: Claude Haiku is the most expensive external dep (~$0.25/month) but produces the conviction-level and direction classification. Pydantic validation of every response is mandatory — parse failures return a zero-score sentinel rather than crashing. System prompt lives in `config/prompts/scoring_prompt.txt` (DATA-SOURCES.md §Source 5), not in code.
- **Description**: Implement `scoring/llm_client.py` (`LLMClient` ABC, `PostScore` Pydantic model per DATA-SOURCES.md §Source 5). Implement `scoring/claude_client.py` (`ClaudeHaikuClient` — reads prompt from file, calls `anthropic.Anthropic`, Pydantic-validates response, logs to `api_usage` table, retries once on `APIError`, sentinel on parse fail).
- **Acceptance Criteria**:
  - [ ] `LLMClient` ABC defines `score_post(post_text, author_handle) -> PostScore`
  - [ ] `PostScore` validates `tickers`, `direction`, `conviction_level` (0–5), `key_claim`, `argument_quality`, `time_horizon`, `market_moving_potential`, `rationale`
  - [ ] System prompt read from `config/prompts/scoring_prompt.txt` (not inline)
  - [ ] Model: `claude-haiku-4-5` or latest Haiku
  - [ ] On Pydantic fail: logs raw response WARNING, returns sentinel (`conviction_level=0`, `direction="AMBIGUOUS"`, empty lists)
  - [ ] On `APIError`: retries once after 5s; sentinel on second fail
  - [ ] Every call logged to `api_usage` with `provider='anthropic'`, latency_ms, tokens, status
  - [ ] Integration test: score 5 real posts and verify all return valid `PostScore`; zero parse errors
- **Demo Artifact**: Output of scoring 5 fixture posts (including the FNMA Ackman example) with PostScore serialized as JSON, saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-007-scoring.json`.
- **Notes**: Store `llm_model_version`, raw response, token counts on every `signals` row for MVP audit and re-scoring.

### TASK-008: Five-factor scoring engine + conflict resolver + signal classifier
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: High
- **Depends on**: TASK-003, TASK-006, TASK-007
- **Context**: The scoring engine combines Claude's output with the credibility seed (F1), virality (F2a/F2b), consensus (F3), amplifier (F4 — only for Act Now, see TASK-009), and liquidity (F5). All weights read from `scoring_config` table (not hardcoded). Conflict resolver handles same-poster repeats/flips and multi-poster mixed-direction splits per PRD §6.12. Classifier assigns ACT_NOW / WATCH / UNSCORED using virality thresholds.
- **Description**: Implement `scoring/scoring_engine.py` (`ScoringEngine` loads weights from `scoring_config`; computes F1..F5 and composite conviction_score). Implement `scoring/conflict_resolver.py` (same-poster highest-virality selection for same-direction repeats; most-recent + `direction_flip=True` + penalty for same-poster flips; per-direction signal emission with `conflict_group='opposing_exists'` for 3+ posters mixed direction). Implement `scoring/classifier.py` (thresholds from `scoring_config`; `classify(post) -> 'ACT_NOW' | 'WATCH' | 'UNSCORED'`). Persist all factor scores individually on the `signals` row.
- **Acceptance Criteria**:
  - [ ] `ScoringEngine` loads weights from `scoring_config` table (not hardcoded)
  - [ ] All five sub-scores (F1 credibility, F2a virality_abs, F3 consensus, F4 amplifier, F5 liquidity) computed and persisted to `signals`
  - [ ] F2b (virality_vel) computed only for WATCH tier; F4 (amplifier) populated only for ACT_NOW after TASK-009
  - [ ] `conviction_level < 2` or `direction in ["NEUTRAL", "AMBIGUOUS"]` → `conviction_score = 0`, `tier = 'UNSCORED'`
  - [ ] `ConflictResolver`: same-poster repeats → highest-virality retained, others dropped
  - [ ] `ConflictResolver`: same-poster flip → `direction_flip=True` (always set), `penalty_applied = scoring_config.direction_flip_penalty` (default 0.0 — tag-only at PoC, non-zero values immediately activate penalty deduction with no code change), most-recent retained
  - [ ] Test case: with `direction_flip_penalty=0.0` (default), a flipped signal renders the `⚠️ Direction changed` tag but its `final_score == conviction_score` (no deduction)
  - [ ] Test case: with `direction_flip_penalty=2.0` (simulated DB update), the same flipped signal produces `final_score = conviction_score - 2.0`
  - [ ] `ConflictResolver`: 3+ posters on same ticker mixed direction → one signal per direction group, `conflict_group='opposing_exists'` on each
  - [ ] `classify` returns ACT_NOW when `views >= virality_views_threshold` OR `reposts >= virality_reposts_threshold`
  - [ ] `classify` returns WATCH when below threshold but `views_per_hour >= watch_velocity_floor`
  - [ ] Unit tests: single post scoring, same-poster repeat, same-poster flip, 3-poster mixed, threshold crossings, all weights DB-driven
- **Demo Artifact**: Output of scoring 6 fixture posts (including one flip scenario and one 3-poster mixed scenario) showing all factor scores, tier assignment, and conflict handling, saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-008-scoring.txt`.
- **Notes**: ScoringEngine must be pure — receives `PostScore` + `RawPost` + account credibility, does not call external services. Testable in isolation.

### TASK-009: Amplifier fetcher + market-cap resolver
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-004, TASK-008
- **Context**: Amplifier quality (F4) is fetched only for ACT_NOW candidates (~5–10/day) to respect twikit rate limits. Each retweeter is persisted in the `retweeters` table at fetch time (amplifier regression dataset for MVP). Cross-reference with the `accounts` table — any monitored account in the retweeter list = strong signal. Market-cap resolver uses `finvizfinance` with a weekly cache in the `price_cache` table.
- **Description**: Implement `scoring/amplifier.py` (`AmplifierFetcher.fetch_and_score(post, source)` → calls `source.fetch_retweeters`, persists all to `retweeters` with `is_monitored` set by cross-ref against `accounts`; applies the TDD §2.3 formula: `min(10, monitored_count*3 + high_follower_count*1.5 + mid_follower_count*0.5)` with tiers from `scoring_config`). Implement `market_data/market_cap_resolver.py` (`MarketCapResolver.resolve(ticker)` → `price_cache` hit within 7 days returns cached; else finvizfinance call + insert; on failure returns `"Micro"`). Map cap class to liquidity modifier (0.8× Mega / 0.9× Large / 1.0× Mid / 1.15× Small / 1.3× Micro) from `scoring_config`.
- **Acceptance Criteria**:
  - [ ] `AmplifierFetcher.fetch_and_score(post, source)` fetches up to ~100 retweeters via `source.fetch_retweeters`
  - [ ] All retweeters persisted to `retweeters` table with `is_monitored` flag set by cross-ref against `accounts`
  - [ ] Amplifier score in [0, 10] per TDD §2.3 formula
  - [ ] Called only for ACT_NOW signals (gated in `PipelineOrchestrator`, enforced in tests)
  - [ ] `MarketCapResolver.resolve` returns one of: Mega, Large, Mid, Small, Micro
  - [ ] 7-day cache in `price_cache`; cache miss calls finvizfinance
  - [ ] finvizfinance failure returns `"Micro"` + WARNING log
  - [ ] Market-cap string parsing: `"3911.50B"` → 3_911_500 (millions); `"498.22M"` → 498; `""` → None → Micro
  - [ ] Liquidity modifier applied to conviction_score per class
  - [ ] Unit tests: amplifier formula with 0/1/3 monitored matches; cap-class parsing edge cases; cache hit/miss
- **Demo Artifact**: DB dump showing `retweeters` rows from a real Act Now Ackman post + the computed `score_amplifier`, saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-009-amplifier.txt`.
- **Notes**: Follower tier thresholds (high 100K+, mid 10K-50K) are in `scoring_config` and configurable.

### TASK-010: Morning pipeline orchestrator (end-to-end 3-account demo)
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: High
- **Depends on**: TASK-002, TASK-004, TASK-005, TASK-006, TASK-007, TASK-008, TASK-009
- **Context**: Wires all Milestone 2 components into `PipelineOrchestrator.run_morning(run_date)`. First end-to-end run is against 3 accounts only (Ackman, Burry, Chanos) to validate the pipeline before scaling to 30. Real-data WhatsApp message replaces the hardcoded Milestone 1 fixture. Always-send rule honored: empty-signals message ships even when no signals are found.
- **Description**: Implement `pipeline.py` with `PipelineOrchestrator.run_morning(run_date: date, account_limit: int | None = None)`. Steps: (1) validate accounts via `AccountRegistry`, (2) `source.fetch_recent_posts` for each active account in collection window via `TradingCalendar`, (3) insert posts + engagement_snapshots, (4) extract tickers per post, (5) Claude-score each, (6) build signals via ScoringEngine (F1/F2/F3/F5 at this stage), (7) apply ConflictResolver, (8) classify into ACT_NOW/WATCH/UNSCORED, (9) for ACT_NOW: AmplifierFetcher (F4), (10) persist signals, (11) render morning alert top-5 ACT_NOW + top-5 WATCH, (12) send via `TwilioWhatsAppDelivery` with CallMeBot fallback, (13) write `daily_summaries` and `messages_sent` rows. `account_limit=3` for the initial milestone demo; remove for full run. CLI: `python -m influence_monitor.pipeline morning [--account-limit N] [--dry-run] [--use-fixtures]`. `--use-fixtures`: bypasses steps 1–9 entirely (no twikit, no Claude), inserts records from `tests/fixtures/sample_signals.json` directly into the `signals` table with all factor scores pre-populated, then executes steps 10–13 (classify → render → send). This allows M2 deliverables to be validated with a real WhatsApp even on days with no organic signals.
- **Acceptance Criteria**:
  - [ ] `run_morning` executes the 13 steps in order; each step logs START/DONE
  - [ ] Non-trading-day short-circuit: no fetch, no message, log INFO and exit
  - [ ] Empty-signals day: "no signals" WhatsApp message still ships (always-send)
  - [ ] AmplifierFetcher called only for ACT_NOW signals (assert in test)
  - [ ] All signals persisted with factor scores populated
  - [ ] `daily_summaries` row upserted with pipeline_status, accounts_fetched, signals_scored, signals_act_now, signals_watch
  - [ ] On `AccountRegistry` all-inactive: operational WhatsApp sent, `pipeline_status='failed'`
  - [ ] On any unhandled exception: operational WhatsApp sent, traceback logged, no partial message
  - [ ] `--dry-run` renders to stdout without sending or writing to DB
  - [ ] `--account-limit 3` demo: pipeline runs end-to-end against 3 real accounts; WhatsApp arrives on user's phone
  - [ ] `--use-fixtures`: inserts `sample_signals.json` records into `signals` table with all factor scores set; then runs classification → rendering → delivery; sends a real WhatsApp with realistic signal blocks (no twikit or Claude credentials required)
  - [ ] `python -m influence_monitor.pipeline morning --use-fixtures` completes successfully on any day, with or without organic signals
- **Demo Artifact**: Two artifacts: (a) CLI log of the 3-account dry-run saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-010-dryrun.txt`; (b) screenshot of the real WhatsApp morning alert — use `--use-fixtures` if no organic signals exist that day, or the live 3-account run if signals exist — saved to `docs/influence-post-monitoring/poc/demos/milestone-2/TASK-010-live.png`.
- **Notes**: Operational failure messages go to the same recipient phone — the user is both operator and user at PoC. `pipeline.py` is the CLI entry point.

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
- **Context**: yfinance silent-stale-data is the #1 data-quality risk. Freshness assertion on every fetch is mandatory. Alpha Vantage is the fallback with 25 req/day — use sparingly. Also fetches SPY for the excess-return computation and the prior-`vol_lookback_days` vol window for each stock (default 20, configurable via `scoring_config.vol_lookback_days`).
- **Description**: Implement `market_data/base.py` (`MarketDataClient` ABC). Implement `market_data/yfinance_client.py` (`YFinanceClient` with `fetch_ohlc(ticker, date)`, `fetch_close(ticker, date)`, `fetch_stock_vol(ticker, date, lookback_days)`, `fetch_spy_return(date)` — all with freshness assertion and single-retry). Implement `market_data/alpha_vantage_client.py` (`AlphaVantageClient` fallback via `GLOBAL_QUOTE`). Batch-fetch helper for efficiency. The lookback is passed as a parameter — callers read `scoring_config.vol_lookback_days` and pass it in; the client does not hardcode 20.
- **Acceptance Criteria**:
  - [ ] `MarketDataClient` ABC defines the four fetch methods; `fetch_stock_vol` takes `lookback_days` as a required parameter (no default of 20 in the client)
  - [ ] `YFinanceClient.fetch_ohlc` asserts `hist.index[-1].date() == date`; raises `DataFreshnessError` on stale
  - [ ] On `DataFreshnessError`: retry once (60s), then fall back to `AlphaVantageClient`; log `provider='yfinance_fallback'` to `api_usage`
  - [ ] `fetch_stock_vol(ticker, date, lookback_days)` returns daily-return stdev over the prior `lookback_days` trading days of the ticker at `date`, using `TradingCalendar.trading_days_between` for date alignment
  - [ ] `fetch_spy_return(date)` returns `(today_close - prev_close) / prev_close` for SPY using `TradingCalendar.previous_trading_day`
  - [ ] Batch `fetch_closes(tickers, date)` uses `yf.download` for efficiency
  - [ ] Unit tests: mock yfinance returning today (pass), yesterday (fail + fallback), empty (fail + fallback); stdev computation on known-vol sample for lookback_days=20 AND a second non-default value (e.g., 10) to confirm the parameter threads through
- **Demo Artifact**: CLI output showing `fetch_ohlc` for AAPL + `fetch_spy_return` + `fetch_stock_vol(lookback_days=20)` for 3 real tickers, saved to `docs/influence-post-monitoring/poc/demos/milestone-3/TASK-011-market-data.txt`.
- **Notes**: Pin yfinance version. Annualize vs. keep daily vol is a modeling choice — we keep daily stdev (matches the daily overnight return numerator; excess/vol is then dimensionally `daily_return / daily_return` which is unitless and interpretable). Documented in the function docstring. The `stock_20d_vol` column name in `signals` is retained for schema stability even if the lookback is retuned; the actual lookback used on any given day is recoverable via `scoring_config.vol_lookback_days` at query time.

### TASK-012: Outcome engine + scorecard aggregator
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-011, TASK-003
- **Context**: Per PRD §6.13–14 and the critical decision updates: overnight_return uses `TradingCalendar.previous_trading_day(today)` for prev_close — handles weekends AND holidays. Excess/vol replaces win-rate entirely: `(stock_return - spy_return) / stock_vol` where the vol lookback window is read from `scoring_config.vol_lookback_days` (default 20). Scorecard aggregator groups by poster (not ticker) and averages excess/vol across the 30-day window. Idempotent for safe re-runs.
- **Description**: Implement `outcome/outcome_engine.py` (`OutcomeEngine.compute_and_store(signal_date)` — for every signal where `overnight_return IS NULL`: read `vol_lookback_days` from `scoring_config`; fetch today_open + today_close + prev_close (from `TradingCalendar.previous_trading_day`) + spy_return + stock_vol (via `fetch_stock_vol(ticker, date, lookback_days=vol_lookback_days)`); compute and persist overnight_return, tradeable_return, excess_vol_score, price_data_source into the `stock_20d_vol` column — the column name is retained for schema stability). Implement `outcome/scorecard_aggregator.py` (`ScorecardAggregator.top_n_posters(as_of, window_days=30, top_n=5)` returns rows of `{handle, avg_excess_vol, n_signals}` sorted desc). `⚠️ Sample still building` is emitted when `trading_days_with_signals < 20`.
- **Acceptance Criteria**:
  - [ ] `OutcomeEngine.compute_and_store` is idempotent (skips signals with non-null `excess_vol_score`)
  - [ ] `prev_close` resolved via `TradingCalendar.previous_trading_day` — Monday correctly uses Friday close
  - [ ] `overnight_return`, `tradeable_return`, `spy_return`, `stock_20d_vol`, `excess_vol_score` persisted to `signals` with 6 decimal places
  - [ ] On any price fetch fail: `price_data_source='unavailable'`, outcome columns NULL, signal excluded from scorecard
  - [ ] `ScorecardAggregator.top_n_posters` returns top 5 by avg excess/vol across all scored signals from each poster in window
  - [ ] Returns `n_signals` count alongside avg (for transparency in "building..." state)
  - [ ] Identifies when `trading_days_with_signals < 20` so renderer can emit warning
  - [ ] Unit tests: LONG + up stock → positive excess_vol; SHORT + up stock → negative excess_vol (correct sign); price fetch fail → NULL + unavailable marker; idempotency; weekend-crossing prev_close; Good-Friday-crossing prev_close
- **Demo Artifact**: Console output showing `compute_and_store` run against a simulated Friday → Monday weekend (fixture data) producing correct excess_vol values, saved to `docs/influence-post-monitoring/poc/demos/milestone-3/TASK-012-outcome.txt`.
- **Notes**: No win-rate metric anywhere. No binary is_hit. Excess/vol is the only quality metric.

### TASK-013: Evening summary renderer + full pipeline orchestration
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-012, TASK-010
- **Context**: Evening summary per PRD §6.17 + UX-SPEC.md + the UX-SPEC override decisions in PRD §8: three metrics per stock (overnight / tradeable / excess-vol with SPY and 20d-vol in parentheses). SHORT annotations `_(short = gain)_` on negative moves. Watch List shown separately. 30-day scorecard is per-poster ranked by average excess/vol. `⚠️ Sample still building` warning when <20 days. Always-send: ships on every trading day even with zero outcomes. `PipelineOrchestrator.run_evening` wires fetch → compute → render → send.
- **Description**: Implement `rendering/evening_renderer.py` (`render_evening(outcomes, scorecard_rows, trading_days_scored, as_of_date) -> str`). Implement `PipelineOrchestrator.run_evening(run_date)` calling OutcomeEngine + ScorecardAggregator + EveningRenderer + `TwilioWhatsAppDelivery`. Always-send message when no outcomes. CLI: `python -m influence_monitor.pipeline evening [--dry-run] [--use-fixtures]`. `--use-fixtures`: inserts records from `tests/fixtures/sample_outcomes.json` (pre-computed outcome data) into the `signals` table, then runs ScorecardAggregator → render → send. Allows M3 deliverables to be validated with a real WhatsApp on any day.
- **Acceptance Criteria**:
  - [ ] Per-stock outcome block shows three metrics: `+X.X% overnight / +X.X% tradeable / +X.XX excess-vol (SPY: +X.X% | vol: X.X%)`
  - [ ] SHORT + negative move → `_(short = gain)_` annotation; SHORT + positive → `_(short went up)_`
  - [ ] Watch List outcomes shown in a separate section ("Watch List (monitored only)")
  - [ ] 30-day per-poster scorecard: top 5 by avg excess_vol desc; each row shows `@Handle — avg excess-vol +X.XX (N signals)`
  - [ ] `⚠️ Sample still building — treat as watchlist only (< 20 days)` shown when `trading_days_scored < 20`
  - [ ] Empty-outcomes day: "No outcomes to report today." still ships (always-send)
  - [ ] Disclaimer footer present
  - [ ] `run_evening` trigger on non-trading days short-circuits without sending
  - [ ] Integration test (dry-run): full evening run against Milestone 2's DB produces a correctly formatted message under 4,000 chars
  - [ ] `--use-fixtures`: inserts `sample_outcomes.json` records into `signals` table; runs ScorecardAggregator → render → delivery; sends real WhatsApp with all three metrics and scorecard visible
  - [ ] `python -m influence_monitor.pipeline evening --use-fixtures` completes successfully on any day, with or without organic signals
  - [ ] Live test: real evening WhatsApp arrives (use `--use-fixtures` if no organic outcomes exist)
- **Demo Artifact**: Screenshot of a real evening WhatsApp summary on the user's phone — use `--use-fixtures` if no organic outcomes exist that day — saved to `docs/influence-post-monitoring/poc/demos/milestone-3/TASK-013-evening.png`. Plus a dry-run sample text at `TASK-013-sample.txt`.
- **Notes**: Message length budget: target <40 lines; hard cap 4,000 chars.

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
- **Description**: Create `.github/workflows/market_hours_poll.yml`, `morning_alert.yml`, `evening_summary.yml`. Configure all secrets via `${{ secrets.* }}`. Verify Turso DB connection from Actions runner. Handle EST/EDT DST: use UTC cron but pipeline checks `is_trading_day` + ET-local time boundaries before running.
- **Acceptance Criteria**:
  - [ ] `market_hours_poll.yml`: cron every 2h UTC covering 9 AM–5 PM ET; pipeline internally checks ET-local hours to early-exit outside window
  - [ ] `morning_alert.yml`: cron `0 13 * * 1-5` (EST: 8 AM ET — buffer for processing; pipeline sends at 9:00 AM ET sharp by waiting if needed)
  - [ ] `evening_summary.yml`: cron `45 20 * * 1-5` (EST: 3:45 PM ET — buffer for price availability; pipeline sends 4:45 PM ET)
  - [ ] All workflows: `pip install -r requirements.txt` + `python -m spacy download en_core_web_sm` + set `TURSO_URL` + `TURSO_TOKEN`
  - [ ] All secrets from TDD §7 registered in GitHub Actions Secrets
  - [ ] `continue-on-error: false` so failures surface in Actions UI
  - [ ] `workflow_dispatch` trigger available on all three for manual runs
  - [ ] Documented DST caveat per TDD §7: on March (spring-forward) and November (fall-back) transition days, UTC cron fires will drift 1 hour in ET; pipeline's internal ET-local-time check early-exits outside the target window. Acceptable for PoC — no code change. README captures the caveat.
- **Demo Artifact**: Screenshot of GitHub Actions showing 3 successful scheduled runs (one each of poll + morning + evening), saved to `docs/influence-post-monitoring/poc/demos/milestone-4/TASK-014-actions.png`.
- **Notes**: Turso free tier covers PoC comfortably; README documents the setup (create DB, capture `libsql://` URL and token).

### TASK-015: Full 30-account live run + account validation verification
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-014
- **Context**: Remove the `account_limit=3` safeguard and run against all 30 primaries. `AccountRegistry` validates all handles and promotes backups for any inactive primary. Twitter suspension risk increases at scale — polling stays at 2h cadence.
- **Description**: Remove `--account-limit` default from pipeline. Run full morning + evening pipeline against all 30 primaries for 5 consecutive trading days. Verify `AccountRegistry` correctly handles any inactive primary (e.g., Citron reduced activity, placeholder B14). Log all promotions to `accounts.status` changes.
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
- **Context**: Integration tests validate the full pipeline end-to-end with mocked external deps. Fixtures cover: high-conviction LONG (FNMA-style), high-conviction SHORT (Burry-style), neutral post, direction-flip scenario, 3-poster mixed-direction scenario, Burry-deleted post, price-data-unavailable case.
- **Description**: Create `tests/fixtures/sample_posts.json` (10 realistic posts). Implement end-to-end tests: morning pipeline with all scenarios → render → assert content; evening pipeline with price fixtures → assert excess_vol + scorecard.
- **Acceptance Criteria**:
  - [ ] `sample_posts.json` has 10 fixtures covering: Ackman-FNMA LONG, Burry SHORT, neutral, direction flip (same poster), 3-poster mixed, deleted post, high virality, low virality (Watch only), multi-ticker post, corroboration (2 posters same ticker same direction)
  - [ ] Morning pipeline test: fixtures → Claude mock → scoring → classify → render → assert top ticker, tier, corroboration tag
  - [ ] Evening pipeline test: signals + price fixtures → outcome → scorecard → render → assert three-metric format + `Sample still building` when `days<20`
  - [ ] Conflict-resolution test: direction flip scenario → `⚠️ Direction changed` tag rendered
  - [ ] Multi-poster test: 3 posters mixed → both direction blocks rendered with `⚠️ Conflicted`
  - [ ] Price-unavailable test: outcome row renders `— price data unavailable`
  - [ ] `pytest --cov=influence_monitor tests/` passes with ≥80% coverage on `extraction/`, `scoring/`, `outcome/`, `rendering/`
  - [ ] `pytest tests/` runs with no live-credential requirements (all external deps mocked)
- **Demo Artifact**: Output of `pytest --cov` with coverage report + the fixture file, saved to `docs/influence-post-monitoring/poc/demos/milestone-5/TASK-016-tests.txt` and `TASK-016-fixtures.json`.
- **Notes**: Use `unittest.mock.patch` for twikit, Claude, yfinance, Twilio. Store test DB in `:memory:` SQLite.

### TASK-017: README + setup documentation
- **Status**: To Do
- **Agent**: content-writer
- **Complexity**: Low
- **Depends on**: TASK-016
- **Context**: README is the onboarding surface — must include the "Built with Claude Code" attribution, complete setup (Twilio sandbox activation, twikit auth, Turso DB setup, GitHub Actions secrets), the daily runbook, and MVP migration notes (tweepy swap, public leaderboard page).
- **Description**: Write `projects/influence-post-monitoring/README.md` with: project description, `> Built with [Claude Code](https://claude.ai/code)` line, setup guide, architecture overview, configuration reference, known limitations, MVP migration notes.
- **Acceptance Criteria**:
  - [ ] README begins with project description + `> Built with [Claude Code](https://claude.ai/code)` directly below
  - [ ] Setup: clone, venv, `pip install -r requirements.txt`, spaCy model download, `.env` from `.env.example`
  - [ ] Twilio WhatsApp Sandbox setup walkthrough (with console links)
  - [ ] twikit throwaway-account + `python -m influence_monitor.ingestion.twitter_twikit --login` step for initial cookie save
  - [ ] Turso account setup + `TURSO_URL` / `TURSO_TOKEN` capture
  - [ ] GitHub Actions secrets list
  - [ ] Database init command: `python -m influence_monitor.db.repository --init`
  - [ ] Dry-run commands: `--dry-run` morning and evening
  - [ ] Architecture overview (2-para summary of the pipeline components)
  - [ ] Known limitations: twikit ToS, Burry-deletion pattern, yfinance staleness, DST handling caveat
  - [ ] MVP migration notes: `SOCIAL_SOURCE=twitter_official` tweepy swap, public leaderboard page plan, weight recalibration via SQL
  - [ ] Regulatory disclaimer prominent: "This is information about public posts, not investment advice."
- **Demo Artifact**: The finished README.md (link to file).
- **Notes**: No marketing copy. No emojis. Technical documentation only.

### TASK-018: Security review + PHASE-REVIEW.md
- **Status**: To Do
- **Agent**: architect
- **Complexity**: Low
- **Depends on**: TASK-017
- **Context**: Security review is the architect's gate before PoC → MVP. Covers CLAUDE.md security rules + architect-specific PII review, rate-limit abuse check, data-flow audit. `PHASE-REVIEW.md` summarizes the PoC: what worked, what didn't, what to promote from BACKLOG, Beta-decision commercial-signal reading.
- **Description**: Conduct security review against CLAUDE.md + TDD §5. Write `docs/influence-post-monitoring/poc/PHASE-REVIEW.md` per the phase-review template.
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

### ✅ Milestone 1 — First WhatsApp Alert End-to-End (hardcoded data)
**Approved**: 2026-04-19 | **Outcome**: Approved

**Tasks**: PRE-001, TASK-001, TASK-002
**Demo Gallery**: `docs/influence-post-monitoring/poc/demos/milestone-1/`

**What shipped**: Twilio + CallMeBot delivery layer; `render_morning` with full UX (Act Now / Watch List, market cap class, ✅ conviction score + %, 🔄/⚔️ warning emojis, multi-poster list, 150-char quote truncation, 2-message split at 4,000 chars, `❌ No signals for today.` empty state); `--demo` and `--demo-empty` CLI entrypoints. 343 tests passing.

**Deviations accepted**: Conviction dots replaced by ✅+%; CORROBORATED label removed (multi-poster list self-evident); disclaimer footer removed for PoC personal-use readability (must be re-evaluated before any non-personal-use distribution — PRD §8 override to be added by architect).
