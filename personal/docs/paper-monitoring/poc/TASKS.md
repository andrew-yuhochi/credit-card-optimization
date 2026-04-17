# Task Breakdown -- Paper Monitoring

> **Status**: Active
> **Last Updated**: 2026-04-16
> **Depends on**: PRD.md, TDD.md, DATA-SOURCES.md (all approved)

## Progress Summary
| Status | Count |
|--------|-------|
| Done | 28 |
| In Progress | 0 |
| To Do | 0 |
| Backlog | 2 |
| Blocked | 0 |

---

## Sprint 1: Foundation (Scaffolding, Schema, Config)

> **Suggested starting point**: Begin with TASK-001, TASK-002, and TASK-003. These three tasks produce the project skeleton, data contracts, and database layer that every subsequent task depends on.

### TASK-001: Project Scaffolding and Configuration
- **Status**: Done (2026-04-13)
- **Complexity**: S
- **Depends on**: None
- **Description**: Create the full project directory structure as defined in TDD Section 9. Set up the Python virtual environment, install pinned dependencies from `requirements.txt`, create `.env.example`, `.gitignore`, and the `config.py` module using Pydantic `BaseSettings` with all tunables from TDD Section 7.
- **Acceptance Criteria**:
  - [ ] Directory tree matches TDD Section 9 exactly, including all `__init__.py` files, `.gitkeep` files in `digests/` and `notebooks/`, and empty module stubs
  - [ ] `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` succeeds without errors
  - [ ] `requirements.txt` contains exact pinned versions for all 8 dependencies listed in TDD Section 12
  - [ ] `config.py` loads defaults and overrides from environment variables with the `PM_` prefix (e.g., `PM_OLLAMA_MODEL=phi4:14b` overrides `ollama_model`)
  - [ ] `.env.example` committed; `.env` gitignored
  - [ ] `.gitignore` includes `data/`, `.env`, `__pycache__/`, `*.pyc`, `.venv/`, `*.egg-info/`, `digests/*.html`
  - [ ] Logging configuration module (`utils/logging_config.py`) writes to both stderr and a rotating file at `data/logs/pipeline.log`
- **Notes**: This task produces the skeleton every other task imports from. No business logic here.

### TASK-002: Pydantic Data Models
- **Status**: Done (2026-04-14)
- **Complexity**: S
- **Depends on**: TASK-001
- **Description**: Implement all Pydantic v2 models defined in TDD Section 10 across four files: `models/arxiv.py`, `models/huggingface.py`, `models/classification.py`, and `models/graph.py`. These are the data contracts between all components.
- **Acceptance Criteria**:
  - [ ] `ArxivPaper` model with all fields from TDD (arxiv_id, title, abstract, authors, primary_category, all_categories, published_date, updated_date, arxiv_url, pdf_url, comment)
  - [ ] `HFPaper` model with defaults (upvotes=0, ai_keywords=[], num_comments=0)
  - [ ] `PaperClassification` model supports `tier=None` and `classification_failed=True` for Ollama failures; includes `raw_response` field for debugging
  - [ ] `ExtractedConcept` model with name, description, domain_tags, prerequisite_concept_names
  - [ ] `Node`, `Edge`, `ScoredPaper`, `WeeklyRun`, `DigestEntry` models match TDD definitions exactly
  - [ ] All models use Pydantic v2 syntax (not v1 compat)
  - [ ] Unit tests validate model construction, defaults, and rejection of invalid input (e.g., missing required fields)
- **Notes**: These models are imported by every service and integration module. Get them right early.

### TASK-003: GraphStore and SQLite Schema
- **Status**: Done (2026-04-14)
- **Complexity**: M
- **Depends on**: TASK-001, TASK-002
- **Description**: Implement the `GraphStore` class in `store/graph_store.py` with the full SQLite schema from TDD Section 2.4.2. The schema must use **nodes + edges tables** as the core graph structure -- not flat arrays or embedded JSON concept lists. Include the `weekly_runs` supporting table and all indexes.
- **Acceptance Criteria**:
  - [ ] `GraphStore.__init__` creates the database file and runs `CREATE TABLE IF NOT EXISTS` for `nodes`, `edges`, and `weekly_runs` tables on first open
  - [ ] `nodes` table has columns: `id TEXT PRIMARY KEY`, `node_type TEXT NOT NULL`, `label TEXT NOT NULL`, `properties TEXT`, `created_at`, `updated_at`
  - [ ] `edges` table has composite primary key `(source_id, target_id, relationship_type)` with foreign key references to `nodes(id)`
  - [ ] All six indexes from TDD Section 2.4.2 are created
  - [ ] `upsert_node` inserts new nodes and updates `properties` + `updated_at` on conflict
  - [ ] `upsert_edge` inserts or replaces edges on the composite primary key
  - [ ] `get_concept_index()` returns a `list[str]` of all concept node labels
  - [ ] `paper_exists(arxiv_id)` checks for `paper:{arxiv_id}` in the nodes table
  - [ ] `log_run` and `get_latest_run` work correctly for the `weekly_runs` table
  - [ ] `get_papers_for_digest(run_date)` returns paper node data joined with their `BUILDS_ON` edges to concept nodes
  - [ ] Unit tests run against an in-memory SQLite database (`:memory:`) and verify all CRUD operations, upsert behavior, and index existence
  - [ ] Node IDs follow the convention: `concept:{normalized_name}` and `paper:{arxiv_id}`
- **Notes**: This is the core persistence layer. The graph schema is a hard requirement -- see project memory on graph-first design.

---

## Sprint 2: Data Ingestion (arXiv, HuggingFace, PDF)

### TASK-004: arXiv API Client
- **Status**: Done (2026-04-14)
- **Complexity**: M
- **Depends on**: TASK-002
- **Description**: Implement `ArxivFetcher` in `integrations/arxiv_client.py` with three methods: `fetch_recent`, `fetch_by_id`, and `fetch_batch`. Parse Atom XML responses into `ArxivPaper` Pydantic models. Implement the date-filter workaround, deduplication, and rate limiting.
- **Acceptance Criteria**:
  - [ ] `fetch_recent(categories, max_results)` queries arXiv with `sortBy=submittedDate` and `sortOrder=descending`, **not** the broken `submittedDate:[FROM TO]` range parameter
  - [ ] Python post-processing filters papers by `published_date >= (today - lookback_days)` and stops pagination when papers are older than the lookback window
  - [ ] Deduplication by `arxiv_id` across category fetches (cross-listed papers appear once)
  - [ ] `arxiv_id` extracted correctly from URL: `http://arxiv.org/abs/2604.11805v1` becomes `2604.11805` (version suffix and URL prefix stripped)
  - [ ] 3-second `time.sleep` between sequential API requests (configurable via `config.arxiv_fetch_delay`)
  - [ ] Retry up to 3 times with exponential backoff (3s, 9s, 27s) on HTTP 5xx; log and abort on HTTP 4xx
  - [ ] Malformed XML entries are logged and skipped, not raised
  - [ ] `fetch_by_id(arxiv_id)` returns a single `ArxivPaper` (used by `seed.py --arxiv-id`)
  - [ ] `fetch_batch(arxiv_ids)` returns a list of `ArxivPaper` for a batch of IDs (used during seeding)
  - [ ] Unit tests use canned XML responses (no live API calls); one integration test (marked `@pytest.mark.slow`) hits the live API for a known paper ID
