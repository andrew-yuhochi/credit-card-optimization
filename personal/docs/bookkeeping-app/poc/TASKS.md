# Task Breakdown — Bookkeeping App

> **Status**: Active
> **Last Updated**: 2026-04-15
> **Depends on**: PRD.md (approved), TDD.md (approved), DATA-SOURCES.md (approved)

---

## Progress Summary

| Status | Count |
|--------|-------|
| Done | 22 |
| In Progress | 0 |
| Not Started | 5 |
| Blocked | 0 |

---

## Sprint 1: Scaffolding & Data Foundation

### TASK-001: Project Scaffolding and Repository Initialization
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Low
- **Depends on**: None
- **Context**: First task per the CLAUDE.md task-completion checklist — creates the GitHub repo under `andrew-yuhochi`, sets up the Python venv and project directory structure per `docs/STRUCTURE.md`, writes the README with the mandatory "Built with Claude Code" line.
- **Description**: Initialize the `bookkeeping-app` project directory with the standard Python project structure. Create `pyproject.toml` or `requirements.txt` with pinned dependencies. Set up `venv`. Create `README.md` with the "Built with Claude Code" line directly below the project description. Create `.env.example` with all required environment variable placeholders. Create `.gitignore`. Create the GitHub repo under `andrew-yuhochi/bookkeeping-app` and push the initial commit.
- **Acceptance Criteria**:
  - [ ] `projects/bookkeeping-app/` exists with the standard directory structure (see `docs/STRUCTURE.md`)
  - [ ] `requirements.txt` pins: fastapi, uvicorn, pdfplumber, scikit-learn, pydantic, sqlalchemy, alembic, openpyxl, httpx, jinja2, python-multipart, ruff, pytest
  - [ ] `venv` created and activatable
  - [ ] `README.md` contains `> Built with [Claude Code](https://claude.ai/code)` directly below the project description
  - [ ] `.env.example` documents `DATABASE_URL`, `HOUSEHOLD_ID`, `SECRET_KEY`, `BOC_VALET_BASE_URL`
  - [ ] `.gitignore` excludes `.env`, `*.db`, `__pycache__`, `venv/`, `*.pkl`
  - [ ] GitHub repo `andrew-yuhochi/bookkeeping-app` created and initial commit pushed
- **Notes**: This task exists to satisfy the CLAUDE.md GitHub Rule #2 (create remote on first task completion). No application logic is implemented here.

---

### TASK-002: Database Schema, Alembic Migrations, and Seed Categories
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-001
- **Context**: Implements TDD Section 4.1 (full logical schema) and 4.2 (categories.yaml seed). All six Section 2A architectural constraints are encoded here: multi-tenant tables with `household_id`, `household_tier` + `tax_context` on categories, per-person `budget_envelopes`, `split_method` column on transactions, `exact_match_cache` table, `corrections` table.
- **Description**: Define all SQLAlchemy 2.x ORM models in `db/models.py`. Write the initial Alembic migration. Create `config/categories.yaml` with all 11 expense + 4 income categories including `household_tier`, `tax_context`, `default_split`, and `sort_order`. Write `scripts/seed_categories.py` to insert the canonical categories and create the default household + two users (Andrew and Kristy) from `config/`.
- **Acceptance Criteria**:
  - [ ] All tables from TDD Section 4.1 exist in the migration: `households`, `users`, `categories`, `budget_envelopes`, `statements`, `transactions`, `corrections`, `exact_match_cache`, `parse_errors`
  - [ ] Every table has a `household_id` UUID foreign key
  - [ ] `categories` table has `household_tier` (`household | personal_pocket | shared_discretionary`) and `tax_context` (`taxable | pre_tax | tax_sheltered`) columns
  - [ ] `transactions` table has `split_method`, `andrew_amount`, `kristy_amount`, `accounting_period_year`, `accounting_period_month`, `accounting_period_is_override`, `fx_rate_source`, `classifier_source`, `needs_review` columns
  - [ ] `config/categories.yaml` contains all 15 categories (11 expense + 4 income) with all required fields
  - [ ] `scripts/seed_categories.py` runs idempotently against a fresh SQLite DB and inserts correct data
  - [ ] `alembic upgrade head` on a fresh database produces the complete schema
  - [ ] All monetary columns are `NUMERIC(18,4)` — no REAL/FLOAT for money
- **Notes**: Use `CHAR(1)` for `users.person_code` ("A" / "K"), not hardcoded names, to satisfy 2A-1.

---

### TASK-003: Historical Seed Data Import
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-002
- **Context**: Imports `Income_Expense_updated.xlsx` (1,790 expense rows + 140 income rows + budget envelopes) as the classifier seed corpus and baseline transaction history. See DATA-SOURCES.md Source 5 for sheet-by-sheet strategy. Column names must be confirmed against the real file before implementation begins.
- **Description**: Write `scripts/seed_import.py` to import three sheets from `Income_Expense_updated.xlsx`: `Expense - Expense` (transactions), `Income - 表格 1` (income transactions), `Planning - Monthly` (budget envelopes). Use openpyxl. Map to the `transactions` and `budget_envelopes` tables. Set `source = "historical_import"` on all imported transactions. Use upsert with `source_ref = "historical:{sheet}:{row_index}"` for idempotency.
- **Acceptance Criteria**:
  - [ ] Script runs idempotently — running twice does not create duplicate rows
  - [ ] At least 1,700 expense transactions imported (allow for a small number of blank/header rows)
  - [ ] At least 130 income transactions imported
  - [ ] Budget envelopes imported for both users for at least the 2025 and 2026 periods
  - [ ] All imported transactions have `source = "historical_import"` and `accounting_period_year` / `accounting_period_month` populated from the date column
  - [ ] `split_method` values are exactly `"A"`, `"K"`, or `"A/K"` — no variants
  - [ ] Script prints a summary on completion: rows imported, rows skipped (duplicate), rows failed
