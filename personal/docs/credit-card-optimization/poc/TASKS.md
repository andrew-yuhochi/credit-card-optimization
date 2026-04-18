# Task Breakdown — Credit Card Optimization

> **Status**: Active
> **Last Updated**: 2026-04-15
> **Depends on**: PRD.md (approved), TDD.md (approved), DATA-SOURCES.md (approved)

---

## Progress Summary

| Status | Count |
|--------|-------|
| Done | 7 |
| In Progress | 0 |
| To Do | 20 |
| Blocked | 0 |

---

## Phase 0: Project Setup

### TASK-001: Repository and Project Scaffold

- **Status**: Done (2026-04-15)
- **Agent**: `data-pipeline`
- **Complexity**: Low
- **Depends on**: None
- **Context**: Per CLAUDE.md, the first completed task must create the GitHub repo under `andrew-yuhochi`. The project lives at `projects/credit-card-optimization/` inside the monorepo. Python 3.11+ virtual environment, requirements.txt with pinned versions, directory structure per TDD Section 2.5.
- **Description**: Create the project directory structure, Python virtual environment, `requirements.txt` with all pinned dependencies, `.env.example`, `.gitignore`, and a minimal `README.md`. Create the GitHub repository under `andrew-yuhochi` named `credit-card-optimization` and push.
- **Acceptance Criteria**:
  - [ ] Directory structure matches TDD Section 2.5 exactly: `app/`, `data/`, `config/`, `migrations/`, `scripts/`, `tests/`
  - [ ] `requirements.txt` pins: `fastapi`, `uvicorn`, `jinja2`, `pydantic>=2`, `sqlalchemy>=2`, `pulp==3.3.0`, `openpyxl==3.1.5`, `httpx`, `beautifulsoup4`, `python-dotenv`, `pytest`, `pytest-cov`, `aiofiles`
  - [ ] `.env.example` contains all variables listed in TDD Section 7 with placeholder values
  - [ ] `.gitignore` excludes: `.env`, `*.db`, `__pycache__/`, `.venv/`, `*.pyc`, `data/cc_optimizer.db`
  - [ ] `README.md` contains the `> Built with [Claude Code](https://claude.ai/code)` line directly below the project description
  - [ ] GitHub repo `andrew-yuhochi/credit-card-optimization` is created as public and the commit is pushed