- **Notes**: The date-filter workaround is critical. arXiv's `submittedDate` range query returns 0 results -- this was confirmed during research.

### TASK-005: HuggingFace Daily Papers Client
- **Status**: Done
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: S
- **Depends on**: TASK-002
- **Description**: Implement `HuggingFaceFetcher` in `integrations/hf_client.py` with three methods: `fetch_daily_papers`, `fetch_week`, and `lookup_paper`. Parse JSON responses into `HFPaper` Pydantic models. The client must degrade gracefully -- if the API is unreachable, return empty results instead of raising.
- **Acceptance Criteria**:
  - [x] `fetch_week(end_date)` calls `fetch_daily_papers` for each of the past 7 days and returns a `dict[str, HFPaper]` keyed by arXiv ID
  - [x] 1-second `time.sleep` between sequential API calls (configurable via `config.hf_fetch_delay`)
  - [x] If the HF API returns any error (HTTP 4xx/5xx, connection error, timeout), log a warning and return empty results -- never raise
  - [x] Malformed JSON entries are logged and skipped
  - [x] `lookup_paper(arxiv_id)` returns `HFPaper | None`
  - [x] Unit tests use canned JSON responses
- **Notes**: HF data is supplementary. The pipeline must work even if HF is completely down.

### TASK-006: PDF Text Extractor
- **Status**: Done (2026-04-14)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: S
- **Depends on**: TASK-001
- **Description**: Implement `PdfExtractor` in `integrations/pdf_extractor.py` using PyMuPDF (`fitz`). Used only during the seeding phase to extract text from textbook chapters by page range.
- **Acceptance Criteria**:
  - [ ] `extract_chapters(pdf_path, chapter_ranges)` accepts a `Path` and a list of `(start_page, end_page)` tuples (0-indexed, inclusive)
  - [ ] Returns a `list[ChapterText]` where each entry contains the extracted text and a source description (e.g., "Goodfellow et al. Deep Learning, Ch. 3")
  - [ ] Handles missing PDF file by logging an error and returning an empty list (not raising)
  - [ ] Unit test with a small test PDF validates text extraction and page range slicing
- **Notes**: Expect noise from headers, footers, and equation formatting. This is acceptable for PoC -- Ollama handles noisy input well.

---

## Sprint 3: Seeding Pipeline (Knowledge Bank Bootstrap)

### TASK-007: Ollama Client Wrapper with Retry Logic
- **Status**: Done (2026-04-14)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: M
- **Depends on**: TASK-001, TASK-002
- **Description**: Implement the low-level Ollama wrapper in `integrations/ollama_client.py` that handles the `format="json"` parameter, JSON parsing, Pydantic validation, and retry logic. This wrapper is used by `OllamaClassifier` (TASK-008) but is a separate module to isolate retry and connection logic.
- **Acceptance Criteria**:
  - [ ] Calls `ollama.chat()` with `model` from config, `format="json"`, and system + user messages
  - [ ] Parses response with `json.loads()`; validates against a caller-provided Pydantic model
  - [ ] On JSON parse failure or Pydantic validation failure, retries up to 3 total attempts; on each retry appends "Your previous response was not valid JSON. Return ONLY a JSON object with the specified fields." to the user prompt
  - [ ] After 3 failed attempts, returns `None` and logs a warning with the raw response text
  - [ ] Detects Ollama-not-running (connection refused) and raises a clear error: "Ollama is not running. Start with: ollama serve"
  - [ ] Detects model-not-found and raises a clear error: "Model {model} not found. Pull with: ollama pull {model}"
  - [ ] Timeout configurable via `config.ollama_timeout` (default 60s)
  - [ ] Unit tests mock the `ollama` library; test success path, JSON retry path (succeeds on attempt 2), and exhausted-retries path
- **Notes**: This module is the single point where Ollama is called. All retry logic lives here, not in the classifier.

### TASK-008: OllamaClassifier -- Concept Extraction and Paper Classification
- **Status**: Done (2026-04-14)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: M
- **Depends on**: TASK-007
- **Description**: Implement `OllamaClassifier` in `services/classifier.py` with two methods: `extract_concepts` (used during seeding) and `classify_paper` (used during weekly pipeline). Both call the Ollama wrapper from TASK-007. Includes the full prompt templates from TDD Section 2.3.1.
- **Acceptance Criteria**:
  - [ ] `extract_concepts(text, source_id)` uses the concept extraction prompt from TDD and returns `list[ExtractedConcept]`
  - [ ] `classify_paper(paper, concept_index)` uses the classification prompt from TDD with 3-5 few-shot examples and returns `PaperClassification`
  - [ ] The concept index (list of all known concept names) is injected into the classification system prompt so the LLM can reference existing concepts
  - [ ] If the Ollama wrapper returns `None` (all retries exhausted), `classify_paper` returns a `PaperClassification` with `classification_failed=True` and `tier=None`
  - [ ] Unit tests use a mocked Ollama wrapper; test that prompts are constructed correctly and that failure paths produce the expected `PaperClassification` shape
- **Notes**: Prompt text will need tuning during the validation phase (TASK-016). Get the structure right here; the exact wording can be iterated.

### TASK-009: Seeding Pipeline and CLI
- **Status**: Done (2026-04-14)
- **Agent**: architect (phase-transition review), data-pipeline (impl), test-validator (QA)
- **Complexity**: L
- **Depends on**: TASK-003, TASK-004, TASK-006, TASK-008
- **Description**: Implement `seed.py` as the seeding CLI entry point. Orchestrates the one-time knowledge bank bootstrap: fetches landmark papers and survey papers via `ArxivFetcher.fetch_batch()`, extracts textbook chapters via `PdfExtractor`, runs concept extraction via `OllamaClassifier.extract_concepts()`, and stores concept nodes + edges via `GraphStore`. Also supports the manual `python seed.py --arxiv-id <id>` command for adding individual survey papers.
- **Acceptance Criteria**:
  - [ ] `python -m src.seed` (no arguments) runs the full seeding pipeline: landmark papers (17), survey papers (9), textbook chapters (configured page ranges)
  - [ ] `python -m src.seed --arxiv-id 1706.03762` fetches a single paper, extracts concepts, and adds them to the knowledge bank
  - [ ] Concept nodes are created with IDs following the `concept:{normalized_name}` convention (lowercased, spaces to underscores, special characters stripped)
  - [ ] `INTRODUCES` edges are created from paper nodes to the concept nodes they introduced
  - [ ] `PREREQUISITE_OF` edges are created between concept nodes based on the `prerequisite_concept_names` returned by Ollama
  - [ ] Paper nodes for landmark/survey papers are created with full metadata in the `properties` JSON
  - [ ] Textbook chapter page ranges are configurable (in `seed.py` or a seeding config section)
  - [ ] If a textbook PDF is missing, the pipeline logs a warning and continues without it
  - [ ] If a concept node already exists (from a previous seed run or a different source), `upsert_node` updates it rather than creating a duplicate
  - [ ] After seeding, `GraphStore.get_concept_index()` returns 150-300 concept labels (approximate target)
  - [ ] Seeding progress is logged to the console: which paper/chapter is being processed, how many concepts were extracted
  - [ ] Integration test: run seeding with 2 landmark papers (mocked Ollama) and verify concept nodes and edges are persisted correctly