- **Notes**: Before implementing, print all column names in the three sheets using `openpyxl` and confirm against the expected names in DATA-SOURCES.md. If column names differ, update the mapping config accordingly.

---

### TASK-004: IssuerParser Interface and ParserRegistry
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Low
- **Depends on**: TASK-001
- **Context**: Implements TDD Section 2.1 — the `IssuerParser` ABC and `ParserRegistry` that dispatches to the correct per-issuer parser. This is Architectural Constraint 2A-3 (per-issuer parser plugin interface and open-banking migration path). No real parsing logic here — only the interface and registry.
- **Description**: Create `parsers/base.py` with the `IssuerParser` ABC defining `issuer_name: str`, `detect(filename, first_page_text) → bool`, and `parse(pdf_bytes) → list[ParsedTransaction]`. Create `parsers/registry.py` with a `ParserRegistry` class that holds a list of registered parsers, provides `detect_issuer(filename, pdf_bytes)`, and dispatches to the correct parser. Create `ParsedTransaction` Pydantic model in `parsers/models.py`. Create `config/issuer_rules.yaml` with placeholder entries.
- **Acceptance Criteria**:
  - [ ] `IssuerParser` is an ABC with abstract methods `detect` and `parse`; `issuer_name` is a class attribute
  - [ ] `ParserRegistry.detect_issuer()` returns the correct `IssuerParser` instance or raises `UnknownIssuerError`
  - [ ] `ParsedTransaction` Pydantic model matches the TDD Section 3 contract: `issuer`, `cash_date`, `description`, `original_amount`, `original_currency`, `fx_rate`, `fx_rate_source`, `cad_amount`, `statement_page`
  - [ ] Unit tests: registry with two mock parsers correctly dispatches to the matching one
  - [ ] Adding a new parser requires only creating a new subclass and appending to `REGISTERED_PARSERS` — no other changes
- **Notes**: The `parse()` method signature accepts `pdf_bytes: bytes`. This is also the future open-banking migration point (TDD 2.1).

---

### TASK-005: ClassifierClient Interface and OfflineClassifierClient Skeleton
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-002
- **Context**: Implements TDD Section 2.2 — the `ClassifierClient` ABC from RESEARCH-REPORT-v2 Section 1.3 and the `OfflineClassifierClient` concrete implementation. This is Architectural Constraint 2A-4. The OfflineClassifierClient in this task is a skeleton — it returns `needs_review=True` for everything until TASK-006 trains the real model.
- **Description**: Create `classifier/base.py` with the full `ClassifierClient` ABC, `Transaction` dataclass, `ClassificationResult` dataclass, and `SplitMethod` literal type — exactly as specified in RESEARCH-REPORT-v2 Section 1.3. Create `classifier/offline.py` with `OfflineClassifierClient` implementing all four abstract methods. In this task, `classify()` returns a stub result with `confidence=0.0`, `needs_review=True`, `source="stub"`. The `retrain()` method is a no-op returning an empty dict. Write unit tests verifying the ABC contract.
- **Acceptance Criteria**:
  - [ ] `ClassifierClient` ABC is in `classifier/base.py` with all four abstract methods: `classify`, `classify_batch`, `update_from_correction`, `retrain`; plus `is_online` abstract property
  - [ ] `OfflineClassifierClient.is_online` returns `False`
  - [ ] `OfflineClassifierClient` can be instantiated and called without error
  - [ ] No module outside `classifier/` imports `TfidfVectorizer`, `LogisticRegression`, or `pickle` — enforced by a ruff rule or explicit grep test
  - [ ] Unit test: calling `classify()` on a `Transaction` returns a `ClassificationResult` — stub values are fine at this stage
- **Notes**: The `Transaction` and `ClassificationResult` dataclasses must be `frozen=True` (as in RESEARCH-REPORT-v2). External callers import only from `classifier.base`.

---

## Sprint 2: Core ML Pipeline

### TASK-006: Merchant Normalization and Exact-Match Cache (Layer 1)
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-003, TASK-005
- **Context**: Implements TDD Section 2.2 Layer 0 (preprocessing) and Layer 1 (exact-match cache). After TASK-003, the historical seed data is in the DB — this task builds the normalization pipeline and populates the exact-match cache from it.
- **Description**: Implement merchant normalization in `classifier/normalizer.py`: lowercase, strip branch/store IDs (regex), strip province codes and city name trailing patterns, strip card-network noise ("PURCHASE", "POS", "PAYMENT", "AUTHORIZATION"). Implement the `ExactMatchCache` in `classifier/cache.py` backed by the `exact_match_cache` DB table. Populate the cache from the historical seed data (normalized merchant → most-frequent (category, split_method) pair). Wire the cache as Layer 1 inside `OfflineClassifierClient.classify()`.
- **Acceptance Criteria**:
  - [ ] Normalization function is deterministic: same input always produces same output
  - [ ] "STARBUCKS #1234 TORONTO ON" and "STARBUCKS 5678 OTTAWA" normalize to the same key
  - [ ] "PURCHASE AUTHORIZATION LOBLAWS 0042 TORONTO ON" normalizes to "loblaws"
  - [ ] Cache lookup returns `confidence=1.0`, `source="cache"` on a hit
  - [ ] Cache is populated with at least 100 distinct normalized merchants from the historical seed data
  - [ ] Cache hit rate on the historical seed data is ≥60% (measure and log)
  - [ ] Unit tests cover normalization edge cases: empty string, Chinese characters (pass-through), amounts in description