- **Notes**: Do not create the GitHub repo before this task is complete (per CLAUDE.md GitHub Rule #2).

---

### TASK-002: Static Data Files and Configuration

- **Status**: Done (2026-04-15)
- **Agent**: `data-pipeline`
- **Complexity**: Low
- **Depends on**: TASK-001
- **Context**: The card database (`data/cards/cards.json`), store MCC map (`data/stores/store_mcc_map.json`), bundled MCC reference (`data/stores/mcc_codes.json`), and CPP config (`config/valuation.json`) are all static files loaded at startup. This task creates the file structures with placeholder/seed data for the 5 hand-curated cards that will be used for testing in Phase 1.
- **Description**: Create all static data files with correct schema structure. Seed `cards.json` with 5 representative cards (CIBC Dividend Visa Infinite, Scotiabank Gold Amex, PC Financial World Elite, Rogers World Elite, Amex Cobalt) with accurate data from issuer pages. Download and bundle `mcc_codes.json` from the greggles/mcc-codes GitHub repository. Create `store_mcc_map.json` with the 8 pre-populated stores (Costco, Walmart, Shoppers Drug Mart, Canadian Tire, Loblaws/PC, Amazon Canada, LCBO, Lowe's). Create `config/valuation.json` with CPP defaults.
- **Acceptance Criteria**:
  - [ ] `data/cards/cards.json` validates against the `CardRecord` Pydantic model for all 5 seed cards
  - [ ] All 5 seed cards have accurate `category_rates`, `category_caps_monthly`, `store_overrides`, and `approval` fields sourced from issuer pages (not estimated)
  - [ ] `data/stores/mcc_codes.json` contains the full greggles/mcc-codes dataset (≥ 981 entries)
  - [ ] `data/stores/store_mcc_map.json` maps all 8 pre-populated stores to their MCC and default category
  - [ ] `config/valuation.json` contains CPP defaults for all point systems listed in TDD Section 2.1
  - [ ] `cards.json` schema version field is present: `"schema_version": "1.0"`
- **Notes**: Accuracy of the 5 seed cards matters more than speed — verify each rate against the issuer's live product page. Do not guess or estimate any rate; leave `"source": "estimated"` and `"confidence": "low"` if in doubt.

---

## Phase 1: Data Layer and Core Optimizer

### TASK-003: Pydantic Data Models

- **Status**: Done (2026-04-17)
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-002
- **Context**: All data crosses component boundaries as Pydantic v2 models. The full model hierarchy is defined in TDD Section 8: `CardRecord`, `ApprovalRequirements`, `StoreOverride`, `SpendingProfile`, `PersonProfile`, `DummyCard`, `SpendBucket`, `AssignmentRow`, `CardSummaryRow`, `OptimizationResult`, `DeltaResult`, `OptimizationSession`. Type hints required on all signatures.
- **Description**: Implement all Pydantic models in `app/models/` as specified in TDD Section 8. Add validators where needed (e.g., `monthly_amount >= 0` on spend buckets, `base_rate >= 0` on dummy cards, non-empty `category_spend` or `store_spend` validation on `SpendingProfile`).
- **Acceptance Criteria**:
  - [ ] All models in `app/models/card.py`, `app/models/spending.py`, `app/models/optimization.py`, `app/models/session.py` with zero import errors
  - [ ] `CardRecord.model_validate(seed_card_dict)` succeeds for all 5 seed cards from TASK-002
  - [ ] `SpendingProfile` raises `ValidationError` if both `category_spend` and `store_spend` are empty or all-zero
  - [ ] `DummyCard` raises `ValidationError` if `base_rate < 0`
  - [ ] `CreditScoreBand` and `IncomeBand` enums match the values specified in TDD Section 8
  - [ ] All model files have type hints on every method signature
  - [ ] pytest coverage ≥ 80% on `app/models/`

---

### TASK-004: Card Database Loader

- **Status**: Done (2026-04-17)
- **Agent**: `data-pipeline`
- **Complexity**: Low
- **Depends on**: TASK-003
- **Context**: `CardDatabaseLoader` is a registry-pattern class (abstract base + JSON implementation) that loads `cards.json` at startup and exposes `get_all()`, `get_by_id()`, and `get_store_mcc_map()`. It is the single point of card data access. See TDD Section 2.1.
- **Description**: Implement `app/services/card_loader.py` with the abstract `CardDatabaseLoaderBase` ABC and concrete `JsonCardDatabaseLoader` implementation. Load and validate all card records against `CardRecord` at startup; raise `ValueError` with the offending card's `id` if any record fails validation.
- **Acceptance Criteria**:
  - [ ] `JsonCardDatabaseLoader` loads all 5 seed cards successfully and returns them via `get_all()`
  - [ ] `get_by_id("cibc_dividend_vi")` returns the correct `CardRecord`
  - [ ] `get_by_id("nonexistent")` returns `None`
  - [ ] `get_store_mcc_map()` returns a dict keyed by store slug
  - [ ] Invalid JSON in `cards.json` raises `ValueError` at startup with the offending record's `id`
  - [ ] All file paths use `pathlib.Path`, not string paths
  - [ ] `logging` is used for startup load success/failure, not `print()`
  - [ ] pytest coverage ≥ 80% on `card_loader.py`

---

### TASK-005: Eligibility Pre-Filter

- **Status**: Done (2026-04-17)
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-003, TASK-004
- **Context**: `EligibilityFilter.filter(cards, profile)` removes ineligible cards before the MILP is constructed, reducing the active pool from 100+ to ~40–50. Filter rules are in TDD Section 2.2: Amex toggle, credit score band, income band, household income for couple mode, store acceptance. This is also where performance is won — get it right before touching the solver.
- **Description**: Implement `app/services/eligibility.py`. The filter must handle single mode (one `PersonProfile`) and couple mode (two `PersonProfile` instances). Map credit score bands and income bands to numeric thresholds. Log the number of cards removed per filter rule at `DEBUG` level.
- **Acceptance Criteria**:
  - [ ] With `include_amex=False`, all cards with `requires_amex=True` are removed
  - [ ] A card with `min_credit_score=725` is removed when `person1.credit_score_band = "fair"` (< 660)
  - [ ] In couple mode, a card is retained if either person qualifies individually
  - [ ] In couple mode, a card requiring `min_household_income=100000` is retained when combined income ≥ 100K
  - [ ] A card with `store_acceptance["costco_instore"] = False` is removed when the spending profile has Costco in-store spend
  - [ ] At least one card remains after filtering for the 5 seed cards and a reasonable test profile (credit score 725+, income $80K)
  - [ ] pytest coverage ≥ 80% on `eligibility.py`

---

### TASK-006: Spend Bucket Normalizer and Dummy Card Builder

- **Status**: Done (2026-04-17)
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-003, TASK-004
- **Context**: `SpendBucketNormalizer` converts the user's `SpendingProfile` (category + store spend dicts + Chexy) into a flat list of `SpendBucket` objects. `DummyCardBuilder` converts user-defined dummy cards into `CardRecord` objects. Both are described in TDD Section 2.2. The Chexy bucket is special: effective_rate = card_other_rate − 0.0175.
- **Description**: Implement `app/services/spend_normalizer.py` containing `SpendBucketNormalizer` and `DummyCardBuilder`. Normalizer must resolve each store slug to a category using `store_mcc_map`; unknown slugs default to "other" and are logged at `WARNING` level. Zero-amount buckets are excluded from the output list (they have no effect on the optimization and add variables unnecessarily).
- **Acceptance Criteria**:
  - [ ] A spending profile with grocery=$400, costco=$300, chexy_rent=$1500 produces 3 `SpendBucket` objects
  - [ ] Costco bucket has `resolved_category="wholesale"` and `store_slug="costco"`
  - [ ] Chexy bucket has `bucket_id="chexy_rent"` and `is_chexy=True`
  - [ ] A $0 amount for any category/store is excluded from the output (not added as a zero bucket)
  - [ ] `DummyCardBuilder` produces a `CardRecord` with `is_dummy=True`, `approval.min_credit_score=0`, and `approval.min_personal_income=0`
  - [ ] A dummy card with `base_rate=2.0` and no specific category rates uses 2.0% for all categories
  - [ ] pytest coverage ≥ 80% on `spend_normalizer.py`

---

### TASK-007: MILP Optimizer (Core Solve)

- **Status**: Done (2026-04-17)
- **Agent**: `data-pipeline`
- **Complexity**: High
- **Depends on**: TASK-005, TASK-006
- **Context**: `MILPOptimizer.solve()` implements the full MILP formulation from TDD Section 2.3: binary card-selection variables, continuous spend allocation variables, coverage constraint, card-selection linking, monthly cap constraints, store acceptance exclusions. PuLP 3.3.0 + CBC solver. 30-second time limit. Returns `OptimizationResult` with status, monthly/annual net reward, baseline comparison (2% flat), and row-level assignments.
- **Description**: Implement `app/services/optimizer.py` as `OptimizerBase` (ABC) + `MILPOptimizer` (concrete). The optimizer takes the pre-filtered card list and normalized spend buckets. It must correctly compute `effective_rate` using the store override resolution order from TDD Section 2.3. Annual fee prorated monthly. Baseline calculated as `sum(bucket.monthly_amount for bucket in buckets) * 0.02`.
- **Acceptance Criteria**:
  - [ ] With 5 seed cards and a test profile (grocery=$400, gas=$150, dining=$300, costco=$300), solve returns `status="optimal"` in under 5 seconds
  - [ ] CIBC Dividend is assigned to grocery spend (4% rate) when it is the highest eligible rate for grocery
  - [ ] Reward cap is correctly enforced: if CIBC Dividend has an $80/month grocery cap and monthly grocery spend is $400, only $80/$400 = $2000 eligible spend earns 4%, rest earns 1% (other rate or routed to next-best card)
  - [ ] Annual fee is correctly deducted: `card_summary[i].net_annual_value = estimated_annual_reward - annual_fee`
  - [ ] Chexy rent earns `card_other_rate - 0.0175` (net effective rate)
  - [ ] `status="infeasible"` when no cards are eligible (all filtered out)
  - [ ] `status="timeout"` when `MILP_TIME_LIMIT_SECONDS` is exceeded (testable with an artificially small limit)
  - [ ] `baseline_monthly_reward` equals 2% of total monthly spend
  - [ ] pytest coverage ≥ 80% on `optimizer.py`
- **Notes**: Benchmark the solve time after implementation — it should be under 2 seconds with 5 pre-filtered seed cards. Log solve time at `INFO` level.

---

### TASK-008: Explanation Generator

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-007
- **Context**: `ExplanationGenerator.explain(assignment, card, bucket, cards_considered)` produces a one-sentence English explanation for each `AssignmentRow`. Four explanation templates are defined in TDD Section 2.3: store override, category rate, cap-constrained split, Chexy. The explanations populate the "Why this card?" row expansion in the UI.
- **Description**: Implement `app/services/explainer.py`. The generator annotates each `AssignmentRow` with a populated `explanation` field. The explanation must reference the actual rate, category/store name, and card name — not generic text. Handle the cap-constrained split case where spend is split across two cards.
- **Acceptance Criteria**:
  - [ ] Grocery assigned to CIBC Dividend produces: "CIBC Dividend Visa Infinite earns 4.0% on grocery spending; no eligible card earns more in this category."
  - [ ] Shoppers Drug Mart assigned to CIBC Dividend (store override) produces: "CIBC Dividend Visa Infinite earns 4.0% at Shoppers Drug Mart — it is classified as grocery by CIBC and this is the highest rate among eligible cards."
  - [ ] Chexy rent row produces: "CARD earns X% on all purchases (other category); after Chexy's 1.75% fee, the net return on rent is Y%." where Y = X - 1.75
  - [ ] All explanation strings are non-empty for every `AssignmentRow` in the test optimization run
  - [ ] pytest coverage ≥ 80% on `explainer.py`

---

### TASK-009: SQLite Schema and Session Management

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Low
- **Depends on**: TASK-003
- **Context**: SQLite via SQLAlchemy 2.x stores optimization sessions (input + result JSON) with 24-hour TTL. Two tables: `optimization_sessions` and `households`. All tables have `user_id` and `household_id` columns (multi-tenant scaffold). Migration executed from `migrations/001_initial_schema.sql` at startup. Session ID is a UUID4 stored in an HttpOnly cookie.
- **Description**: Implement `app/models/session.py` (SQLAlchemy ORM model), `migrations/001_initial_schema.sql` (DDL), and session save/load/purge methods. The startup hook in `app/main.py` runs the migration if not already applied and purges expired sessions.
- **Acceptance Criteria**:
  - [ ] `OptimizationSession.save(db, session_id, input_json, result_json)` writes a row to `optimization_sessions`
  - [ ] `OptimizationSession.load(db, session_id)` returns the row or `None` if not found or expired
  - [ ] `OptimizationSession.purge_expired(db)` deletes all rows where `expires_at < now()`
  - [ ] Migration runs idempotently (no error if tables already exist)
  - [ ] `user_id` and `household_id` columns exist on both tables with defaults `"default"`
  - [ ] pytest coverage ≥ 80% on session management code

---

### TASK-010: Card Database Bulk Seeding Script

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-003, TASK-004
- **Context**: `scripts/seed_cards.py` is a one-time offline tool that scrapes PrinceOfTravel using `httpx` + `BeautifulSoup4` to extract card metadata and earn rates. It produces draft JSON records for human review — it does NOT write directly to `cards.json`. This is a maintenance script, not a runtime component. Target: extract draft records for 20+ additional cards beyond the 5 hand-curated seed cards.
- **Description**: Implement `scripts/seed_cards.py` with CLI arguments for a list of PrinceOfTravel card page URLs. For each URL: fetch the page, extract the JSON-LD block, parse earn rates from body text using regex, output a draft `CardRecord`-compatible dict. Flag `"source": "princeoftravel"` and `"confidence": "medium"` on all extracted records. Print draft JSON to stdout for human review; do not auto-merge.
- **Acceptance Criteria**:
  - [ ] Running `python scripts/seed_cards.py --urls https://princeoftravel.com/credit-cards/american-express-cobalt-card/` produces a valid draft `CardRecord` JSON to stdout
  - [ ] Extracted `annual_fee` matches the value in the JSON-LD `offers.price` field
  - [ ] Earn rate regex captures patterns: "X× Category", "X% on Category", "up to $Y/month cap"
  - [ ] `last_verified_date` is set to today's date in YYYY-MM-DD format
  - [ ] Respects a 2-second delay between requests (configurable via CLI arg `--delay`)
  - [ ] Gracefully handles 404 or timeout on any URL (logs error, continues to next URL)
  - [ ] Output records are flagged with `"source": "princeoftravel"` — human review required before merging
- **Notes**: This script is NOT tested with pytest (it requires network access). It is documented in the README with usage instructions.

---

### TASK-011: Expanded Card Database (60+ Cards)

- **Status**: To Do
- **Agent**: `none — manual user process`
- **Complexity**: High
- **Depends on**: TASK-010
- **Context**: The card database must cover 60+ major Canadian credit cards to be meaningful for optimization. 5 cards exist after TASK-002. TASK-010 produces draft records for additional cards. This task is the human data-curation work: reviewing drafts, filling gaps from issuer pages, adding `store_overrides` per card, and merging into `cards.json`. Data accuracy is the entire value proposition — this task cannot be rushed.
- **Description**: Using the seeding script output from TASK-010 + direct issuer page research, expand `cards.json` to 60+ cards. Each card must have accurate: `category_rates`, `category_caps_monthly`, `store_overrides` (at minimum for Costco, Walmart, Shoppers Drug Mart), `approval` thresholds with correct `source` and `confidence`. Verify each record against the live issuer page.
- **Acceptance Criteria**:
  - [ ] `cards.json` contains ≥ 60 `CardRecord` entries
  - [ ] Coverage includes cards from all major issuers: TD, RBC, Scotiabank, CIBC, BMO, Amex, PC Financial, Rogers, Canadian Tire, Capital One
  - [ ] Every card has `last_verified_date` set to within the last 30 days of this task's completion
  - [ ] Every card with a grocery earn rate has a `store_override` entry for Costco (rate = 1% or card's "other" rate) with `note` explaining the wholesale classification
  - [ ] All records pass `CardRecord.model_validate()` without errors
  - [ ] `JsonCardDatabaseLoader` loads all records successfully at startup
- **Notes**: Prioritize cards that commonly appear in r/churningcanada optimization discussions: Scotiabank Gold Amex, Amex Cobalt, TD First Class Travel, CIBC Aventura, RBC Avion Visa Infinite, PC Financial World Elite, Rogers World Elite.

---

## Phase 2: Web UI

### TASK-012: FastAPI Application Bootstrap and Routes

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-009
- **Context**: `app/main.py` creates the FastAPI application, registers routers, runs startup hooks (migration, expired session purge, card database load), and configures the Jinja2 template engine. Three routers: `input.py` (GET /, POST /optimize), `results.py` (GET /results/{session_id}), `export.py` (GET /export/{session_id}). See TDD Section 2.5.
- **Description**: Implement `app/main.py` and the three router files as stubs (returning placeholder responses). Set up Jinja2 `TemplateResponse` patterns. Configure static file serving for `app/static/`. Register the startup event for DB migration and session purge. Wire the `CardDatabaseLoader` as a FastAPI dependency.
- **Acceptance Criteria**:
  - [ ] `uvicorn app.main:app --reload` starts without errors
  - [ ] `GET /` returns HTTP 200
  - [ ] `GET /results/nonexistent-session` returns HTTP 302 redirect to `/` with a session-expired flash message
  - [ ] `GET /export/nonexistent-session` returns HTTP 302 redirect to `/`
  - [ ] Card database is loaded at startup and accessible via `CardDatabaseLoader` dependency
  - [ ] SQLite migration runs at startup without error
  - [ ] `logging` is configured at the level from `LOG_LEVEL` env var

---

### TASK-013: Input Page — Spending Form

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: High
- **Depends on**: TASK-012
- **Context**: The Input Page is defined in the UX-SPEC wireframe and TDD Section 2.5. It has five sections: Standard category spending (collapsible groups), "Stores with Non-Obvious Classifications" sub-section (keystone UX element), Settings panel (collapsed by default), Dummy Cards panel (collapsed by default), Current Cards panel (for Feature 2 delta). Form submits to `POST /optimize`.
- **Description**: Implement `app/templates/input.html` and `app/templates/base.html`. The spending category groups and "Stores with Non-Obvious Classifications" section must match the UX-SPEC exactly (labels, help text/tooltips, collapsible group headers). Settings panel contains: Amex toggle, credit score dropdown, income dropdown, couple mode toggle (reveals Person 2 fields), Chexy toggle (reveals rent amount field). Dummy Cards panel has "+ Add dummy card" that reveals a card definition form. Current Cards panel has a multi-select from the card database (for Feature 2). Session pre-population: if a session cookie is present and the session has input data, pre-populate all fields.
- **Acceptance Criteria**:
  - [ ] All 19 standard categories from PRD Section 4 are present as input rows
  - [ ] The "Stores with Non-Obvious Classifications" section contains all 8 stores (Costco, Walmart, Shoppers Drug Mart, Canadian Tire, Loblaws/PC, Amazon Canada, LCBO, Lowe's) with classification tooltips
  - [ ] Costco row displays tooltip: "Classified as Wholesale/Warehouse, not Grocery — Mastercard only in-store"
  - [ ] Settings panel is collapsed by default and expands on click
  - [ ] Couple mode toggle reveals Person 2 credit score and income dropdowns
  - [ ] Chexy toggle reveals monthly rent amount field
  - [ ] Dummy Cards panel is collapsed by default; "+ Add dummy card" button reveals a card definition form with name, annual fee, base rate, and per-category rate fields
  - [ ] Current Cards panel has a multi-select populated with card names from the database (for Feature 2)
  - [ ] Form submits to `POST /optimize` via standard HTML form POST (no JavaScript required for form submission)
  - [ ] Returning from the Results page pre-populates all fields from session state
  - [ ] Non-numeric input in a spend field shows an inline validation error

---

### TASK-014: `POST /optimize` Route — Full Pipeline Integration

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: High
- **Depends on**: TASK-007, TASK-008, TASK-012, TASK-013
- **Context**: The `POST /optimize` handler is the integration point for the full pipeline: form parsing → Pydantic validation → eligibility filter → spend normalization → MILP solve → explanation generation → session save → redirect to Results page. The redirect pattern (POST → redirect → GET) prevents form resubmission on browser refresh.
- **Description**: Implement the `POST /optimize` handler in `app/routers/input.py`. Parse the HTML form fields into a `SpendingProfile`. Run the full pipeline: `EligibilityFilter` → `SpendBucketNormalizer` → `MILPOptimizer` → `ExplanationGenerator`. Save the result to SQLite. Set a session ID cookie (UUID4, HttpOnly, SameSite=Lax). Redirect to `GET /results/{session_id}`.
- **Acceptance Criteria**:
  - [ ] POST with a valid spending form redirects to `/results/{session_id}` with HTTP 302
  - [ ] A session ID cookie is set (HttpOnly, SameSite=Lax)
  - [ ] The session record in SQLite contains the serialized `SpendingProfile` and `OptimizationResult`
  - [ ] POST with all-zero spend amounts returns HTTP 422 with form-level error rendered in `input.html`
  - [ ] POST with couple mode enabled and no Person 2 profile returns HTTP 422 with field-level error
  - [ ] Solve time is logged at `INFO` level: "Optimization completed in X.XXs (status: optimal, cards evaluated: N)"
  - [ ] The full pipeline runs end-to-end in under 15 seconds for a profile with 60+ cards and 20 spend buckets

---

### TASK-015: Results Page

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-014
- **Context**: The Results Page is specified in the UX-SPEC wireframe and TDD Section 2.5. It renders the `OptimizationResult` from the session. Components: summary banner, assignment table (sortable, expandable "Why this card?" rows), card summary panel, "Export" button, "Adjust inputs" link. Couple mode adds a "Cardholder" column. The baseline comparison (2% flat) appears in the summary banner.
- **Description**: Implement `app/templates/results.html`. The assignment table renders one row per `AssignmentRow` with a `<details>/<summary>` collapse for the "Why this card?" explanation. Card summary panel shows each selected card's fee, assigned categories, estimated annual reward, and net annual value. The summary banner compares actual vs. 2% flat baseline. The "No eligible cards" empty state and the infeasibility/timeout warning banners must be implemented.
- **Acceptance Criteria**:
  - [ ] Summary banner shows total monthly reward and annual net reward after all annual fees
  - [ ] Summary banner shows baseline comparison: "A 2% flat cash-back card would earn ~$X/month. Your recommended setup earns $Y/month — $Z/month more."
  - [ ] Assignment table has all five columns: Category/Store | Assigned Card | Estimated Monthly Expense | Reward % | Expected Monthly Reward
  - [ ] Each assignment row has an expandable "Why this card?" section using `<details>/<summary>` (no JavaScript required)
  - [ ] Card summary panel has one row per selected card with correct `net_annual_value` displayed
  - [ ] In couple mode, assignment table includes a "Cardholder" column (Person 1 / Person 2)
  - [ ] "No eligible cards" state renders correctly when `result.status == "infeasible"`
  - [ ] Timeout warning banner renders when `result.status == "timeout"`
  - [ ] "Adjust inputs" link navigates to `GET /?session={session_id}` and the form is pre-populated
  - [ ] Page renders correctly for the 5-card test database with a representative spending profile

---

## Phase 3: Feature 2 — Delta Calculator

### TASK-016: Delta Calculator Service

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-007
- **Context**: `DeltaCalculator` calls `MILPOptimizer.solve()` twice — once with the eligible pool constrained to the user's current cards, once with the full eligible pool. Returns a `DeltaResult` model containing both solve results and the delta figure. This is the commercial-signal instrument described in the PRD.
- **Description**: Implement `app/services/delta.py`. The constrained solve forces `y[c, p] = 0` for all cards not in `current_card_ids`. If `current_card_ids` is empty, the constrained result is `current_annual_reward = 0`. Log both solve times at `INFO` level.
- **Acceptance Criteria**:
  - [ ] With `current_card_ids = ["cibc_dividend_vi"]` and a grocery-heavy spending profile, `current_annual_reward` reflects only what CIBC Dividend earns
  - [ ] `optimal_annual_reward` matches the result from `MILPOptimizer.solve()` without constraints
  - [ ] `delta_annual = optimal_annual_reward - current_annual_reward`
  - [ ] With empty `current_card_ids`, `current_annual_reward = 0.0`
  - [ ] Both solves complete within the `MILP_TIME_LIMIT_SECONDS` limit
  - [ ] `DeltaResult` is serializable to JSON (for SQLite session storage)
  - [ ] pytest coverage ≥ 80% on `delta.py`

---

### TASK-017: Delta Results UI Integration

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-015, TASK-016
- **Context**: The Results page must display the delta comparison when `current_card_ids` were provided. The delta section sits between the summary banner and the assignment table. It shows: current annual reward, optimal annual reward, and the delta ($Z improvement). This is the primary shareability hook described in the PRD and MARKET-ANALYSIS.
- **Description**: Update `app/routers/input.py` `POST /optimize` handler to call `DeltaCalculator` when `current_card_ids` is non-empty. Update `app/templates/results.html` to render the delta section when `DeltaResult` is present in the session. The delta figure should be visually prominent (large, clear "You could earn $Z more per year" statement).
- **Acceptance Criteria**:
  - [ ] When current cards are selected on the input page, the results page shows a delta section with three figures: current annual reward, optimal annual reward, delta
  - [ ] When no current cards are selected, the delta section is absent (no empty state)
  - [ ] The delta figure is rendered prominently — larger text, clearly differentiated from the assignment table
  - [ ] If `delta_annual = 0` (current setup is already optimal), the delta section reads: "Your current card setup is already optimal for your spending profile."
  - [ ] If `delta_annual < 0` (edge case: current setup beats optimizer — should not happen unless current cards were filtered differently), a warning is shown
  - [ ] Delta calculation adds no more than 10 seconds to the total solve time

---

## Phase 4: Spreadsheet Export and Polish

### TASK-018: Spreadsheet Exporter

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-007
- **Context**: `SpreadsheetExporter.generate(result, input_profile)` produces a four-tab `.xlsx` file using openpyxl 3.1.5. Four tabs per TDD Section 2.5 and UX-SPEC Section Touchpoint 7: Summary, Calculation Detail, Cards Considered, Input Echo. File is named `credit-card-optimization-YYYY-MM-DD.xlsx`. Served as a streaming download.
- **Description**: Implement `app/services/exporter.py`. Tab 1 (Summary): the assignment table from the web page. Tab 2 (Calculation Detail): one row per category/store × card considered, with all intermediate values (base rate, override rate, cap applied, cap amount, effective rate, monthly reward, annual reward, annual fee portion, net annual contribution). Tab 3 (Cards Considered): all eligible cards with key attributes. Tab 4 (Input Echo): the exact spending amounts and settings entered. Write the tool URL in cell A1 of the Input Echo tab.
- **Acceptance Criteria**:
  - [ ] `SpreadsheetExporter.generate(result, input_profile)` returns a `BytesIO` object that openpyxl can verify as a valid `.xlsx`
  - [ ] The file has exactly 4 tabs: Summary, Calculation Detail, Cards Considered, Input Echo
  - [ ] Tab 2 (Calculation Detail) has one row per (category/store × card) pair — not just the selected card, but every eligible card considered
  - [ ] Tab 4 (Input Echo) contains all spending amounts and settings from the `SpendingProfile`
  - [ ] Cell A1 of Tab 4 contains the tool's URL (configurable via env var)
  - [ ] The `GET /export/{session_id}` route streams the file with correct `Content-Disposition: attachment; filename="credit-card-optimization-YYYY-MM-DD.xlsx"` header
  - [ ] Export works for the delta result case (includes both current and optimal results)
  - [ ] pytest coverage ≥ 80% on `exporter.py`

---

### TASK-019: `GET /export/{session_id}` Route

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Low
- **Depends on**: TASK-018
- **Context**: The export route loads the session from SQLite, calls `SpreadsheetExporter`, and streams the result. Session not found → redirect to `/`. Export failure → inline error response (logged + 500).
- **Description**: Implement `GET /export/{session_id}` in `app/routers/export.py`. Load session, deserialize result, call `SpreadsheetExporter.generate()`, return `StreamingResponse` with correct MIME type and filename.
- **Acceptance Criteria**:
  - [ ] `GET /export/{valid_session_id}` returns HTTP 200 with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - [ ] `Content-Disposition` header is `attachment; filename="credit-card-optimization-YYYY-MM-DD.xlsx"`
  - [ ] `GET /export/{nonexistent_session_id}` returns HTTP 302 redirect to `/`
  - [ ] File downloads correctly in a browser (manual verification)
  - [ ] Export failure is caught, logged with full traceback, and returns HTTP 500 with a user-facing error message

---

### TASK-020: Custom Store Entry — Autocomplete and Classification

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Medium
- **Depends on**: TASK-013, TASK-014
- **Context**: The "+ Add a store" button in the input form allows users to enter any store name. The system looks up the store's MCC from the store_mcc_map; if found, shows a classification tag; if not found, shows "Classification unknown — using General retail" with an override dropdown. This is Touchpoint 2 in the UX-SPEC.
- **Description**: Implement the custom store entry flow. A JavaScript-free fallback must work (server-rendered classification lookup on form submission). Optional: add a lightweight JSON endpoint `GET /stores/lookup?name={store_name}` for client-side autocomplete. Classification override: a dropdown with standard category names (Grocery, Gas, Dining, Pharmacy, Other, etc.).
- **Acceptance Criteria**:
  - [ ] Submitting "Costco" in the custom store field shows a warning: "This store is already in the Stores with Non-Obvious Classifications section — we've handled its classification for you."
  - [ ] Submitting "T&T Supermarket" resolves to "Grocery" (MCC 5411, if in store_mcc_map) or "General retail" (if not)
  - [ ] Unknown store shows yellow "Classification unknown — using General retail" tag
  - [ ] Classification override dropdown contains all standard categories
  - [ ] Custom store spend is correctly included in the MILP solve as a spend bucket with the resolved or overridden category
  - [ ] Multiple custom stores can be added (no hard cap)

---

### TASK-021: Error Handling and Empty States

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Low
- **Depends on**: TASK-013, TASK-015
- **Context**: Error states are specified in the UX-SPEC Section "Error and Empty States" and TDD Section 6. All six error conditions must be rendered correctly: all-zero spend, backend failure, export failure, no eligible cards, no card beats 2% baseline, solver timeout.
- **Description**: Implement all error and empty states: (1) `app/templates/error.html` for backend failures, (2) form-level validation errors in `input.html`, (3) infeasibility/no-eligible-cards state in `results.html`, (4) timeout warning banner in `results.html`, (5) inline export failure message in `results.html`.
- **Acceptance Criteria**:
  - [ ] All-zero spend form submission shows inline error: "Enter at least one spending amount to see a recommendation."
  - [ ] Backend optimization failure renders `error.html` with a retry button and back link
  - [ ] `result.status == "infeasible"` renders the no-eligible-cards message in the results page assignment table area
  - [ ] `result.status == "timeout"` renders a warning banner above the assignment table
  - [ ] Export failure shows inline error below the export button without a page reload
  - [ ] "No cards beat 2% flat" state renders the warning banner replacing the normal summary banner

---

### TASK-022: Accessibility and CSS

- **Status**: To Do
- **Agent**: `data-pipeline`
- **Complexity**: Low
- **Depends on**: TASK-013, TASK-015
- **Context**: Accessibility requirements from UX-SPEC: keyboard tab order follows reading order; colour-blind-safe palette (no red/green alone — use + icon + text label); currency fields formatted on blur; accordion group headers. No mobile optimization required, but no catastrophic breakage on tablet.
- **Description**: Write `app/static/styles.css`. Implement `app/static/input.js` for: accordion collapse/expand on group headers, currency field formatting on blur (e.g., "400" → "$400.00"), percentage field formatting (e.g., "3" → "3.0%"). Ensure tab order is correct. Use semantic HTML elements in templates.
- **Acceptance Criteria**:
  - [ ] Tab key navigates through all spending input fields in reading order (top-to-bottom)
  - [ ] Currency fields display `$X.XX` on blur
  - [ ] Percentage fields display `X.X%` on blur
  - [ ] Group headers collapse/expand their content on click
  - [ ] Positive net_annual_value in card summary panel shows `+` prefix and green color + "+" text (not color alone)
  - [ ] Negative net_annual_value shows `−` prefix and red color + "−" text
  - [ ] Layout does not break on a 768px-wide viewport (tablet)

---

## Phase 5: Testing and Documentation

### TASK-023: Integration Tests — Full Pipeline

- **Status**: To Do
- **Agent**: `test-validator`
- **Complexity**: Medium
- **Depends on**: TASK-014, TASK-016
- **Context**: Unit tests cover individual services (Phases 1–4). Integration tests cover the full request lifecycle: form POST → optimizer pipeline → results render → export download. Use FastAPI's `TestClient`. Tests run against the actual 5-card seed database (TASK-002), not mocks.
- **Description**: Write `tests/test_routes.py` covering: (1) successful single-user optimization end-to-end, (2) successful couple-mode optimization, (3) delta calculation with current cards specified, (4) export download produces a valid `.xlsx`, (5) all-zero spend returns form validation error, (6) session expiry returns redirect.
- **Acceptance Criteria**:
  - [ ] Single-user optimization test: POST valid form → 302 redirect → GET results → 200 with assignment table present
  - [ ] Couple mode test: two eligibility profiles, assignment table includes "Cardholder" column
  - [ ] Delta test: current cards specified → delta section present in results with `delta_annual > 0`
  - [ ] Export test: GET /export/{session_id} → 200 → response body is valid `.xlsx` (verified by openpyxl `load_workbook`)
  - [ ] All-zero spend test: POST → 422 → error message present in response body
  - [ ] Session expiry test: GET /results/{expired_session} → 302 to `/`
  - [ ] Overall pytest coverage ≥ 80% across all modules (run `pytest --cov=app`)
- **Notes**: Do not mock the optimizer or the card loader. Use the real 5-card database and the real PuLP solver. If solve time in tests exceeds 30 seconds, reduce the test profile complexity.

---

### TASK-024: Performance Benchmark

- **Status**: To Do
- **Agent**: `test-validator`
- **Complexity**: Low
- **Depends on**: TASK-011, TASK-014
- **Context**: PRD success criterion: optimization returns in under 15 seconds for any valid profile. With 60+ cards (post TASK-011), the solve time must be verified against the full database. Benchmark at three scales: single user (60 cards, 20 buckets), couple mode (60 cards, 20 buckets, 2 persons), worst case (60 cards, 50 buckets, 2 persons).
- **Description**: Write `tests/test_performance.py`. Use `time.perf_counter()` around `MILPOptimizer.solve()`. Log results. Assert solve time < 15 seconds for all three scenarios.
- **Acceptance Criteria**:
  - [ ] Single user (60 cards, 20 buckets): solve time < 5 seconds
  - [ ] Couple mode (60 cards, 20 buckets): solve time < 10 seconds
  - [ ] Worst case (60 cards, 50 buckets, couple mode): solve time < 15 seconds
  - [ ] All three scenarios return `status = "optimal"` (not "timeout")
  - [ ] Benchmark results logged at `INFO` level with card count and bucket count

---

### TASK-025: README and Usage Documentation

- **Status**: To Do
- **Agent**: `content-writer`
- **Complexity**: Low
- **Depends on**: TASK-022
- **Context**: The README must contain the "Built with Claude Code" line per CLAUDE.md. It documents: what the tool does (one paragraph), how to set it up (virtual environment, .env, database), how to run it (uvicorn command), how to use the seeding script, and how to update the card database.
- **Description**: Write `projects/credit-card-optimization/README.md` with sections: project description (with "Built with Claude Code" line directly below), setup instructions, running the app, using the card seeding script, updating card data, and a note on the methodology (honest optimizer, no affiliate bias).
- **Acceptance Criteria**:
  - [ ] `> Built with [Claude Code](https://claude.ai/code)` is present directly below the project description
  - [ ] Setup instructions include: `python -m venv .venv`, `pip install -r requirements.txt`, `cp .env.example .env`, `uvicorn app.main:app --reload`
  - [ ] Card seeding script usage is documented with an example URL
  - [ ] Card database update procedure is documented (edit `data/cards/cards.json`, verify with `python -c "from app.services.card_loader import JsonCardDatabaseLoader; ..."`)
  - [ ] The methodology note explicitly states: no affiliate relationships, no issuer compensation, optimization is purely mathematical

---

### TASK-026: Security Review and Secrets Audit

- **Status**: To Do
- **Agent**: `architect`
- **Complexity**: Low
- **Depends on**: TASK-025
- **Context**: Pre-push security review per CLAUDE.md and TDD Section 5. Verify no secrets are committed, session cookies are correctly configured, input validation is in place, and no PII is stored.
- **Description**: Review all committed files for: (1) no API keys or tokens in any file, (2) `.env` is gitignored, (3) session cookie attributes are HttpOnly, SameSite=Lax, Secure flag documented for production, (4) all user inputs pass through Pydantic validators before reaching the optimizer, (5) no `print()` statements in production code, (6) no raw string paths (all use `pathlib.Path`).
- **Acceptance Criteria**:
  - [ ] `git grep -i "secret\|token\|api_key\|password"` returns no results in committed files (except `.env.example` with placeholder values)
  - [ ] `.gitignore` excludes `.env`, `*.db`, `.venv/`
  - [ ] Session cookie is set with `httponly=True`, `samesite="lax"` in all `Response.set_cookie()` calls
  - [ ] No `print()` statements in any file under `app/`
  - [ ] No string path concatenation — all file paths use `pathlib.Path`
  - [ ] MILP solver time limit is enforced (`timeLimit=MILP_TIME_LIMIT_SECONDS`)
  - [ ] Verdict: PASS or FAIL WITH NOTES — document any findings in a comment on this task

---

### TASK-027: Phase-Gate Review — Implementation → Testing

- **Status**: To Do
- **Agent**: `architect`
- **Complexity**: Low
- **Depends on**: TASK-023, TASK-024, TASK-026
- **Context**: Architect phase-gate review before marking the PoC as ready for personal use. Checks: all tasks done, implementation matches TDD, PRD success criteria met, security review passed, README complete.
- **Description**: Review TASKS.md (all tasks Done), run `pytest --cov=app` and verify ≥80% coverage, verify PRD success criteria against working app, verify README compliance. Produce a written verdict: PASS / PASS WITH NOTES / FAIL with specific items.
- **Acceptance Criteria**:
  - [ ] All TASK-001 through TASK-026 are marked Done
  - [ ] `pytest --cov=app` shows ≥80% coverage on all `app/` modules
  - [ ] All 6 PRD success criteria are demonstrably met (tested manually or via integration tests)
  - [ ] TASK-026 security review verdict is PASS or PASS WITH NOTES (no FAIL items outstanding)
  - [ ] README contains "Built with Claude Code" line
  - [ ] Architect writes a final verdict comment on this task

---

## Completed Tasks Log

<!-- Move completed tasks here with completion date -->