- **Notes**: This is the largest single task. The landmark and survey paper arXiv IDs are listed in DATA-SOURCES.md. Textbook page ranges must be determined by inspecting each PDF during implementation.

---

## Sprint 4: Weekly Pipeline -- Ingestion and Pre-Filtering

### TASK-010: Pre-Filter Scoring
- **Status**: Done (2026-04-14)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: S
- **Depends on**: TASK-002
- **Description**: Implement `PreFilter` in `services/prefilter.py`. Scores and filters the raw weekly paper list down to the top candidates for classification.
- **Acceptance Criteria**:
  - [ ] `score_and_filter(papers, hf_data, top_n)` computes `score = (hf_upvotes * UPVOTE_WEIGHT) + category_priority_score` for each paper
  - [ ] `UPVOTE_WEIGHT` and category priority scores are read from `config.py`, not hardcoded
  - [ ] Category priorities match TDD: cs.LG=5, stat.ML=4, cs.AI=3, cs.CL=3, cs.CV=2
  - [ ] Papers not found in `hf_data` dict receive `upvotes=0` (still eligible via category score)
  - [ ] Returns top N papers sorted by score descending as `list[ScoredPaper]`
  - [ ] Default `top_n=100` is configurable
  - [ ] Unit tests verify scoring formula, sort order, tie-breaking, and that papers with 0 upvotes are not excluded
- **Notes**: Simple scoring module. Keep top 50-100 to stay within Ollama's comfortable throughput window (~2-5 minutes total).

### TASK-011: Weekly Pipeline -- Ingestion Stage
- **Status**: Done (2026-04-15)
- **Agent**: architect (phase-transition review), data-pipeline (impl), test-validator (QA)
- **Complexity**: M
- **Depends on**: TASK-003, TASK-004, TASK-005, TASK-010
- **Context**: Builds the ingestion stage of `pipeline.py` (currently a stub) — calls `ArxivFetcher.fetch_recent()` + `HuggingFaceFetcher.fetch_week()`, deduplicates, skips known papers via `GraphStore.paper_exists()`, and produces a scored candidate list via `PreFilter.score_and_filter()`.
- **Description**: Implement the first stage of `pipeline.py`: fetch arXiv papers, fetch HF enrichment data, deduplicate, pre-filter, and produce the candidate list. This stage runs before classification and is the most network-intensive part of the pipeline.
- **Acceptance Criteria**:
  - [ ] `pipeline.py` entry point creates a `weekly_runs` record with `status='running'` at the start
  - [ ] Calls `ArxivFetcher.fetch_recent()` for all 5 configured categories
  - [ ] Calls `HuggingFaceFetcher.fetch_week()` for the same date range
  - [ ] Deduplicates arXiv papers by `arxiv_id` (handled by `ArxivFetcher`, but verified here)
  - [ ] Skips papers that already exist in the database (`GraphStore.paper_exists()`)
  - [ ] Passes the combined data to `PreFilter.score_and_filter()` to produce the candidate list
  - [ ] Logs summary: total fetched, after dedup, after existing-paper filter, after pre-filter
  - [ ] If ArxivFetcher fails completely (all retries exhausted), pipeline aborts and marks the run as `status='failed'`
  - [ ] If HuggingFaceFetcher fails, pipeline continues with `upvotes=0` for all papers (logged as warning)
  - [ ] Unit test mocks both fetchers and verifies the ingestion flow end-to-end
- **Notes**: This task builds the pipeline.py skeleton. Subsequent tasks (TASK-012, TASK-013, TASK-014) add classification, linking, and rendering stages to the same file.

---

## Sprint 5: Weekly Pipeline -- Classification, Linking, Storage, and Rendering

### TASK-012: Weekly Pipeline -- Classification Stage
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: M
- **Depends on**: TASK-008, TASK-011
- **Context**: Adds the classification stage to `pipeline.py` — loads concept index via `GraphStore.get_concept_index()`, then calls `OllamaClassifier.classify_paper()` for each candidate; preserves `classification_failed=True` papers rather than dropping them.
- **Description**: Add the classification stage to `pipeline.py`. For each candidate paper from the pre-filter, call `OllamaClassifier.classify_paper()` with the current concept index from the knowledge bank. Handle classification failures gracefully.
- **Acceptance Criteria**:
  - [ ] Loads the concept index from `GraphStore.get_concept_index()` before classification begins
  - [ ] Iterates over all candidate papers and calls `classify_paper()` for each
  - [ ] Papers where classification fails (`classification_failed=True`) are preserved in the results with `tier=None` -- they are not dropped
  - [ ] Logs progress: "Classifying paper N of M: {title}"
  - [ ] Logs a summary after classification: papers classified, papers failed, tier distribution
  - [ ] If Ollama is not running or the model is not found, pipeline aborts with a clear error message
  - [ ] Unit test mocks the classifier and verifies that the pipeline handles a mix of successful and failed classifications
- **Notes**: Classification of 50-100 papers at ~1-3s per paper takes ~2-5 minutes on Apple Silicon. No parallelism needed.

### TASK-013: ConceptLinker -- Fuzzy Concept Matching and Edge Creation
- **Status**: Done (2026-04-15)
- **Agent**: test-validator (QA)
- **Complexity**: S
- **Depends on**: TASK-003
- **Context**: `ConceptLinker` in `services/linker.py` is fully implemented. Only `tests/unit/test_linker.py` is missing.
- **Description**: Add unit tests for `ConceptLinker`. The implementation already exists in `services/linker.py`.
- **Acceptance Criteria**:
  - [x] `link_paper_to_concepts(paper_node_id, concept_names, store)` creates `BUILDS_ON` edges from the paper node to matched concept nodes
  - [x] `link_concept_prerequisites(concept_node_id, prerequisite_names, store)` creates `PREREQUISITE_OF` edges between concept nodes (used during seeding)
  - [x] Matching strategy: normalize both names to lowercase + stripped whitespace; try exact match first; if no match, use `difflib.SequenceMatcher` with threshold >= 0.85 (configurable via `config.concept_match_threshold`)
  - [x] Returns a list of matched concept node IDs; logs unmatched concept names at INFO level for user review
  - [x] Unit tests verify exact match, fuzzy match at boundary (0.84 rejected, 0.85 accepted), and unmatched name logging
- **Notes**: The 0.85 threshold should catch variations like "attention mechanism" vs "self-attention mechanism" while avoiding false matches. Threshold is tunable.