- **Notes**: The cache write gate (only write for merchants with <3 prior confirmed labels, or when a correction is confirmed 3+ times) is implemented in TASK-010, not here. In this task, populate from seed data without the gate.

---

### TASK-007: TF-IDF + Logistic Regression Classifier (Layer 2)
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-006
- **Context**: Implements TDD Section 2.2 Layer 2 — TF-IDF (unigram + bigram, max_features=5000) + LogisticRegression trained on the historical seed corpus. This is the primary ML classification layer for novel merchants not in the cache.
- **Description**: Implement the TF-IDF + LR training loop inside `OfflineClassifierClient`. The `retrain()` method queries the DB for all seed rows UNION all corrections rows, normalizes merchant strings, trains a `TfidfVectorizer` + `LogisticRegression` pipeline end-to-end, serializes the model to `classifier/models/model.pkl`, and returns a metrics dict. Wire Layer 2 into `classify()`: if Layer 1 cache miss, call the LR model, set `needs_review` based on confidence thresholds (≥0.70 → False with optional dot flag in UI, <0.70 → True).
- **Acceptance Criteria**:
  - [ ] `retrain()` completes in <5 seconds on the 1,790-row seed corpus on a MacBook M-series
  - [ ] `retrain()` returns `{"rows_trained": int, "held_out_accuracy": float, "duration_seconds": float}` with `held_out_accuracy ≥ 0.70` on a 20% hold-out split of the seed data
  - [ ] `classify()` after `retrain()` returns a `ClassificationResult` with `source="tfidf_lr"` and `0 < confidence < 1.0` for a novel merchant not in the cache
  - [ ] Confidence thresholds: `confidence ≥ 0.70` → `needs_review=False`; `< 0.70` → `needs_review=True`
  - [ ] Model serializes to `classifier/models/model.pkl` (~400–600 KB)
  - [ ] `retrain()` is thread-safe: a new model is trained in memory and swapped atomically; calls to `classify()` during retraining continue to use the old model
  - [ ] The separate responsibility LR classifier is also trained in `retrain()` on the same corpus using `split_method` labels
- **Notes**: Use `scikit-learn==1.8.0`, `solver="lbfgs"`, `multi_class="multinomial"`. No `partial_fit`. Train both a category classifier and a responsibility classifier in the same `retrain()` call.

---

### TASK-008: FX Client — BoC Valet API Integration
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Low
- **Depends on**: TASK-001
- **Context**: Implements TDD Section 2.3 — the `FXClient` wrapping the BoC Valet API for HKD → CAD daily-average fallback rates. See DATA-SOURCES.md Source 6 for the confirmed live endpoint and sample response.
- **Description**: Create `fx/boc_client.py` with `FXClient`. Implement `get_daily_average(currency: str, period_year: int, period_month: int) -> Decimal`. Fetch daily observations for the requested month from `https://www.bankofcanada.ca/valet/observations/FX{currency}CAD/json?start_date=...&end_date=...`. Average non-null values. Cache the result in-process per `(currency, period_year, period_month)`. Add 1-second sleep between distinct HTTP calls. Raise `FXRateNotAvailableError` if the API returns no data.
- **Acceptance Criteria**:
  - [ ] `FXClient.get_daily_average("HKD", 2026, 3)` returns a `Decimal` value close to 0.1755 (within ±5% of the known rate)
  - [ ] Response is cached: calling the same `(currency, period)` twice makes only one HTTP request
  - [ ] If the API returns an HTTP error: raises `FXRateNotAvailableError` with a descriptive message
  - [ ] The courtesy 1-second sleep is implemented between distinct (non-cached) HTTP calls
  - [ ] Unit tests mock the HTTP call and verify the averaging logic (exclude null observations, correct arithmetic)
- **Notes**: Use `httpx` (async-capable) even though the FX client is called synchronously in the ingestion pipeline — easier future async migration.

---

### TASK-009: Transaction Normalizer and FX Resolution Pipeline
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-007, TASK-008
- **Context**: Implements TDD Section 2.3 — the `TransactionNormalizer` that converts `ParsedTransaction` objects into `Transaction` objects (for the classifier) and resolves FX rates. This is the bridge between parsing and classification.
- **Description**: Create `ingestion/normalizer.py` with `TransactionNormalizer`. Takes a `ParsedTransaction`, applies the FX resolution logic from TDD Section 2.3 (statement rate → BoC average → manual flag), calls merchant normalization, and returns a fully resolved `Transaction` ready for classification. Also determines `accounting_period_year` and `accounting_period_month` from `cash_date` (default: same month; no override logic at this stage — overrides are applied in the web layer).
- **Acceptance Criteria**:
  - [ ] CAD transactions: `cad_amount = original_amount`, `fx_rate = 1.0`, `fx_rate_source = "statement"`
  - [ ] HKD with parsed rate: `cad_amount = original_amount * fx_rate`, `fx_rate_source = "statement"`
  - [ ] HKD without parsed rate: calls `FXClient`, sets `fx_rate_source = "boc_average"`
  - [ ] USD transactions: `cad_amount = None`, `fx_rate_source = "manual"`, `needs_review = True`
  - [ ] `accounting_period_year` and `accounting_period_month` default to `cash_date.year` and `cash_date.month`
  - [ ] Unit tests for each currency path; FXClient is mocked

---

## Sprint 3: PDF Parsers

### TASK-010: MBNA Parser
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-004, TASK-009
- **Context**: First real issuer parser. MBNA is chosen first because it is the best-understood Canadian issuer and has the cleanest expected layout (standard Canadian Mastercard statement format). Implementing MBNA first establishes the parser-development workflow before tackling more complex issuers.
- **Description**: Implement `MBNAParser` in `parsers/mbna.py` implementing `IssuerParser`. Use `pdfplumber` to extract transaction rows from MBNA credit card PDF statements. Implement `detect()` using filename heuristic ("mbna") + first-page text signature. Implement `parse()` to return a `list[ParsedTransaction]`. Handle inline foreign-currency conversion lines (`USD X.XX converted at Y.YY = CAD Z.ZZ`).
- **Acceptance Criteria**:
  - [ ] `MBNAParser().detect("MBNA_2026-03.pdf", first_page_text)` returns `True`; returns `False` for MBNA-unrelated filenames
  - [ ] `parse(real_mbna_pdf_bytes)` returns at least 1 `ParsedTransaction` with correct date, description, and amount
  - [ ] Foreign-currency transactions have `fx_rate` and `original_currency` populated from the inline conversion block (if present)
  - [ ] Parse failure on one page does not crash the parser — partial results are returned and the failed page is recorded
  - [ ] Integration test with a real MBNA statement (anonymized if needed): row count matches Andrew's manual count
- **Notes**: Requires a real MBNA statement as a test fixture. Store as `tests/fixtures/mbna_sample.pdf`. Before implementing, examine the statement layout with `pdfplumber.open(path).pages[0].extract_text()` to confirm the column structure.

---

### TASK-011: Wealthsimple Parser
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-004, TASK-009
- **Context**: Wealthsimple issues both Cash (debit card) and Investment account statements with different layouts. The parser must detect which type it is dealing with.
- **Description**: Implement `WealthsimpleParser` in `parsers/wealthsimple.py`. The `detect()` method matches "wealthsimple" or "ws_" in filename and confirms with a first-page text signature. The `parse()` method branches on statement type (Cash vs. Investment) detected from a page-1 text marker. Implement both extraction paths.
- **Acceptance Criteria**:
  - [ ] `detect()` correctly identifies Wealthsimple files
  - [ ] `parse()` correctly distinguishes Cash account from Investment account statements
  - [ ] Integration test with a real Wealthsimple Cash statement: all transactions parsed with correct amounts
  - [ ] Integration test with a real Wealthsimple Investment statement (if available): buy/sell transactions parsed
  - [ ] Parse errors are isolated to the failing page — successful pages are returned

---

### TASK-012: Rogers Bank Parser
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-004, TASK-009
- **Context**: Rogers Bank Mastercard (newer entrant, 2022). Statement format follows the standard Canadian Mastercard template but must be confirmed from a real sample. Third parser in the sequence.
- **Description**: Implement `RogersParser` in `parsers/rogers.py`. Follow the same pattern as MBNA. Detect via filename ("rogers") + first-page text signature. Parse transaction rows with `pdfplumber`. Handle any foreign-currency conversion blocks.
- **Acceptance Criteria**:
  - [ ] `detect()` correctly identifies Rogers Bank files
  - [ ] Integration test with a real Rogers statement: all transactions parsed with correct amounts
  - [ ] Foreign-currency transactions flagged correctly (either parsed rate or `needs_review=True`)
  - [ ] Parse errors isolated per page

---

### TASK-013: Full Ingestion Pipeline Integration
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-010, TASK-011, TASK-012
- **Context**: Wires together the parser registry, normalizer, FX client, and classifier into a single `IngestionPipeline.ingest(pdf_bytes, filename) → IngestionResult`. This is the callable surface the FastAPI upload route will use.
- **Description**: Create `ingestion/pipeline.py` with `IngestionPipeline`. The `ingest()` method: detects issuer via registry, parses, normalizes (FX resolution), classifies via `ClassifierClient.classify_batch()`, detects duplicates, writes to DB (`statements` + `transactions` rows). Returns an `IngestionResult` with counts (parsed, classified, flagged, duplicates, errors).
- **Acceptance Criteria**:
  - [ ] `ingest()` called with a real MBNA PDF produces correct DB rows
  - [ ] Duplicate transactions (same date + amount + merchant + issuer) are skipped on re-upload
  - [ ] `needs_review=True` transactions appear in the DB with the correct flag
  - [ ] A parse error on one page does not prevent other pages from being ingested
  - [ ] `classifier.base.ClassifierClient` is the only classifier symbol imported in this module

---

## Sprint 4: Web Application — Core

### TASK-014: FastAPI Application Scaffolding and Base Templates
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-002
- **Context**: Creates the FastAPI app, Jinja2 template configuration, HTMX integration, and the left-sidebar navigation layout. This is the structural scaffolding all other web tasks build on.
- **Description**: Create `api/main.py` (FastAPI app), `api/dependencies.py` (DB session, ClassifierClient injection), `api/routes/` (one file per route group). Set up Jinja2 templates in `templates/`. Create `templates/base.html` with the left-sidebar navigation (month selector, Overview, Upload, Needs Review with badge count, all 11 expense + 4 income category entries, Settings). Include HTMX 2.x and Sortable.js via CDN `<script>` tags. Implement a basic health-check route `GET /health`.
- **Acceptance Criteria**:
  - [ ] `uvicorn api.main:app --reload` starts without error
  - [ ] `GET /health` returns `{"status": "ok"}`
  - [ ] `GET /` redirects to `/overview`
  - [ ] The base template renders with the full left-sidebar navigation (all 15 category links visible)
  - [ ] HTMX and Sortable.js are loaded (verify in browser DevTools)
  - [ ] The month selector in the sidebar is present (static for now — functional in TASK-018)