### TASK-014: Weekly Pipeline -- Storage and Digest Rendering
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: M
- **Depends on**: TASK-003, TASK-011, TASK-012, TASK-013
- **Context**: Adds storage + rendering stages to `pipeline.py` — upserts paper nodes into `GraphStore`, creates `BUILDS_ON` edges via `ConceptLinker`, updates the `weekly_runs` record, and renders `digests/YYYY-MM-DD.html` via a new `DigestRenderer` class using Jinja2 templates in `templates/`.
- **Description**: Add the storage and rendering stages to `pipeline.py`. After classification and linking, persist all paper nodes and edges to GraphStore, then render the weekly HTML digest using Jinja2.
- **Acceptance Criteria**:
  - [ ] Paper nodes are upserted into `GraphStore` with full classification metadata in the `properties` JSON (tier, confidence, summary, key_contributions, hf_upvotes, prefilter_score, run_date, classification_failed)
  - [ ] `BUILDS_ON` edges are created via `ConceptLinker` for each classified paper
  - [ ] `weekly_runs` record is updated with `papers_fetched`, `papers_classified`, `papers_failed`, `digest_path`, and `status='completed'`
  - [ ] `DigestRenderer.render()` produces `digests/YYYY-MM-DD.html` using Jinja2 templates
  - [ ] Digest groups papers by tier: T1 and T2 at the top (highlighted), T3/T4/T5 collapsed by default, classification failures at the bottom
  - [ ] Each paper card includes: title (linked to arXiv), authors, tier badge (color-coded), confidence, summary, key contributions, linked concept badges (with hover description), arXiv and PDF links
  - [ ] T5 papers include a note: "Consider adding to knowledge bank: `python seed.py --arxiv-id <id>`"
  - [ ] Jinja2 templates use inline CSS; HTML renders correctly in Safari on macOS
  - [ ] Template files: `templates/digest.html.j2`, `templates/partials/paper_card.html.j2`, `templates/partials/concept_badge.html.j2`
  - [ ] If no papers passed classification (empty digest), render a page with "No papers found this week" message
  - [ ] Unit test renders a digest from canned data and validates the output HTML contains expected structure (tier sections, paper titles, concept badges)
- **Notes**: Inline CSS is an intentional PoC shortcut documented in TDD Section 13. Tier badge colors: T1=gold, T2=silver, T3=blue, T4=gray, T5=green.

---

## Sprint 6: Scheduling and End-to-End Validation

### TASK-015: Scheduling -- cron, run_weekly.sh, and macOS Setup
- **Status**: Done (2026-04-15)
- **Agent**: data-pipeline (impl), content-writer (README docs)
- **Complexity**: S
- **Depends on**: TASK-014
- **Context**: No new Python code — creates `run_weekly.sh` shell script (activate venv, check Ollama health, run `python -m src.pipeline`) and updates README with crontab entry and macOS Full Disk Access instructions.
- **Description**: Create `run_weekly.sh`, document the cron setup, and document the macOS Full Disk Access requirement. The shell script activates the venv, verifies Ollama is running (starting it if needed), and runs the pipeline.
- **Acceptance Criteria**:
  - [ ] `run_weekly.sh` is executable (`chmod +x`) and contains the script from TDD Section 8
  - [ ] Script activates `.venv`, checks Ollama health via `curl -sf http://localhost:11434/api/tags`, starts Ollama if not running, and runs `python -m src.pipeline`
  - [ ] Script uses `set -euo pipefail` for strict error handling
  - [ ] Script logs start/end timestamps to stdout (captured by cron redirection)
  - [ ] Crontab entry documented in README: `0 18 * * 5 caffeinate -i /path/to/run_weekly.sh >> /path/to/cron.log 2>&1`
  - [ ] README includes macOS Full Disk Access setup steps: System Settings > Privacy & Security > Full Disk Access > add `/usr/sbin/cron`
  - [ ] README includes a verification step: test cron writes a file to the project directory before relying on the weekly schedule
  - [ ] `caffeinate -i` documented as preventing idle sleep only (not lid-close sleep)
- **Notes**: macOS Full Disk Access is a common gotcha -- without it, cron file writes silently fail. This must be documented prominently.

### TASK-016: End-to-End Integration Test
- **Status**: Done (2026-04-15)
- **Agent**: test-validator (primary), data-pipeline (test scaffolding)
- **Complexity**: M
- **Depends on**: TASK-009, TASK-014
- **Context**: Creates `tests/integration/test_pipeline_e2e.py` — runs seed→ingest→classify→store→render using mocked Ollama and in-memory SQLite; validates that the full data flow from canned XML/JSON inputs produces a correctly structured HTML digest.
- **Description**: Create an end-to-end integration test that runs the full weekly pipeline on a small batch of papers with a mocked Ollama backend. Validates the entire data flow from fetch to HTML digest output.
- **Acceptance Criteria**:
  - [ ] Test seeds the knowledge bank with 5 known concepts (mocked Ollama extraction)
  - [ ] Test feeds 10 canned arXiv papers (from saved XML) and 5 canned HF papers (from saved JSON) through the full pipeline
  - [ ] Pre-filter reduces 10 papers to top 5
  - [ ] Mocked Ollama classifier returns deterministic tier assignments for the 5 papers
  - [ ] ConceptLinker matches at least 2 concepts per paper (from the seeded knowledge bank)
  - [ ] Paper nodes and `BUILDS_ON` edges are persisted to an in-memory SQLite database
  - [ ] `weekly_runs` record is created with correct counts and `status='completed'`
  - [ ] Digest HTML file is written to a temp directory, contains all 5 classified papers grouped by tier
  - [ ] Test runs in under 30 seconds (no live API calls, no live Ollama)
  - [ ] Test is located in `tests/integration/test_pipeline_e2e.py`
- **Notes**: This test proves the components integrate correctly. It does not test Ollama classification quality -- that is TASK-017's concern.

### TASK-017: End-to-End Production Validation
- **Status**: Done (2026-04-16)
- **Agent**: none — manual validation
- **Complexity**: M
- **Depends on**: TASK-015, TASK-016 (both Done); dashboard (TASK-022, Done)
- **Description**: Validate the full system against all 5 PRD success criteria using actual production data. Revised from the original 4-week subjective validation — prompt quality iteration is deferred to MVP phase where the classification schema will be completely redesigned (BL-007: concept-first schema).
- **Acceptance Criteria**:
  - [x] SC-1: Unattended pipeline execution — cron installed, pipeline ran end-to-end from dashboard (verified TASK-023)
  - [x] SC-2: Papers classified with tier assignments — 30 papers classified (T3:24, T4:4, T5:2). Subjective quality of summaries is adequate for PoC; richer extraction deferred to MVP (BL-007)
  - [x] SC-3: Tier + summary + contributions + concept links present for every paper — verified via SkillClaw (2604.08377) and dashboard smoke test (TASK-023)
  - [x] SC-4: Knowledge bank contains 150-300 foundational concepts — exceeded target with 492 concepts
  - [x] SC-5: Zero ongoing cost — Ollama local, arXiv/HF APIs free, no paid services
  - [x] Spot-check filtered-out papers: reviewed pre-filter behavior during TASK-028 tuning (top_n reduced from 100→30, lookback extended to 30 days for fairer scoring). Pre-filter is not overly aggressive given the 30-day window provides sufficient upvote signal
- **Notes**: Original 4-week prompt tuning plan is superseded by MVP BL-007 (concept-first schema redesign), which will completely rewrite classification prompts and extraction logic. Tuning the current prompts would be wasted effort. Cron remains installed and will continue running weekly as background validation during MVP planning.

---

## Sprint 7: Streamlit Dashboard and Progress Reporting

### TASK-020: GraphStore — add get_all_papers() Method
- **Status**: Done (2026-04-15)
- **Complexity**: S
- **Depends on**: None
- **Description**: Add `get_all_papers(limit: int = 500) -> list[dict]` to `GraphStore`. Returns all paper nodes with their `properties` JSON parsed, ordered by `published_date DESC` using SQLite's `json_extract()`.
- **Acceptance Criteria**:
  - [x] Queries `nodes WHERE node_type = 'paper'` ordered by `json_extract(properties, '$.published_date') DESC`
  - [x] Returns at most `limit` rows (default 500)
  - [x] Each returned dict contains `id`, `label`, and all keys from `properties` JSON
  - [x] Returns `[]` if no paper nodes exist
  - [x] Full test suite passes with no regressions (250/250)