- **Notes**: Use `Accept`-header duality from TDD Section 2.5 (React migration path): routes that return HTML partials also return JSON when `Accept: application/json` is set.

---

### TASK-015: Upload Flow — File Upload and SSE Progress Stream
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: High
- **Depends on**: TASK-013, TASK-014
- **Context**: The primary value-delivery surface. Implements TDD Section 2.5 (upload route, SSE streaming) and UX-SPEC Touchpoint 1. The upload page accepts multi-file PDF drop, dispatches to the ingestion pipeline per file, and streams progress via SSE.
- **Description**: Implement `GET /upload` (upload page template) and `POST /upload` (accept PDF bytes, dispatch ingestion in a background task, return a session_id). Implement `GET /upload/status/{session_id}` as a FastAPI `StreamingResponse` SSE endpoint that emits progress events per file (`queued → parsing → classifying → done / error`). Handle the "unknown issuer" case (return a dropdown in the SSE event for the UI to render). Implement parse-failure and partial-parse display states.
- **Acceptance Criteria**:
  - [ ] Multi-file PDF drop on the upload page triggers `POST /upload` for each file
  - [ ] SSE stream emits at least these events per file: `{"status": "queued"}`, `{"status": "parsing"}`, `{"status": "classifying"}`, `{"status": "done", "parsed": N, "flagged": M}` or `{"status": "error", "message": "..."}`
  - [ ] A parse failure on one file does not stop SSE events for other files
  - [ ] After all files complete, the UI shows a "Continue to review →" button
  - [ ] The upload page has an app-wide drag-and-drop zone (not just the upload button area)
  - [ ] Duplicate files are reported as "N duplicates skipped" in the SSE event
  - [ ] **BLOCKER NOTE**: SIM HK parser (TASK-016) is not required for this task — the pipeline handles unknown-issuer gracefully. This task can proceed with MBNA, Wealthsimple, Rogers only.

---

### TASK-016: SIM HK Parser
- **Status**: Done (2026-04-16)
- **Agent**: data-pipeline (impl)
- **Complexity**: High
- **Depends on**: TASK-004, TASK-009
- **Context**: SIM HK is the highest-risk parser (DATA-SOURCES.md Source 4, RISK: HIGH). It is the product's primary commercial differentiator and must be done last among parsers to allow time to obtain a real statement. This task cannot begin until Andrew has provided a real SIM HK statement.
- **Description**: Implement `SIMHKParser` in `parsers/sim_hk.py`. The implementation approach depends entirely on the real statement format — which must be examined before writing any code. Expected: `pdfplumber` text extraction with bounding-box tuning for the observed layout. Handle bilingual content (Chinese + English merchant names) in normalization. Determine whether HKD → CAD rates appear inline per transaction or only as a monthly aggregate.
- **Acceptance Criteria**:
  - [ ] **PRE-CONDITION**: Andrew has provided a real SIM HK statement. Parser approach has been reviewed by the architect.
  - [ ] `detect()` correctly identifies SIM HK files
  - [ ] Integration test with a real SIM HK statement: all transactions parsed with correct HKD amounts
  - [ ] If per-transaction FX rate is available in the statement: `fx_rate` is populated and `fx_rate_source = "statement"`
  - [ ] If per-transaction FX rate is NOT available: `fx_rate = None` and the normalizer uses BoC fallback
  - [ ] Chinese-character merchant names are preserved in `description` and passed through normalization without encoding errors
  - [ ] Parse errors are isolated per page
- **Notes**: This is the last parser task deliberately. If the format is radically different from expectations (scanned, unusual structure), escalate to architect before proceeding.

---

## Sprint 5: Web Application — Review Surfaces

### TASK-017: Category Pages with Transaction Table and Per-Person Totals
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-014
- **Context**: Implements TDD Section 2.5 and UX-SPEC Touchpoint 4 — the most-visited surface in the app. One page per category showing the envelope bars, per-person totals, and the transaction table. Data is read from the DB filtered by `accounting_period`.
- **Description**: Implement `GET /category/{category_slug}` and `GET /income/{category_slug}` routes. Render `templates/category.html` with: envelope vs. actual progress bars for Andrew and Kristy, per-person totals in large type, transaction table (date, merchant, amount, split_method, confidence dot). Implement the confidence dot visual for 0.70–0.85 confidence transactions.
- **Acceptance Criteria**:
  - [ ] Each of the 11 expense category pages renders correctly with seed data
  - [ ] Each of the 4 income category pages renders correctly
  - [ ] Envelope bars show actual vs. envelope amounts; turn amber at 90%, red at 100% (with icon, not just color — colour-blind-safe per UX-SPEC)
  - [ ] Andrew total and Kristy total are displayed in large type above the table
  - [ ] Transactions are sorted by date descending by default
  - [ ] Transactions with confidence 0.70–0.85 show a gray dot in the category column
  - [ ] Empty category page shows the correct empty-state text (no emoji)
  - [ ] The month selector in the sidebar filters the displayed transactions by `accounting_period`

---

### TASK-018: Inline Responsibility Toggle (HTMX Partial)
- **Status**: Done (2026-04-16)
- **Agent**: data-pipeline (impl)
- **Complexity**: Low
- **Depends on**: TASK-017
- **Context**: Implements the inline responsibility toggle (A / K / A/K) on every transaction row. Clicking cycles the value and updates the row + page totals via HTMX OOB swap. Changes are held in server-side session state until "Save review session" is pressed.
- **Description**: Implement `POST /transactions/{id}/responsibility` route. Returns an updated `<tr>` partial for the transaction row (HTMX swap) and an OOB swap for the Andrew/Kristy total lines. Changes are stored in the server-side session (pending commit). Implement server-side session state (Python dict in a signed cookie or in-memory dict keyed by session token).
- **Acceptance Criteria**:
  - [ ] Clicking `A` on a row cycles to `K` without a full page reload
  - [ ] The Andrew and Kristy total lines update immediately after the toggle
  - [ ] The change is held in session state — a page refresh shows the toggled value
  - [ ] Three cycles in sequence: A → K → A/K → A (correct order per discovery)
  - [ ] Session state is not committed to the DB until "Save review session"

---

### TASK-019: Drag-to-Recategorize (Sortable.js + HTMX)
- **Status**: Done (2026-04-16)
- **Agent**: data-pipeline (impl)
- **Complexity**: High
- **Depends on**: TASK-017, TASK-018
- **Context**: Implements the keystone UX interaction (UX-SPEC Section "Keystone Interaction"). Drag a transaction row to a different category in the sidebar; totals on both pages update. TDD Section 2.5 specifies the Sortable.js + HTMX OOB swap pattern.
- **Description**: Implement `POST /transactions/{id}/move` route. Sortable.js on the transaction table fires a `fetch()` POST to this route on drop. Response includes `HX-Trigger` header to cause both the source and target category totals to refresh via HTMX OOB. Sidebar category highlights on hover during drag. Transaction disappears from current page. Toast appears: "Moved 'H-Mart' to Living Expense. [Undo]".
- **Acceptance Criteria**:
  - [ ] Dragging a transaction row onto a sidebar category link moves it to that category
  - [ ] The source category's Andrew and Kristy totals update within 200ms of drop (latency target from PRD NFR-7)
  - [ ] The sidebar category totals reflect the change (no full page reload)
  - [ ] A toast notification appears with the merchant name, target category, and an "Undo" button
  - [ ] "Undo" reverts the move (within the current session, before Save)
  - [ ] Dragging to the same category is a no-op (no toast, no DB change)
  - [ ] If the POST fails (network error), the transaction snaps back to its original row with an error toast
  - [ ] The move is held in session state, not committed to DB until Save

---

### TASK-020: Needs-Review Queue Page
- **Status**: Done (2026-04-17)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-017
- **Context**: Implements TDD Section 2.5 and UX-SPEC Touchpoint 5 — the queue of low-confidence transactions the classifier flagged for review. Keyboard-first interaction is the primary mode (J/K navigate, Enter accept, 1/2/3 pick alternate, A/K/S set responsibility).
- **Description**: Implement `GET /review` route and `templates/review_queue.html`. Show each flagged transaction with merchant, date, amount, statement source, classifier's top 3 guesses with confidence scores, and a responsibility prompt for ambiguous categories. Implement keyboard navigation: `↓`/`↑` or `J`/`K` to move between items, `Enter` to accept top guess, `1`/`2`/`3` to pick alternate category, `A`/`K`/`S` to set responsibility, `Space` to skip. Implement `POST /review/corrections` to record bulk corrections in session state.
- **Acceptance Criteria**:
  - [x] All transactions with `needs_review=True` appear in the queue for the selected month
  - [x] Each item shows the top 3 classifier guesses with confidence scores
  - [x] Keyboard shortcuts `J`/`K`/`Enter`/`1`/`2`/`3`/`A`/`K`/`S`/`Space` all function correctly
  - [x] Accepting a guess removes the item from the queue and decrements the badge count in the sidebar
  - [x] "Accept all confident guesses" accepts all items where the top guess confidence ≥ 0.70
  - [x] Queue-empty state shows "All transactions reviewed." with no emoji
  - [x] The sidebar badge count updates live as items are resolved

---