### TASK-021: Pipeline Progress Callback for Dashboard
- **Status**: Done (2026-04-15)
- **Complexity**: S
- **Depends on**: None
- **Description**: Add optional `progress_callback` parameter to `run_pipeline()` and `--progress` CLI flag. When `--progress` is passed, pipeline emits JSON lines to stdout at checkpoints (start, ingestion, per-paper classification, storage, done/error). Cron path passes `None` — zero overhead.
- **Acceptance Criteria**:
  - [x] `run_pipeline(progress_callback=None)` — new optional parameter
  - [x] `_run_classification` accepts `on_paper_classified` callback for per-paper progress
  - [x] `--progress` CLI flag emits JSON lines: `{"type": "progress|done|error", "message": "..."}`
  - [x] Cron path and all existing tests unchanged (250/250 pass)

### TASK-022: Streamlit Dashboard — Core App
- **Status**: Done (2026-04-15)
- **Complexity**: M
- **Depends on**: TASK-020, TASK-021
- **Description**: Streamlit single-page app at `src/dashboard/app.py`. Paper table from GraphStore, "Run Weekly Update" button that launches pipeline as a subprocess, live progress display, tier filter. Subprocess isolation ensures pipeline survives browser refresh.
- **Acceptance Criteria**:
  - [x] `src/dashboard/app.py` runs with `streamlit run src/dashboard/app.py`
  - [x] Paper table: 6 columns (tier, title, authors, published date, category, HF upvotes, confidence, arXiv link)
  - [x] Tier multiselect filter (T1–T5 + Failed)
  - [x] Header shows last run date/status from `get_latest_run()`
  - [x] "Run Weekly Update" launches `python -m src.pipeline --progress` as subprocess
  - [x] Reader thread drains subprocess stdout into queue; dashboard polls every 2s via `st.rerun()`
  - [x] On completion: success banner + progress log
  - [x] On error: error banner + last 5 stderr lines
  - [x] Empty state: "No papers classified yet" message
  - [x] `run_dashboard.sh` executable, activates venv, runs on port 8501
  - [x] `requirements.txt` updated with `streamlit==1.45.0`

### TASK-023: Dashboard Manual Smoke Test
- **Status**: Done (2026-04-16)
- **Agent**: none — manual user process
- **Complexity**: S
- **Depends on**: TASK-022, TASK-024, TASK-025, TASK-026, TASK-027
- **Description**: Manual verification. Run the dashboard against the live production database and verify all acceptance criteria hold after all dashboard improvements.
- **Acceptance Criteria**:
  - [ ] Dashboard loads at `http://localhost:8501` with the real `paper_monitoring.db`
  - [ ] Classified Papers tab shows card layout (tier, title, summary, key contributions, related concepts, arXiv link)
  - [ ] Seed papers are NOT shown in Classified Papers tab
  - [ ] Knowledge Bank tab shows all concepts with descriptions, source papers, prerequisites, and search
  - [ ] Papers older than 30 days are hidden from Classified Papers tab
  - [ ] Tier filter works correctly
  - [ ] "Run Weekly Update" triggers a pipeline run with live progress
  - [ ] After run completes, paper table refreshes; if T5 surveys found, knowledge bank grows
  - [ ] Cron job still fires correctly on Friday

---

## Sprint 8: Dashboard UX Improvements and Knowledge Bank Expansion

### TASK-024: Dashboard Redesign — Card Layout, Concepts Tab, 30-Day Window
- **Status**: Done (2026-04-16)
- **Complexity**: M
- **Depends on**: TASK-022
- **Description**: Redesigned the Classified Papers tab from a flat table to card layout showing: Tier, Title, Summary, Key Contributions, Related Concepts (from BUILDS_ON edges), and arXiv link. Added Knowledge Bank tab showing all concepts with description, source papers, prerequisites, and search. Seed papers hidden (filtered by `run_date` presence). Papers older than 30 days hidden. Sort order: run_date DESC, tier ASC, hf_upvotes DESC.
- **Acceptance Criteria**:
  - [x] Papers displayed as cards with tier, title, summary, key contributions, related concepts, arXiv link
  - [x] `get_all_papers()` joins BUILDS_ON edges to return linked concept labels
  - [x] Seed papers hidden (no `run_date` in properties)
  - [x] 30-day display window (papers older than 30 days hidden from UI)
  - [x] Knowledge Bank tab with `get_all_concepts()` returning INTRODUCES + PREREQUISITE_OF relationships
  - [x] Search bar filters concepts by name or description
  - [x] Sort: run_date DESC, tier ASC, hf_upvotes DESC
  - [x] 250/250 tests pass

### TASK-025: Pipeline Stage 4 — Knowledge Bank Expansion from T5 Surveys
- **Status**: Done (2026-04-16)
- **Complexity**: M
- **Depends on**: TASK-022
- **Description**: Added Stage 4 to the weekly pipeline. After classification, T5 (survey) papers get concept extraction via Ollama. New concepts are stored as nodes with INTRODUCES and PREREQUISITE_OF edges, growing the knowledge bank organically each week.
- **Acceptance Criteria**:
  - [x] `_run_knowledge_bank_expansion()` identifies T5 papers and runs `extract_concepts()`
  - [x] `_store_extracted_concepts()` creates concept nodes (dedup via upsert), INTRODUCES edges, PREREQUISITE_OF edges
  - [x] Progress callback emits "Extracting concepts from survey N of M" events
  - [x] Zero overhead when no T5 surveys in the run
  - [x] 250/250 tests pass

### TASK-026: Source-Type-Aware Concept Extraction Prompts
- **Status**: Done (2026-04-16)
- **Complexity**: S
- **Depends on**: TASK-025
- **Description**: Replaced the fixed "5-15 concepts" extraction prompt with type-specific guidance. `extract_concepts()` now accepts a `source_type` parameter that selects the appropriate prompt.
- **Acceptance Criteria**:
  - [x] `extract_concepts()` accepts `source_type` parameter (default "manual_seed")
  - [x] Prompt guidance: landmark_paper (1-3), survey_paper (20-40), weekly_survey (15-30), textbook_chapter (5-15 per chunk), manual_seed (5-15)
  - [x] Seeder passes `source_label` as `source_type`; pipeline passes "weekly_survey"
  - [x] 250/250 tests pass

### TASK-027: Textbook Seeding with Chunked Chapters
- **Status**: Done (2026-04-16)
- **Complexity**: M
- **Depends on**: TASK-026
- **Description**: Download textbook PDFs and seed concepts from textbook chapters. Chapters are split into ~3000-word chunks to avoid overwhelming the LLM with long inputs. Two of 4 textbooks available (Murphy PML, Sutton RL); Goodfellow is HTML-only (no single PDF), Hastie ESL hosting is down (404).
- **Acceptance Criteria**:
  - [x] `seed_chapter()` splits text into ~3000-word chunks and extracts 5-15 concepts per chunk
  - [x] Murphy PML PDF downloaded to `data/textbooks/murphy_pml_intro.pdf` (860 pages)
  - [x] Sutton & Barto RL PDF downloaded to `data/textbooks/sutton_barto_rl.pdf` (548 pages)
  - [x] Textbook seed completes successfully for Murphy (3 chapters) and Sutton (3 chapters)
  - [x] Knowledge bank grows by 100+ concepts from textbooks
  - [x] Goodfellow: deferred (HTML-only, no single PDF)
  - [x] Hastie ESL: deferred (hosting down, 404)