### TASK-021: Transaction Detail Drawer
- **Status**: Done (2026-04-17)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-017
- **Context**: Implements UX-SPEC Touchpoint 6 — the side drawer that slides in from the right when Andrew clicks any transaction row, showing full metadata including the accounting-period override. This resolves the UX Open Question (accounting period default = cash date's month, manual override here).
- **Description**: Implement `GET /transactions/{id}/drawer` returning an HTMX partial rendering the drawer. Drawer contains: merchant, amount, original currency + rate + rate source, category with classifier confidence + top 3 alternates, responsibility radio, accounting period selector (month picker defaulting to cash_date's month), notes field, source file reference, classifier audit trail. Implement `POST /transactions/{id}/update` to apply changes to session state.
- **Acceptance Criteria**:
  - [x] Clicking any transaction row in any page opens the drawer without leaving the current page
  - [x] Drawer shows rate source ("statement" / "BoC daily average" / "manual") with clear labeling
  - [x] Accounting period shows cash date and a month picker (default = cash date's month per TDD Section 2.4)
  - [x] Changing accounting period in the drawer moves the transaction to that month's view
  - [x] Notes field accepts free text
  - [x] Classifier audit trail shows `"classified by tfidf_lr at 0.84 on 2026-04-15"` format
  - [x] `Esc` or clicking outside closes the drawer without losing other session edits
  - [x] Changes from the drawer are held in session state until Save

---

### TASK-022: Save Review Session and Classifier Retrain
- **Status**: Done (2026-04-17)
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-020, TASK-021, TASK-007
- **Context**: Implements TDD Section 2.5 (save route) and UX-SPEC Touchpoint 7 (batched commit model). The "Save review session" button commits all pending session edits to the DB, writes corrections rows, and triggers a background retrain.
- **Description**: Implement `POST /review/save-session`. Show a confirmation: "Save N corrections from this session? The classifier will retrain (~2 seconds)." On confirm: commit all session edits to the DB (update transactions, insert corrections rows), update the exact-match cache, call `ClassifierClient.retrain()` in a background thread, show a "Classifier updated" toast on completion. Handle retrain failure gracefully (changes saved, old classifier stays active, warning shown).
- **Acceptance Criteria**:
  - [ ] All pending session edits are committed to the DB atomically (DB transaction; if any write fails, all roll back)
  - [ ] A `corrections` row is inserted for each changed category or responsibility
  - [ ] `ClassifierClient.retrain()` is called in a background thread — the page does not block
  - [ ] A toast shows "Classifier updated" when retraining completes
  - [ ] If retraining fails: a warning banner appears; the old model continues to operate
  - [ ] The "Save review session" button is disabled (with tooltip "No changes to save") when session state is empty
  - [ ] Browser `beforeunload` guard is active: navigating away with unsaved changes prompts the browser dialog
  - [ ] After save, the session state is cleared

---

## Sprint 6: Overview and Analytics

### TASK-023: Overview Page — Monthly Snapshot and Envelope Grid
- **Status**: Not started
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-017, TASK-022
- **Context**: Implements UX-SPEC Touchpoint 3 and TDD Section 2.2 (ClassifierPerformanceStats data contract). The Overview is read-only — all editing happens on category pages.
- **Description**: Implement `GET /overview` route and `templates/overview.html`. Monthly snapshot: total income, total expense, net — per person (Andrew, Kristy) and combined. Envelope compliance grid: 11 categories × 2 people, each cell green/amber/red (with icon, colour-blind-safe). Month-over-month comparison: this month vs. last month by category. Classifier performance panel: review queue length trend (last 3 sessions), override rate trend, confidence histogram.
- **Acceptance Criteria**:
  - [ ] Overview shows correct total income, total expense, and net for the selected month
  - [ ] Andrew total and Kristy total are broken out separately
  - [ ] Envelope compliance grid renders for all 11 expense categories with correct green/amber/red + icon indicators
  - [ ] Clicking a category cell navigates to that category page
  - [ ] Classifier performance panel shows at least: review queue length for the last 3 sessions, override rate for the last session
  - [ ] Overview is read-only: no inline editing is possible from this page
  - [ ] Empty state for a month with no uploads shows the correct CTA

---

### TASK-024: Settings Page — Budget Envelopes
- **Status**: Not started
- **Agent**: data-pipeline (impl)
- **Complexity**: Low
- **Depends on**: TASK-017
- **Context**: Allows Andrew to view and update budget envelope amounts for each category and person. Seeded from `Planning - Monthly` sheet; editable in-app.
- **Description**: Implement `GET /settings` and `POST /settings/envelopes` routes and `templates/settings.html`. Show all 11 expense categories with Andrew's and Kristy's envelope amounts for the selected year. Inline edit fields for each cell. Save updates the `budget_envelopes` table.
- **Acceptance Criteria**:
  - [ ] All 11 categories are shown with Andrew and Kristy envelope amounts
  - [ ] Amounts are editable inline (HTMX partial submit per row, or a single form save for the page)
  - [ ] Saved amounts are reflected immediately on the category pages (envelope bars)
  - [ ] Invalid amounts (non-numeric, negative) are rejected with a validation error
  - [ ] The settings page is accessible from the sidebar

---

## Sprint 7: Quality, Testing, and Polish

### TASK-025: Pytest Test Suite — Core Logic Coverage
- **Status**: Not started
- **Agent**: test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-009, TASK-007, TASK-008
- **Context**: Validates the core pipeline logic (normalizer, classifier, FX client, parser registry) meets the 80% coverage target for core logic per CLAUDE.md coding standards. Does not cover FastAPI routes (those are integration-tested in TASK-026).
- **Description**: Write pytest unit tests for: `classifier/normalizer.py` (normalization edge cases), `classifier/offline.py` (cache hit/miss, confidence thresholds, retrain metrics), `fx/boc_client.py` (averaging, null exclusion, caching, error handling), `parsers/registry.py` (dispatch logic, UnknownIssuerError), `ingestion/normalizer.py` (all FX paths), `ingestion/pipeline.py` (duplicate detection). Use pytest fixtures for DB setup/teardown with SQLite in-memory.
- **Acceptance Criteria**:
  - [ ] `pytest --cov=classifier --cov=fx --cov=parsers --cov=ingestion` reports ≥80% coverage on each module
  - [ ] All normalization edge cases pass (branch codes, province suffixes, Chinese characters, empty string)
  - [ ] FX client tests mock `httpx` — no real HTTP calls in the test suite
  - [ ] Parser registry tests use mock parsers — no real PDF files required (real-statement integration tests are in the parser tasks)
  - [ ] Retrain test runs on a small synthetic corpus (20 rows) and asserts the metrics dict structure
  - [ ] Tests run in <30 seconds on a MacBook M-series

---

### TASK-026: End-to-End Integration Test — Full Monthly Session
- **Status**: Not started
- **Agent**: test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-015, TASK-022, TASK-023
- **Context**: Validates the full monthly workflow end-to-end: upload MBNA PDF → classification → review queue → save → overview. Uses a real (anonymized) MBNA test fixture.
- **Description**: Write a pytest integration test (or a Playwright/httpx test) that simulates the full monthly session: POST a real MBNA PDF to `/upload`, poll the SSE stream until done, check the review queue, accept all confident classifications, save the session, check the overview totals. Validate DB state at each step.
- **Acceptance Criteria**:
  - [ ] Upload a 20-transaction MBNA PDF → all 20 transactions appear in the DB
  - [ ] At least 15 of 20 transactions have `needs_review=False` (cache + classifier working)
  - [ ] Save session → all pending corrections written to `corrections` table → `retrain()` called
  - [ ] Overview totals after save match the sum of the imported transactions
  - [ ] No unhandled exceptions at any step
  - [ ] Test runs against a real SQLite test DB (not in-memory) to confirm Alembic migration compatibility

---

### TASK-027: README, Documentation, and Deployment Notes
- **Status**: Not started
- **Agent**: content-writer (docs)
- **Complexity**: Low
- **Depends on**: TASK-026
- **Context**: Final documentation task before the PoC is considered shippable. Updates the README with setup instructions, usage guide, and confirms the "Built with Claude Code" line is present.
- **Description**: Update `projects/bookkeeping-app/README.md`: add a "Getting started" section (clone, venv, install, seed import, run), a "Monthly workflow" section (how to run a session), a "Adding a new issuer parser" section (the 3-step process from TDD Section 10). Confirm `> Built with [Claude Code](https://claude.ai/code)` is present directly below the project description. Update `docs/bookkeeping-app/poc/TASKS.md` with final task statuses.
- **Acceptance Criteria**:
  - [ ] `README.md` contains the "Built with Claude Code" line directly below the description
  - [ ] "Getting started" section covers: prerequisites, setup, seed import, first run
  - [ ] "Monthly workflow" section matches the desired workflow in PRD Section 7
  - [ ] "Adding a new issuer parser" section is accurate and references `parsers/base.py`
  - [ ] No private information (account numbers, real transaction data) appears in the README or any committed file
  - [ ] All four mandatory gate documents (PRD, TDD, DATA-SOURCES, TASKS) are referenced in the README

---

## Completed Tasks Log

- **TASK-001** — Project Scaffolding and Repository Initialization — Done 2026-04-15
- **TASK-002** — Database Schema, Alembic Migrations, and Seed Categories — Done 2026-04-15
- **TASK-003** — Historical Seed Data Import — Done 2026-04-15
- **TASK-004** — IssuerParser Interface and ParserRegistry — Done 2026-04-15
- **TASK-005** — ClassifierClient Interface and OfflineClassifierClient Skeleton — Done 2026-04-15
- **TASK-006** — Merchant Normalization and Exact-Match Cache (Layer 1) — Done 2026-04-15
- **TASK-007** — TF-IDF + Logistic Regression Classifier (Layer 2) — Done 2026-04-15
- **TASK-008** — FX Client — BoC Valet API Integration — Done 2026-04-15
- **TASK-009** — Transaction Normalizer and FX Resolution Pipeline — Done 2026-04-15
- **TASK-010** — MBNA Parser — Done 2026-04-15
- **TASK-011** — Wealthsimple Parser — Done 2026-04-15
- **TASK-012** — Rogers Bank Parser — Done 2026-04-15
- **TASK-013** — Full Ingestion Pipeline Integration — Done 2026-04-15
- **TASK-014** — FastAPI Application Scaffolding and Base Templates — Done 2026-04-15
- **TASK-015** — Upload Flow — File Upload and SSE Progress Stream — Done 2026-04-15
- **TASK-017** — Category Pages with Transaction Table and Per-Person Totals — Done 2026-04-15
- **TASK-018** — Inline Responsibility Toggle (HTMX Partial) — Done 2026-04-16
- **TASK-016** — SIM HK Parser — Done 2026-04-16
- **TASK-019** — Drag-to-Recategorize (Sortable.js + HTMX) — Done 2026-04-16
- **TASK-020** — Needs-Review Queue Page — Done 2026-04-17
- **TASK-021** — Transaction Detail Drawer — Done 2026-04-17
- **TASK-022** — Save Review Session and Classifier Retrain — Done 2026-04-17

---

## Gaps & Open Questions

1. **SIM HK statement availability** (TASK-016 pre-condition): TASK-016 is blocked until Andrew provides a real SIM HK statement. This is the single highest-risk item in the entire task list. Andrew should obtain this statement as early as possible — ideally before Sprint 3 begins.

2. **Excel column name verification** (TASK-003 pre-condition): Before implementing `seed_import.py`, the exact column names in the `Expense - Expense`, `Income - 表格 1`, and `Planning - Monthly` sheets must be printed and confirmed. A 10-minute inspection of the real file prevents a painful bug in seed data import.

3. **Wealthsimple statement types**: if Andrew does not have both Cash and Investment Wealthsimple PDFs, TASK-011 can be scoped to Cash account only for Phase 1.

4. **Session state implementation**: TDD Section 2.5 specifies server-side session state stored in a signed cookie or in-memory dict. For a single-user PoC on localhost, an in-memory dict keyed by session token is the simplest correct choice. If the server restarts mid-session, session state is lost (acceptable for PoC). This should be noted as a known limitation.

5. **Sortable.js + HTMX OOB swap targeting off-screen elements** (TDD Gaps #4): when Andrew drags a transaction to a category that is not the currently loaded page, the OOB swap target is not in the DOM. The `move` endpoint should respond with the source page's updated totals as OOB, and the target page will recalculate from DB on next load. This behavior should be tested explicitly in TASK-019.