- **Notes**: Previous attempts failed due to qwen2.5:7b ignoring the expected `{"concepts": [...]}` schema when `format="json"` was used (model returned free-form JSON summaries). Fixed by switching OllamaClient to pass `response_model.model_json_schema()` as the `format` parameter, which constrains the model to the exact Pydantic schema. 45 chunks processed across 6 chapters, 272 concepts extracted (39 unique after dedup), knowledge bank grew from 166 to 389 concepts.

### TASK-028: Config Tuning — Lookback Window and Pre-filter
- **Status**: Done (2026-04-16)
- **Complexity**: S
- **Depends on**: None
- **Description**: Tuned pipeline config based on user feedback. Extended arXiv lookback from 7 to 30 days for fairer upvote scoring (papers published late in the week get more time to accumulate HF upvotes before being scored). Reduced prefilter_top_n from 100 to 30 to cut classification runtime from ~50 min to ~15 min.
- **Acceptance Criteria**:
  - [x] `arxiv_lookback_days`: 7 → 30
  - [x] `prefilter_top_n`: 100 → 30
  - [x] `ollama_timeout`: 60 → 300 (needed for qwen2.5:7b on M4)
  - [x] Settings `extra="ignore"` to tolerate unknown .env vars

### TASK-029: Comprehensive Textbook Seeding and Prerequisite Re-linking (5 Books, Full Coverage)
- **Status**: Backlog
- **Complexity**: L
- **Depends on**: TASK-027
- **Description**: Expand textbook seeding from 3 chapters x 2 books to full coverage across 5 textbooks. Download 3 new PDFs (Hastie ESL, Bishop PRML, Zhang D2L as Goodfellow substitute). Seed all content chapters with correct TOC-derived page ranges. Goodfellow remains unavailable (MIT Press forbids PDF). Previous config had incorrect page ranges for some chapters.
- **Acceptance Criteria**:
  - [x] Hastie ESL PDF downloaded (764 pp, via author's Google Drive)
  - [x] Bishop PRML PDF downloaded (758 pp, from Microsoft Research)
  - [x] Zhang D2L PDF downloaded (1151 pp, from d2l.ai — Goodfellow substitute)
  - [x] TEXTBOOK_CONFIGS updated with TOC-derived 0-indexed page ranges for all 5 books
  - [ ] Murphy PML: all 23 chapters seeded
  - [ ] Hastie ESL: all 17 chapters seeded
  - [ ] Bishop PRML: all 14 chapters seeded
  - [ ] Sutton RL: all 15 chapters seeded (skip Psychology/Neuroscience)
  - [ ] Zhang D2L: 17 key chapters seeded (skip Builders Guide, Computational Performance, Appendices)
  - [ ] Knowledge bank grows significantly (target 800+ concepts before dedup)
  - [ ] All 243 tests pass
- **Notes**: Estimated ~5 hours of Ollama processing for ~86 chapters across 5 books. Concepts overlap across books (e.g., probability in Murphy/Bishop/D2L); upsert handles collisions, semantic dedup deferred to TASK-030.

---

## Backlog (Post-PoC)

### TASK-030: Semantic Concept Deduplication
- **Status**: Backlog
- **Complexity**: M
- **Depends on**: TASK-029
- **Description**: Build a deduplication workflow for the knowledge bank that identifies and merges semantically equivalent concepts. Current name-based fuzzy matching (difflib, ratio >= 0.85) catches surface-level duplicates but misses semantic equivalences and produces false positives on legitimately different concepts with similar names.
- **Acceptance Criteria**:
  - [ ] Algorithm uses concept descriptions and domain tags (not just names) to compute semantic similarity
  - [ ] Embedding-based approach: generate embeddings for concept name + description, cluster by cosine similarity
  - [ ] Configurable merge threshold (default ~0.90 cosine similarity on descriptions)
  - [ ] Merge logic: keep the richer description, union domain_tags, re-link all INTRODUCES/BUILDS_ON/PREREQUISITE_OF edges to the surviving node
  - [ ] Dry-run mode: report proposed merges without executing
  - [ ] CLI: `python -m src.dedup --dry-run` / `python -m src.dedup --apply`
  - [ ] Test with known duplicates from TASK-029 output (e.g., "Bellman Equation" vs "Bellman Equations", "MDP" variants)
- **Notes**: Identified 38 near-duplicates at 0.80+ name similarity after TASK-027. True semantic duplicates include singular/plural variants, abbreviation variants (MDP vs Markov Decision Process), and hyphenation variants (pre-training vs pretraining). False positives include legitimately different concepts like "stochastic gradient ascent" vs "stochastic gradient descent" and "prior distribution" vs "posterior distribution". A description-aware algorithm is needed to distinguish these cases.

---

## Dependency Graph

```
TASK-001 (Scaffolding)
  |
  +-- TASK-002 (Pydantic Models)
  |     |
  |     +-- TASK-004 (arXiv Client)
  |     +-- TASK-005 (HF Client)
  |     +-- TASK-007 (Ollama Wrapper)
  |     |     |
  |     |     +-- TASK-008 (OllamaClassifier)
  |     |
  |     +-- TASK-010 (PreFilter)
  |
  +-- TASK-003 (GraphStore + Schema)  [also depends on TASK-002]
  |     |
  |     +-- TASK-013 (ConceptLinker)
  |
  +-- TASK-006 (PDF Extractor)
  |
  +-- TASK-009 (Seeding Pipeline)  [depends on TASK-003, 004, 006, 008]
  |
  +-- TASK-011 (Pipeline: Ingestion)  [depends on TASK-003, 004, 005, 010]
  |     |
  |     +-- TASK-012 (Pipeline: Classification)  [also depends on TASK-008]
  |           |
  |           +-- TASK-014 (Pipeline: Storage + Rendering)  [also depends on TASK-003, 013]
  |                 |
  |                 +-- TASK-015 (Scheduling)
  |                 +-- TASK-016 (E2E Integration Test)  [also depends on TASK-009]
  |                       |
  |                       +-- TASK-017 (4-Week Validation)  [also depends on TASK-015]
```

---

## Completed Tasks Log

### TASK-001: Project Scaffolding and Configuration — Done 2026-04-13
All acceptance criteria met. Directory tree, venv, config, and logging stubs verified.

### TASK-002: Pydantic Data Models — Done 2026-04-14
All acceptance criteria met. 4 model files created (arxiv.py, huggingface.py, classification.py, graph.py), __init__.py exports all 9 models. 36 unit tests pass covering construction, defaults, optional fields, and ValidationError on missing required fields.

### TASK-003: GraphStore and SQLite Schema — Done 2026-04-14
All acceptance criteria met. `GraphStore` implemented in `src/store/graph_store.py` with full DDL (nodes, edges, weekly_runs, all 6 indexes), upsert_node (ON CONFLICT preserves created_at), upsert_edge (INSERT OR REPLACE), get_concept_index, paper_exists, log_run, get_latest_run, get_papers_for_digest. Context-manager support included. 37 unit tests pass against in-memory SQLite covering schema, all CRUD ops, upsert behavior, and index existence.

### TASK-004: arXiv API Client — Done 2026-04-14
All acceptance criteria met. `ArxivFetcher` implemented in `src/integrations/arxiv_client.py`. Implements the date-filter workaround (sortBy=submittedDate + Python post-filter), pagination with early stop on old papers, deduplication by arxiv_id across categories, 3s rate-limit delay, exponential-backoff retry (3s/9s/27s on 5xx/connection errors), immediate abort on 4xx, skip-and-log on malformed XML entries. All three methods implemented: `fetch_recent`, `fetch_by_id`, `fetch_batch`. 29 unit tests pass using canned XML (no live API calls). One `@pytest.mark.slow` integration test added to `tests/integration/test_arxiv_live.py`.

### TASK-005: HuggingFace Daily Papers Client — Done 2026-04-14
All acceptance criteria met. `HuggingFaceFetcher` implemented in `src/integrations/hf_client.py`. `fetch_daily_papers`, `fetch_week`, and `lookup_paper` implemented. `fetch_week` returns `dict[str, HFPaper]` keyed by arXiv ID across 7 days with 1s delay between calls. All error conditions (HTTP 4xx/5xx, connection error, timeout, malformed JSON) degrade gracefully to empty results with a warning log. Unit tests use canned JSON responses.

### TASK-006: PDF Text Extractor — Done 2026-04-14
All acceptance criteria met. `ChapterText` Pydantic model added to `src/models/seeding.py` and exported from `src/models/__init__.py`. `PdfExtractor` implemented in `src/integrations/pdf_extractor.py` using PyMuPDF (fitz). Tuple extended to 3-tuple `(start_page, end_page, source_description)` to co-locate source description with each range — documented in docstring. Missing PDF and corrupt PDF both return `[]` without raising. Out-of-bounds `start_page` skips the range with a warning; out-of-bounds `end_page` clamps to last page with a warning. `PdfExtractor` exported from `src/integrations/__init__.py`. 8 unit tests pass (synthetic PDF created via fitz fixture); full suite 123/123 pass with no regressions.

### TASK-007: Ollama Client Wrapper with Retry Logic — Done 2026-04-14
All acceptance criteria met. `OllamaClient` implemented in `src/integrations/ollama_client.py`. Calls `ollama.Client.chat()` with `format="json"` and system + user messages. Parses with `json.loads()`, validates with Pydantic `model_validate()`. On `json.JSONDecodeError` or `ValidationError`, retries up to `ollama_max_retries` times appending `_RETRY_SUFFIX` to the user prompt each time. After exhausted retries returns `None` with a warning log. `httpx.ConnectError` raises `RuntimeError("Ollama is not running...")`. `ollama.ResponseError` with "not found" raises `RuntimeError("Model ... not found. Pull with: ollama pull ...")`. Other `ollama.ResponseError` propagates unchanged. `OllamaClient` exported from `src/integrations/__init__.py`. 10 unit tests pass (all ollama.Client calls mocked); full suite 133/133 pass with no regressions.

### TASK-008: OllamaClassifier — Done 2026-04-14
All acceptance criteria met. `OllamaClassifier` implemented in `src/services/classifier.py`. `_ClassificationResponse` and `_ConceptsResponse` are private intermediate models that match the LLM's JSON output exactly. `classify_paper` builds system + user prompts (concept index injected into system prompt; `"(none yet)"` placeholder when empty), calls `OllamaClient.chat()` with `_ClassificationResponse`, and maps to `PaperClassification`; returns `classification_failed=True` when client returns `None`. `extract_concepts` uses `_ConceptsResponse` and returns `[]` on client failure. `OllamaClassifier` exported from `src/services/__init__.py`. 10 unit tests pass (OllamaClient injected as MagicMock); full suite 143/143 pass with no regressions.

### TASK-011: Weekly Pipeline — Ingestion Stage — Done 2026-04-15
Added `create_run()` and `update_run()` to `GraphStore` to support the two-step run-tracking pattern (create with `status='running'` at start, update to `completed`/`failed` at end). Rewrote `src/pipeline.py` stub with full ingestion stage: `_fetch_arxiv()`, `_fetch_hf()` (degrades gracefully on failure), known-paper deduplication via `paper_exists()`, and `PreFilter.score_and_filter()`. Pipeline skeleton includes commented-out stubs for TASK-012 (classification) and TASK-014 (storage + rendering). 9 new pipeline unit tests + 4 new GraphStore tests. Full suite 188/188 pass with no regressions.

### TASK-016: End-to-End Integration Test — Done 2026-04-15
`tests/integration/test_pipeline_e2e.py` — 25 tests, module-scoped fixture runs the pipeline once (0.5s total). Phase 1: seeds 5 concepts via Seeder with mocked OllamaClassifier. Phase 2: mocked ArxivFetcher (10 papers), HuggingFaceFetcher (5 papers with upvotes), OllamaClassifier (4 tiers + 1 failure), real ConceptLinker + DigestRenderer. Assertions: knowledge bank seeding, pre-filter reduction (10→5 by scoring), run record counts, paper nodes + BUILDS_ON edges, failed paper stored without edges, digest HTML structure (tier sections, concept badges, failure section). 243/243 total pass.

### TASK-015: Scheduling — Done 2026-04-15
Rewrote `run_weekly.sh` to use `SCRIPT_DIR` (no hardcoded paths — works on any machine after clone). Improved Ollama health-check loop: retries every 5s for up to 30s instead of a single `sleep 10`. Full README rewrite: setup steps, scheduling section (crontab entry, `caffeinate -i` note, Full Disk Access steps, cron write-permission verification test), second-machine cloning instructions, project structure, and test-running instructions.

### TASK-014: Weekly Pipeline — Storage and Digest Rendering — Done 2026-04-15
`DigestRenderer` in `src/services/renderer.py` (Jinja2, `autoescape=True`). Groups entries into tier_groups dict passed to templates. Three templates fully implemented: `digest.html.j2` (inline CSS, T1/T2 in `<section>`, T3/T4/T5/failures in `<details>` for native collapse, T5 seed note), `partials/paper_card.html.j2`, `partials/concept_badge.html.j2` (hover description via `title` attr). `_run_storage_and_rendering()` added to `pipeline.py`: upserts paper nodes with full properties JSON, creates BUILDS_ON edges via ConceptLinker, assembles DigestEntry list, renders digest, writes `digest_path` to `weekly_runs` record. `ConceptLinker` and `DigestRenderer` exported from `src/services/__init__.py`. 20 renderer unit tests; existing end-to-end pipeline tests updated to patch `_run_storage_and_rendering`. Full suite 218/218 pass.

### TASK-012: Weekly Pipeline — Classification Stage — Done 2026-04-15
Added `_run_classification()` to `pipeline.py` with concept index loading, per-paper progress logging, tier-distribution summary, and graceful preservation of `classification_failed=True` results. RuntimeErrors from OllamaClient propagate naturally to abort the pipeline and mark the run `failed`. Short-circuits cleanly on an empty candidate list. `papers_classified` and `papers_failed` counters written to the `weekly_runs` record. 10 unit tests in `tests/unit/test_pipeline_classification.py`; 2 pre-existing ingestion tests updated to patch `OllamaClassifier` now that the classification stage is wired in. Full suite 198/198 pass.

### TASK-013: ConceptLinker — Done 2026-04-15
Implementation was already complete in `src/services/linker.py`. Added `tests/unit/test_linker.py` with 11 unit tests: exact match (base, case-insensitive, whitespace collapse), fuzzy boundary (ratio=0.85 accepted, 0.84 rejected with INFO log), unmatched name logging, `link_concept_prerequisites` PREREQUISITE_OF edges, empty store, empty names list, and multiple-names partial match. Full suite 175/175 pass with no regressions.

### TASK-009: Seeding Pipeline and CLI — Done 2026-04-14
All acceptance criteria met. Two-pass architecture implemented as designed: Pass 1 writes concept nodes + INTRODUCES edges immediately; Pass 2 (flush_prerequisites) writes PREREQUISITE_OF edges only to targets that exist in the graph. `normalize_concept_name()` created in `src/utils/normalize.py` as the single source of truth for concept node ID normalisation (6-step pipeline: strip, lowercase, whitespace-to-underscore, non-word-to-underscore, collapse underscores, strip underscores). `Seeder` class in `src/services/seeder.py` with `seed_paper`, `seed_chapter`, `seed_all`, `seed_paper_by_id`, and `flush_prerequisites`. `src/seed.py` CLI supports `--arxiv-id`, `--only-papers`, `--only-textbooks`, `--dry-run`. `src/services/__init__.py` updated to export `Seeder`. `src/utils/__init__.py` updated to export `normalize_concept_name`. 11 unit tests for normalisation + 7 integration tests (all with mocked Ollama, in-memory SQLite) pass. Full suite 162/162 pass with no regressions. CLI dry-run verified: logs correct counts for 17 landmark papers, 9 survey papers, 4 textbook configs.

### TASK-010: Pre-Filter Scoring — Done 2026-04-14
All acceptance criteria met. `PreFilter` implemented in `src/services/prefilter.py`. `score_and_filter` computes `score = (upvotes * upvote_weight) + category_priority` per paper, both weights read from `config.py`. Papers absent from `hf_data` receive `upvotes=0` and remain eligible via category score. Papers in unknown categories score 0. Sorted descending and sliced to `top_n` (defaults to `config.prefilter_top_n`). `PreFilter` exported from `src/services/__init__.py`. 10 unit tests pass; full suite 172/172 pass with no regressions.

### TASK-020: GraphStore — get_all_papers() — Done 2026-04-15
Added `get_all_papers(limit=500)` to `GraphStore`. Queries `nodes WHERE node_type = 'paper'`, orders by `json_extract(properties, '$.published_date') DESC`, returns parsed dicts. Full suite 250/250 pass.

### TASK-021: Pipeline Progress Callback — Done 2026-04-15
Added `progress_callback` parameter to `run_pipeline()` and `on_paper_classified` to `_run_classification()`. Added `--progress` CLI flag that emits JSON lines to stdout via `_stdout_progress()`. Checkpoints: start, ingestion complete, per-paper classification, storage complete, done/error. Cron path passes `None` — zero overhead. Also fixed pre-existing `Settings` crash from extra `.env` vars by adding `extra="ignore"` to model_config. Full suite 250/250 pass.

### TASK-022: Streamlit Dashboard — Done 2026-04-15
`src/dashboard/app.py` — single-page Streamlit app. Paper table via `get_all_papers()` with tier multiselect filter and arXiv link columns. "Run Weekly Update" button launches `python -m src.pipeline --progress` as subprocess; reader thread drains stdout JSON lines into `queue.Queue` in `st.session_state`; UI auto-refreshes every 2s. Success/error banners on completion. `run_dashboard.sh` created (executable, activates venv, port 8501). `streamlit==1.45.0` added to `requirements.txt`. Full suite 250/250 pass.

### TASK-024: Dashboard Redesign — Done 2026-04-16
Major dashboard overhaul: (1) Classified Papers tab redesigned from flat table to card layout showing tier, title, summary, key contributions, related concepts (from BUILDS_ON edges), and arXiv link. (2) Knowledge Bank tab added with `get_all_concepts()` — shows all concepts with description, source papers, prerequisites, and search bar. (3) Seed papers hidden from Classified Papers (filtered by `run_date` presence). (4) 30-day display window — older papers hidden from UI. (5) Sort: run_date DESC, tier ASC, hf_upvotes DESC. `get_all_papers()` updated to join BUILDS_ON edges for linked concept labels. 250/250 pass.

### TASK-025: Pipeline Stage 4 — Knowledge Bank Expansion — Done 2026-04-16
Added `_run_knowledge_bank_expansion()` and `_store_extracted_concepts()` to pipeline.py. After classification, T5 survey papers get concept extraction via Ollama. New concepts stored as nodes with INTRODUCES + PREREQUISITE_OF edges. Progress callback wired. Zero overhead when no T5 surveys. 250/250 pass.

### TASK-026: Source-Type-Aware Prompts — Done 2026-04-16
Replaced fixed "5-15 concepts" extraction prompt with `_SOURCE_TYPE_GUIDANCE` dict keyed by source type (landmark_paper: 1-3, survey_paper: 20-40, weekly_survey: 15-30, textbook_chapter: 5-15 per chunk, manual_seed: 5-15). `extract_concepts()` accepts `source_type` parameter. Seeder and pipeline pass appropriate types. 250/250 pass.

### TASK-027: Textbook Seeding with Chunked Chapters — Done 2026-04-16
6 textbook chapters (Murphy PML Ch. 2/3/10, Sutton RL Ch. 3/4/13) processed across 45 chunks with zero failures. 272 concepts extracted, 39 unique after dedup, 50 prerequisite edges. Knowledge bank grew from 166→389 concepts (target was 150-300). Key fix: switched `OllamaClient` from `format="json"` to `format=response_model.model_json_schema()` — the schema-constrained format forces qwen2.5:7b to output the exact expected Pydantic structure instead of free-form JSON summaries. Goodfellow (HTML-only) and Hastie ESL (404) deferred as expected.

### TASK-023: Dashboard Manual Smoke Test — Done 2026-04-16
Full smoke test of dashboard and pipeline. All 8 acceptance criteria passed. Bugs found and fixed: (1) Knowledge Bank not showing textbook sources — added `seeded_from` fallback in dashboard. (2) `.env` overriding `prefilter_top_n=100` — fixed to 30. (3) Pipeline crashes on broken stdout pipe when dashboard page refreshed — catch `BrokenPipeError` in `_stdout_progress`. (4) arXiv 429 rate limit treated as fatal 4xx — now retries with backoff from `Retry-After` header. (5) Paper cards missing date information — added Published/Classified dates. Pipeline verified end-to-end: 10312 papers fetched → 30 pre-filtered → 30 classified (T3:24, T4:4, T5:2) → digest rendered → knowledge bank expanded from 470 to 492 concepts via 2 T5 surveys.

### TASK-028: Config Tuning — Done 2026-04-16
`arxiv_lookback_days`: 7→30 (fairer upvote window), `prefilter_top_n`: 100→30 (~15 min runtime), `ollama_timeout`: 60→300 (needed for qwen2.5:7b on M4), Settings `extra="ignore"` for .env tolerance.
