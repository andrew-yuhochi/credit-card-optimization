# Task Breakdown — Paper Monitoring (Restart)

> **Status**: Active
> **Phase**: PoC (restart — prior PoC's 28 tasks are archived; new milestones below)
> **Last Updated**: 2026-04-19
> **Depends on**: PRD.md, TDD.md, DATA-SOURCES.md (all restart drafts)

This TASKS.md supersedes the 28-task PoC that shipped 2026-04-13 → 2026-04-16. The existing code in `projects/paper-monitoring/src/` is the *starting point*, not a deliverable — each task below describes what is being **added**, **extended**, or **replaced** in the existing codebase. Nothing is deleted wholesale.

## Progress Summary
| Status | Count |
|--------|-------|
| Done | 7 |
| In Progress | 0 |
| To Do | 10 |
| Blocked | 0 |

**Milestone order is binding** per CLAUDE.md's three-stage prototype validation rule (manual prototype → automated sample → full extension). Do not start Milestone 2 before the user approves Milestone 1. Do not start Milestone 3 before the user approves Milestone 2.

---

## Milestone 1: Schema Redesign + Stage 1 Manual Prototype (tree-based models)

> **Goal**: User can browse the hand-crafted XGBoost lineage (Decision Tree → Bagging → Random Forest → Boosting → AdaBoost → Gradient Boosting → XGBoost → LightGBM → CatBoost and their relationships) in both Obsidian and Neo4j Browser, validating the concept-first schema before any automated extraction is attempted.
> **Acceptance Criteria**:
> - The new concept-first schema tables (concepts, concept_relationships, papers, paper_concept_links, citation_snapshots, hf_model_snapshots, concept_queries, content_publications) exist and are populated with ~15 hand-crafted tree-based concepts and ~30 relationships.
> - The user can open Obsidian against the exported vault and navigate the XGBoost lineage by clicking wikilinks.
> - The user can open Neo4j Browser against the local Neo4j instance loaded with the exported Cypher, run a graph query, and see labeled edges on the relationships.
> - Running `python -m src.explore "XGBoost"` produces a Markdown export file with all 8 fields (including CONTENT_ANGLES) populated from the hand-crafted data.
> - The commercial-signal instrument (concept_queries + content_publications) records the explore query and exposes `src.signal report`.
> - Validation conversation with the user: "does this schema capture what you need for content, and does the exploration in Obsidian/Neo4j match your aspirational UX closely enough that we can build the automated version against it?"
> - If the schema needs adjustments, do them HERE — before Milestone 2 writes automated data into it.
> **Demo Gallery**: `docs/paper-monitoring/poc/demos/milestone-1/`
> **Review Checkpoint**: User reviews and approves before Milestone 2 begins (run `/milestone-complete paper-monitoring` to trigger the approval gate).
> **Status**: To Do

### TASK-M1-001: Concept-first schema migration + SQLite DDL
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: M
- **Depends on**: None (extends existing `src/store/graph_store.py`)
- **Context**: Adds 8 new tables from TDD §2.4.2 alongside existing `nodes`/`edges`. Legacy tables stay — the old cron pipeline keeps writing there until Milestone 4 cutover. `GraphStore` gets new methods (upsert_concept, upsert_concept_relationship, upsert_paper, link_paper_to_concept, write_citation_snapshot, log_concept_query, log_content_publication, loop_report).
- **Description**: Extend `GraphStore` with the new concept-first schema. Migration is additive — no data loss, no existing behavior broken. All new tables include `user_id TEXT NOT NULL DEFAULT 'default'`.
- **Acceptance Criteria**:
  - [ ] 8 new tables created per TDD §2.4.2 — all CHECK constraints enforced, all indexes present.
  - [ ] `GraphStore.__init__` runs `CREATE TABLE IF NOT EXISTS` for both legacy and new tables on open.
  - [ ] New methods on `GraphStore`: `upsert_concept`, `get_concept_by_name`, `list_concepts`, `upsert_concept_relationship`, `get_relationships`, `upsert_paper`, `link_paper_to_concept`, `write_citation_snapshot`, `get_citation_delta`, `get_resurrection_cohort`, `log_concept_query`, `log_content_publication`, `loop_report`.
  - [ ] All existing tests still pass (no regression in legacy `nodes`/`edges` behavior).
  - [ ] New unit tests cover the 13 new methods in an in-memory SQLite (`:memory:`) — upsert semantics, user_id defaulting, CHECK constraint violations, empty-result paths, loop_report math.
  - [ ] Pydantic models added/updated in `src/models/concepts.py` (NEW file): `Concept`, `ConceptRelationship`, `PaperRecord`, `PaperConceptLink`, `CitationSnapshot`, `ConceptQuery`, `ContentPublication`, `ResurrectionCandidate`.
- **Implementation Checklist**:
  - **Schema**: All 8 new tables (concepts, concept_relationships, papers, paper_concept_links, citation_snapshots, hf_model_snapshots, concept_queries, content_publications) must be added — none exist in `src/store/graph_store.py` (current DDL only defines `nodes`, `edges`, `weekly_runs` as Python string constants `_CREATE_NODES` / `_CREATE_EDGES` / `_CREATE_WEEKLY_RUNS`). There is no `schema.sql` file — schema lives inline in `graph_store.py`. `user_id` column does not exist on any current table. CHECK constraints for relationship_type enum, concept_type enum, source_type enum must be added — none currently enforced.
  - **Wire**: `GraphStore._create_schema()` at `src/store/graph_store.py:95` — extend the existing `with self._conn:` block to also `execute()` the 8 new CREATE TABLE statements and their indexes. Constructor `GraphStore.__init__` at line 76 already calls `_create_schema()`, so additive CREATE TABLE IF NOT EXISTS runs on every open.
  - **Call site**: The 13 new methods are net-new — no existing callers. Callers will land in TASK-M1-003 (seeder), TASK-M1-004 (explorer + signal logger), TASK-M1-005 (graph exporter), TASK-M2-003 (automated seeder), TASK-M4-002 (trend resurrector), TASK-M4-003 (cutover). Legacy methods `upsert_node`, `upsert_edge`, `get_concept_index`, `get_all_papers`, `get_all_concepts`, `paper_exists`, `get_papers_for_digest` stay intact and keep their existing callers in `src/pipeline.py`, `src/services/seeder.py`, `src/services/linker.py`, `src/dashboard/app.py`.
  - **Imports affected**: `src/models/concepts.py` is a NEW file — no existing importers to update. The 8 new Pydantic models (Concept, ConceptRelationship, PaperRecord, PaperConceptLink, CitationSnapshot, ConceptQuery, ContentPublication, ResurrectionCandidate) are all net-new names. Do not rename or move the existing `src/models/graph.py` models (Node, Edge, WeeklyRun, DigestEntry, ScoredPaper) — those are still used by the legacy path.
  - **Runtime files**: None — this task is pure Python + SQLite DDL. No configs, CSVs, or prompt files read at runtime.
- **Demo Artifact**: A CLI screenshot showing: `python -c "from src.store.graph_store import GraphStore; g = GraphStore('demo.db'); g.upsert_concept(Concept(name='XGBoost', ...)); print(g.get_concept_by_name('XGBoost', 'default'))"` printing the full round-trip. Save to `docs/paper-monitoring/poc/demos/milestone-1/TASK-M1-001.png`.
- **Notes**: This task is pure schema + CRUD. It has no user-visible effect on its own — the user-visible deliverable for Milestone 1 is TASK-M1-005 (Obsidian/Neo4j browsing). Per CLAUDE.md milestone rules, this task is an infrastructure task bundled inside the milestone whose first user-visible task is TASK-M1-005.

### TASK-M1-002: AI-propose 15 tree-based model concepts + relationships; user validates (ground truth)
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (generates proposals), user (reviews and approves)
- **Complexity**: M
- **Depends on**: TASK-M1-001
- **Context**: Instead of the user authoring concepts from scratch, the system generates all 15 concept notes with full fields populated (including CONTENT_ANGLES) and presents them for the user to review, edit, and approve. This validates AI-generated content quality at Stage 1 — earlier than originally planned — and reduces manual authoring effort. The approved set becomes the ground truth benchmark for Milestone 2.
- **Description**: Use the Anthropic Claude API (claude-sonnet-4-6, one-off calibration call) to generate 15 Markdown+YAML concept notes for the tree-based models domain: Decision Tree, Bagging, Random Forest, Boosting, AdaBoost, Gradient Boosting, XGBoost, LightGBM, CatBoost, Oblivious Trees, Histogram-based splits, and related concepts. Write notes to `projects/paper-monitoring/seeds/tree_based_ground_truth/`. User reviews each note, edits where wrong, and explicitly approves. Approved set is committed as the Stage 1 ground truth.
- **Acceptance Criteria**:
  - [ ] A generation script (`scripts/generate_ground_truth.py`) produces all 15 concept notes using Claude API with a structured prompt enforcing the YAML frontmatter schema.
  - [ ] Each note has YAML frontmatter with: `name`, `concept_type`, `what_it_is`, `what_problem_it_solves`, `innovation_chain` (list of {step, why}), `limitations`, `introduced_year`, `domain_tags`, `source_refs`, `content_angles` (3–4 editorial framings).
  - [ ] Each note has body prose explaining the concept with wikilinks to related concepts.
  - [ ] At least 30 relationships encoded in YAML `relationships:` block with typed edges and narrative labels.
  - [ ] All 7 relationship types (BUILDS_ON, ADDRESSES, ALTERNATIVE_TO, BASELINE_OF, PREREQUISITE_OF, INTRODUCES, BELONGS_TO) appear at least once.
  - [ ] User reviews all notes, makes edits, and explicitly confirms: "this quality represents what I want the automated pipeline to produce."
  - [ ] Final approved notes committed to `projects/paper-monitoring/seeds/tree_based_ground_truth/`.
- **Implementation Checklist**:
  - **Schema**: N/A — this task writes Markdown files, not DB rows. DB persistence happens in TASK-M1-003.
  - **Wire**: New entry point `scripts/generate_ground_truth.py` (standalone script, not a module). `scripts/` directory does not exist yet — must be created. Script calls Claude API directly via `anthropic` SDK; it is intentionally NOT wired into `src/pipeline.py` or `src/seed.py` because this is a one-off calibration run.
  - **Call site**: N/A — standalone script with no callers. User invokes manually via `python scripts/generate_ground_truth.py`.
  - **Imports affected**: N/A — `anthropic` is a new third-party dependency (not in `requirements.txt` currently). Add to requirements. Script may import `src.models.concepts.Concept` from TASK-M1-001 for structural validation of the generated YAML, but this is optional.
  - **Runtime files**: Reads `ANTHROPIC_API_KEY` from env (new — not in current `.env.example`). Writes 15 `.md` files to `projects/paper-monitoring/seeds/tree_based_ground_truth/` — directory must be created (neither `seeds/` nor `seeds/tree_based_ground_truth/` exists at project root; there is an unrelated `src/seeds/tree_based_prototype.py` from the legacy PoC that should not be confused with this). If the script uses a prompt template stored in a file, it would live at `scripts/prompts/ground_truth_prompt.txt` — must be added.
- **Demo Artifact**: The approved folder — link from `docs/paper-monitoring/poc/demos/milestone-1/TASK-M1-002-index.md` listing all 15 concept names with user's approval note.
- **Notes**: This is the single highest-leverage artifact in the whole PoC. The AI generates, the user judges. Quality bar: the user should be able to draft a LinkedIn carousel from any single export without needing to look anything up.

### TASK-M1-003: Seeder for hand-crafted ground truth
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: S
- **Depends on**: TASK-M1-001, TASK-M1-002
- **Context**: Adds a new CLI mode to `src/seed.py`: `python -m src.seed --ground-truth tree_based_ground_truth/`. Reads the Markdown+YAML files from TASK-M1-002, parses frontmatter with `python-frontmatter` library, upserts concepts and relationships via GraphStore. No LLM calls — pure file → DB.
- **Description**: Load the hand-crafted tree-based concepts and relationships into the new schema. This is the DB state that Milestones 1 and 2 compare against.
- **Acceptance Criteria**:
  - [ ] `python -m src.seed --ground-truth <dir>` reads all .md files and populates `concepts` + `concept_relationships`.
  - [ ] YAML frontmatter parsed into Concept fields with proper JSON serialization for list fields (innovation_chain, limitations, domain_tags, content_angles, source_refs).
  - [ ] Relationships block parsed into ConceptRelationship rows; target names resolved via fuzzy match (reuse existing ConceptLinker logic, threshold 0.85). Unresolved targets logged as WARNING and skipped.
  - [ ] Re-running the seeder is idempotent — upserts update existing concepts, don't duplicate.
  - [ ] Unit tests: 3 sample Markdown fixtures → 3 concepts + 5 relationships persisted correctly; idempotent re-run verified.
  - [ ] `python-frontmatter` added to `requirements.txt` (pinned version).
- **Implementation Checklist**:
  - **Schema**: Writes to `concepts` and `concept_relationships` tables — both must be added in TASK-M1-001 (not in current schema). No schema changes in this task.
  - **Wire**: `src/seed.py:main()` at line 200 — extend the existing `argparse.ArgumentParser` block (currently has `--arxiv-id`, `--only-papers`, `--only-textbooks`, `--dry-run`) to add `--ground-truth <dir>` flag. Add a new branch in `main()` that short-circuits before the existing `_build_seeder()` call when `--ground-truth` is set. The new path bypasses `Seeder` entirely — it constructs a `GraphStore` directly and calls the new methods from TASK-M1-001.
  - **Call site**: N/A for new methods — this IS the first caller of `GraphStore.upsert_concept` and `GraphStore.upsert_concept_relationship` added in TASK-M1-001. Does not modify existing `Seeder` class (`src/services/seeder.py`) — leave that intact for legacy paper/textbook seeding. Reuses `ConceptLinker._find_match` (defined at `src/services/linker.py:115`) for fuzzy name resolution against existing concepts, or replicates the `difflib.SequenceMatcher` + `concept_match_threshold` (default 0.85, from `src/config.py:44`) logic against the new `concepts` table.
  - **Imports affected**: New import `import frontmatter` in `src/seed.py` (and/or a new helper module like `src/services/ground_truth_loader.py`). No existing imports to rename. Import `Concept`, `ConceptRelationship` from `src/models/concepts.py` (new file from TASK-M1-001).
  - **Runtime files**: Reads all `*.md` files from `projects/paper-monitoring/seeds/tree_based_ground_truth/` — directory created in TASK-M1-002. If TASK-M1-002 has not been completed, this task cannot run. Also reads `src/config.py` Settings (existing — for `db_path` and `concept_match_threshold`). `requirements.txt` must gain `python-frontmatter==1.1.0` (not currently listed — current file only has requests, pydantic, pydantic-settings, ollama, Jinja2, PyMuPDF, streamlit, pytest, pytest-cov).
- **Demo Artifact**: Screenshot of `python -m src.seed --ground-truth seeds/tree_based_ground_truth/` completing successfully and a follow-up `sqlite3` query showing concept count ≥ 15. Save to `docs/paper-monitoring/poc/demos/milestone-1/TASK-M1-003.png`.

### TASK-M1-004: Concept Explorer CLI + Markdown exporter (the engine)
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: M
- **Depends on**: TASK-M1-001, TASK-M1-003
- **Context**: Creates `src/explore.py` CLI entry point and `src/services/concept_exporter.py`. Implements the 8-field Markdown export (UX-SPEC §7), fuzzy concept name resolution, recursive BUILDS_ON lineage traversal, and signal logging via `src/services/signal_logger.py`. Also adds `src/signal.py` CLI with `log-publication` and `report` subcommands.
- **Description**: Build the Concept Explorer engine. Given a concept name, produce the content-draft-ready export. Log every query for the commercial-signal instrument.
- **Acceptance Criteria**:
  - [ ] `python -m src.explore "XGBoost"` writes `exports/xgboost-YYYYMMDD.md` containing all 8 sections (CONCEPT, DEFINITION, CATEGORY, YEAR_INTRODUCED, LINEAGE, KEY_INNOVATIONS, LIMITATIONS, ALTERNATIVES, CONTENT_ANGLES, RELATED, SOURCES) exactly matching the UX-SPEC §7 / §11 layout.
  - [ ] LINEAGE traversal walks BUILDS_ON edges recursively (depth ≤ 10), producing ordered oldest-to-newest steps with their narrative labels.
  - [ ] Fuzzy concept name resolution: `explore "xgboost"`, `explore "XGBoost"`, `explore "XGB"` all resolve to the same concept (reuse ConceptLinker threshold).
  - [ ] `--format json` produces structured JSON with the same 8 fields.
  - [ ] Every call to `explore` logs a row to `concept_queries` via `SignalLogger` (even if output format is json).
  - [ ] `python -m src.signal log-publication --concept xgboost --channel linkedin --url "..."` writes a `content_publications` row.
  - [ ] `python -m src.signal report --days 30` prints query count, publication count, loop ratio, top queried concepts, published concepts.
  - [ ] Concept not found → print "did you mean…?" with top 3 fuzzy matches and exit 1 without logging a query.
  - [ ] Unit tests: resolve/traverse/export each tested with in-memory SQLite fixtures; signal logger verified for both query and publication paths.
- **Implementation Checklist**:
  - **Schema**: Reads `concepts`, `concept_relationships` (via BUILDS_ON edges for LINEAGE traversal, ALTERNATIVE_TO for ALTERNATIVES). Writes to `concept_queries` (every explore call) and `content_publications` (via `src.signal log-publication`). All four tables must be added in TASK-M1-001 — none in current schema.
  - **Wire**: Three new module entry points — all files new, none of them exist yet: `src/explore.py` (CLI, invoked as `python -m src.explore`), `src/signal.py` (CLI, invoked as `python -m src.signal log-publication|report`), `src/services/concept_exporter.py` (renderer class), `src/services/signal_logger.py` (query + publication writer). Not wired into `src/pipeline.py` — these are standalone user-invoked CLIs, not part of the weekly cron.
  - **Call site**: N/A — new CLIs with no upstream callers. `ConceptExporter` is called only from `src/explore.py`. `SignalLogger` is called from both `src/explore.py` (log_query on every explore) and `src/signal.py` (log_publication, report). Uses the new `GraphStore.upsert_concept`, `log_concept_query`, `log_content_publication`, `loop_report`, `get_relationships`, `get_concept_by_name` methods from TASK-M1-001. Fuzzy resolution: either call into existing `ConceptLinker._find_match` at `src/services/linker.py:115` (note: that method operates on `list[Node]` from legacy `nodes` table — would need adaptation to operate on concept rows) or inline the same `difflib.SequenceMatcher` pattern against the new `concepts` table.
  - **Imports affected**: All new files — no existing importers to update. Pulls `Concept`, `ConceptRelationship`, `ConceptQuery`, `ContentPublication` from `src/models/concepts.py` (new in TASK-M1-001). Pulls `Settings` / `settings` from `src/config.py`.
  - **Runtime files**: Reads `src/config.py` (existing — for `db_path`, `concept_match_threshold`). Writes Markdown exports to `projects/paper-monitoring/exports/` — directory does not exist yet, must be created at runtime (`mkdir -p`). If using a Jinja2 template for the Markdown layout, template file would live at `src/templates/concept_export.md.j2` — does not exist yet (current `src/templates/` contains only `digest.html.j2`, `partials/paper_card.html.j2`, `partials/concept_badge.html.j2`). Alternative: format the Markdown in Python f-strings (no template file needed).
- **Demo Artifact**: The generated `exports/xgboost-YYYYMMDD.md` file, plus a screenshot of `python -m src.signal report --days 30` output. Save both to `docs/paper-monitoring/poc/demos/milestone-1/`.

### TASK-M1-005: GraphExporter (Obsidian vault + Neo4j Cypher) + local setup documentation
- **Status**: Done (2026-04-19)
- **Agent**: data-pipeline (impl), content-writer (README docs), test-validator (QA)
- **Complexity**: M
- **Depends on**: TASK-M1-001, TASK-M1-003
- **Context**: Creates `src/services/graph_exporter.py` with `to_obsidian_vault()` and `to_neo4j_cypher()` methods. CLI wrapper in `src/export.py`: `python -m src.export --format obsidian|neo4j|cytoscape`. README documentation on installing Neo4j Community Edition locally (`brew install neo4j`), loading the Cypher export, and opening the Obsidian vault.
- **Description**: The user-visible deliverable of Milestone 1. The user opens Obsidian and Neo4j Browser against the hand-crafted graph and validates the aspirational UX is met.
- **Acceptance Criteria**:
  - [ ] `python -m src.export --format obsidian` writes a vault at `obsidian_vault/` with one `concepts/<slug>.md` per concept; each file has YAML frontmatter (name, year, domain_tags, source_refs) and body with wikilinks for BUILDS_ON / ALTERNATIVE_TO / PREREQUISITE_OF edges; relationship labels inlined into the body text since Obsidian wikilinks can't carry labels.
  - [ ] `python -m src.export --format neo4j` writes `cypher_exports/graph-YYYYMMDD.cypher` with `CREATE (n:Concept {...})` statements for each concept and `MATCH ... CREATE (a)-[:BUILDS_ON {label:"..."}]->(b)` for each relationship.
  - [ ] `python -m src.export --format cytoscape` writes `exports/graph-YYYYMMDD.json` in Cytoscape `{nodes:[...],edges:[...]}` format.
  - [ ] README section "External Visualization Setup" documents: `brew install neo4j`, `neo4j start`, `cypher-shell -f cypher_exports/graph-*.cypher`, `open http://localhost:7474`, plus "Open Obsidian, add vault at `obsidian_vault/`, open Graph View."
  - [ ] User validates in Obsidian: clicking XGBoost → graph view shows local BUILDS_ON / ALTERNATIVE_TO neighbors; clicking a wikilink in the note recenters the graph on that concept.
  - [ ] User validates in Neo4j Browser: running `MATCH p=(:Concept)-[:BUILDS_ON*1..5]->(:Concept) RETURN p LIMIT 50` shows the XGBoost lineage with labeled edges displaying the narrative labels.
  - [ ] Unit tests cover the three export formats against a canned 3-concept / 4-relationship fixture.
- **Implementation Checklist**:
  - **Schema**: Read-only from `concepts` and `concept_relationships` (both added in TASK-M1-001 — not in current schema). No writes.
  - **Wire**: Two new entry points — `src/export.py` (CLI `python -m src.export --format obsidian|neo4j|cytoscape`) and `src/services/graph_exporter.py` (`GraphExporter` class with `to_obsidian_vault()`, `to_neo4j_cypher()`, `to_cytoscape_json()` methods). Neither file exists yet. Standalone CLI — not invoked from `src/pipeline.py`.
  - **Call site**: N/A — new module with no upstream callers. Uses new `GraphStore.list_concepts` and `get_relationships` from TASK-M1-001.
  - **Imports affected**: All new files. Imports `Concept`, `ConceptRelationship` from `src/models/concepts.py` (new in TASK-M1-001). Reuses existing `normalize_concept_name` from `src/utils/normalize.py` for Obsidian file slugs (currently used by `src/pipeline.py`, `src/seeds/tree_based_prototype.py`, `src/services/seeder.py`, `src/dashboard/app.py`). README edit adds a new "External Visualization Setup" section — `projects/paper-monitoring/README.md` currently has sections 1–5 (Install Ollama, venv, env vars, seed, run); content-writer appends a new section without removing any existing content.
  - **Runtime files**: Writes Obsidian vault to `projects/paper-monitoring/obsidian_vault/` (directory does not exist — created at runtime), Cypher files to `projects/paper-monitoring/cypher_exports/` (does not exist — created at runtime), Cytoscape JSON to `projects/paper-monitoring/exports/` (does not exist — created at runtime). README is an existing file (`projects/paper-monitoring/README.md`) — keeps the `> Built with [Claude Code](https://claude.ai/code)` line per GitHub Rule #4. No config or prompt files read at runtime beyond `src/config.py` for `db_path`.
- **Demo Artifact**: Two screenshots — Obsidian Graph View showing XGBoost lineage, and Neo4j Browser showing the same with labeled edges. Save to `docs/paper-monitoring/poc/demos/milestone-1/TASK-M1-005-obsidian.png` and `TASK-M1-005-neo4j.png`.
- **Notes**: If Neo4j install friction is high, Obsidian-only validation is acceptable as a partial pass — log this as a milestone note and defer Neo4j to early Milestone 2.

---

## Milestone 2: Automated Seed Pipeline on Tree-Based Models (Stage 2 validation)

> **Goal**: Run the full automated seed pipeline (Wikidata SPARQL → Wikipedia API → qwen2.5:14b LLM extraction) against the tree-based models domain. Compare the output concept-by-concept and relationship-by-relationship to the Stage 1 ground truth. User validates that the automated output is close enough in quality to the hand-crafted ground truth to justify scaling.
> **Acceptance Criteria**:
> - The automated pipeline produces a set of tree-based model concepts with all 8 fields populated, written into the `concepts`/`concept_relationships` tables under a distinct `user_id='automated_stage2'`.
> - A diff report compares automated vs. ground truth: coverage (concepts captured / total), relationship type accuracy, label precision (user-judged: "vague" / "adequate" / "precise").
> - User reviews the diff and decides: proceed to Milestone 3 (Stage 3 full extension), OR iterate on prompts in Milestone 2 before scaling.
> - The 15-concept validation eval set from Stage 1 becomes a regression test for any future prompt changes.
> **Demo Gallery**: `docs/paper-monitoring/poc/demos/milestone-2/`
> **Review Checkpoint**: User reviews and approves before Milestone 3 begins.
> **Depends on**: Milestone 1 review passed
> **Status**: To Do

### TASK-M2-001: Wikidata + Wikipedia clients
- **Status**: Done (2026-04-20)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: M
- **Depends on**: Milestone 1 complete
- **Context**: Adds `src/integrations/wikidata_client.py` (SPARQL via SPARQLWrapper) and `src/integrations/wikipedia_client.py` (summary + full content via MediaWiki action API). User-Agent headers hardcoded per Wikidata/Wikipedia policy.
- **Description**: Two new data source clients per DATA-SOURCES §5 and §6. Both are stateless HTTP wrappers with graceful degradation.
- **Acceptance Criteria**:
  - [ ] `WikidataClient.sparql(query)` executes the query with `time.sleep(1)` delay, User-Agent set, returns parsed JSON results.
  - [ ] `WikidataClient.fetch_ml_concept_topology(seed_labels)` returns a list of WikidataTriple Pydantic models (source, target, property, property_label) for the given concept labels.
  - [ ] `WikipediaClient.summary(title)` returns `WikipediaSummary` (title, extract, description) or None on 404.
  - [ ] `WikipediaClient.full_content(title)` returns raw wikitext or None.
  - [ ] On 5xx: retry 3x with exponential backoff; on 429: respect Retry-After.
  - [ ] `SPARQLWrapper` added to `requirements.txt`.
  - [ ] Unit tests with canned JSON/SPARQL responses (no live API calls); one `@pytest.mark.slow` live-smoke-test per client hitting a known concept ("XGBoost" and Q2539).
- **Implementation Checklist**:
  - **Schema**: N/A — these clients are read-only HTTP wrappers. No DB writes.
  - **Wire**: Two new files — `src/integrations/wikidata_client.py` (`WikidataClient`), `src/integrations/wikipedia_client.py` (`WikipediaClient`). Neither file exists. Sibling files in `src/integrations/`: `arxiv_client.py`, `hf_client.py`, `ollama_client.py`, `pdf_extractor.py` (follow their pattern — class with `__init__(cfg)`, instance methods, request/retry inline, `requests` library). No entry point wires them yet — wiring happens in TASK-M2-002 (ConceptExtractor consumes Wikipedia text + Wikidata hints) and TASK-M2-003 (seed pipeline calls both clients).
  - **Call site**: N/A — no callers yet. Added in TASK-M2-002 and TASK-M2-003.
  - **Imports affected**: Both files are new. Pydantic models `WikidataTriple`, `WikipediaSummary` are new — add either to `src/models/wikidata.py` + `src/models/wikipedia.py` (new files, following the pattern of existing `src/models/arxiv.py`, `src/models/huggingface.py`) or into `src/models/concepts.py` extended from TASK-M1-001. Avoid placing them in `src/models/classification.py` (reserved for LLM response models).
  - **Runtime files**: No local files. Reads `requirements.txt` dependency `SPARQLWrapper` (not in current `requirements.txt` — must be added, pinned to `SPARQLWrapper==2.0.0` or equivalent). Hardcoded User-Agent string (per Wikidata policy, should include contact email — stored as a module-level constant in the client file). No config additions required beyond adding User-Agent to `src/config.py:Settings` if centralization is preferred.
- **Demo Artifact**: Terminal recording of a live WikidataClient SPARQL call against "Gradient Boosting" and the returned JSON. Save to `docs/paper-monitoring/poc/demos/milestone-2/TASK-M2-001.txt`.

### TASK-M2-002: ConceptExtractor (qwen2.5:14b + few-shot XGBoost)
- **Status**: Done (2026-04-20)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: L
- **Depends on**: Milestone 1 complete, TASK-M2-001
- **Context**: Replaces the prior `OllamaClassifier.extract_concepts()` method with a new `ConceptExtractor` class in `src/services/concept_extractor.py`. Uses `qwen2.5:14b` via existing `OllamaClient` with schema-constrained output (`format=response_model.model_json_schema()`). Prompt includes the XGBoost lineage ground truth from TASK-M1-002 as the few-shot example. Accepts optional `wikidata_hints` to ground relationship extraction.
- **Description**: The central engine of automated seeding. Takes Wikipedia text (optionally enriched with Wikidata topology) and produces structured 8-field concept records with typed labeled relationships.
- **Acceptance Criteria**:
  - [ ] `ConceptExtractor.extract(text, source_type, source_ref, wikidata_hints=None)` returns `list[ExtractedConceptV2]` matching the full 8-field schema.
  - [ ] System prompt includes full XGBoost ground truth from TASK-M1-002 as the few-shot example (all 8 fields including CONTENT_ANGLES, all 7 relationship types demonstrated).
  - [ ] Relationship types constrained to the 7 enum values; LLM violations are caught in Pydantic validation and retried.
  - [ ] When `wikidata_hints` is supplied, the extractor prompt instructs the LLM to annotate only the hinted edges (rather than invent new topology).
  - [ ] Falls back to `qwen2.5:7b` with WARNING if 14b is not pulled.
  - [ ] On 3 consecutive schema-validation failures, logs WARNING with raw response and returns `[]`.
  - [ ] `qwen2.5:14b` added to README setup instructions (`ollama pull qwen2.5:14b`).
  - [ ] Unit tests with mocked OllamaClient: successful 8-field extraction on a canned XGBoost Wikipedia intro; retry path; fallback to 7b when `ResponseError(message='model not found')`; `wikidata_hints` path produces prompt with hint block present.
- **Implementation Checklist**:
  - **Schema**: N/A — `ConceptExtractor` returns Pydantic models to the caller; persistence happens in TASK-M2-003. The `ExtractedConceptV2` model itself is new — the legacy `ExtractedConcept` at `src/models/classification.py:49` has only `name`, `description`, `domain_tags`, `prerequisite_concept_names` (4 fields, insufficient for the new 8-field schema). Add `ExtractedConceptV2` as a new class; do not delete `ExtractedConcept` (still used by `OllamaClassifier.extract_concepts` at `src/services/classifier.py:216` which is called from `src/pipeline.py:387` in the T5-survey path for the legacy pipeline — stays alive until Milestone 4 cutover).
  - **Wire**: New file `src/services/concept_extractor.py` defining `ConceptExtractor`. Uses existing `OllamaClient` at `src/integrations/ollama_client.py` (which already supports `response_model` via Pydantic `model_json_schema()`). No wiring into `src/pipeline.py` in this task — wiring happens in TASK-M2-003 and TASK-M4-003.
  - **Call site**: No existing callers — new class. The description's phrase "replaces the prior `OllamaClassifier.extract_concepts()`" means functionally, not textually: the old method stays in place; new code calls `ConceptExtractor` instead. `OllamaClassifier.extract_concepts` keeps its one caller at `src/pipeline.py:387` (`_run_knowledge_bank_expansion`) until that code path is removed in TASK-M4-003. `ConceptExtractor`'s first caller lands in TASK-M2-003.
  - **Imports affected**: `ExtractedConceptV2` is a new name — no files currently import it. Do not rename `ExtractedConcept` — existing importers (`src/services/classifier.py`, `src/services/seeder.py`, `src/pipeline.py`) continue to use it. If `ConceptExtractor` also needs `WikidataTriple` for hints, import from the new `src/models/wikidata.py` (TASK-M2-001).
  - **Runtime files**: Reads `src/config.py:Settings.ollama_model` (currently hardcoded `"qwen2.5:7b"`) — add a new setting `ollama_extraction_model: str = "qwen2.5:14b"` in `src/config.py` (line 17-21 Ollama block) or parameterize the model per-call. Few-shot XGBoost example text is loaded at runtime — either embedded as a large string constant in `src/services/concept_extractor.py`, or read from `projects/paper-monitoring/seeds/tree_based_ground_truth/xgboost.md` (from TASK-M1-002 — must exist before this task runs). `README.md` must be updated to add `ollama pull qwen2.5:14b` to the setup section — current README §1 mentions only `qwen2.5:7b`. `.env.example` does not need changes (model name is in `config.py`).
- **Demo Artifact**: Save the prompt + LLM response for XGBoost extraction (live run, qwen2.5:14b) to `docs/paper-monitoring/poc/demos/milestone-2/TASK-M2-002-xgboost-extraction.txt`. Include the generated 8-field record.

### TASK-M2-003: Seed pipeline on tree-based models + diff against ground truth
- **Status**: Done (2026-04-20)
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: M
- **Depends on**: TASK-M2-001, TASK-M2-002
- **Context**: Extends `src/seed.py` with a new CLI mode: `python -m src.seed --automated --domain tree-based`. Orchestrates: seed concept names → Wikidata query for topology → Wikipedia fetch for prose → ConceptExtractor for 8-field records → upsert into concepts/concept_relationships under `user_id='automated_stage2'`. Adds a diff script `src/diff_ground_truth.py` that reports coverage and label precision vs. `user_id='default'` ground truth.
- **Description**: The user-observable Stage 2 deliverable. Run automated pipeline on tree-based domain, produce the comparison report.
- **Acceptance Criteria**:
  - [ ] `python -m src.seed --automated --domain tree-based` runs end-to-end in under 30 minutes on the user's machine with qwen2.5:14b.
  - [ ] The 15 tree-based concept names from ground truth are used as the seed list; pipeline fetches Wikidata + Wikipedia for each, runs LLM extraction, upserts.
  - [ ] `user_id='automated_stage2'` isolates automated output from the ground truth under `user_id='default'`.
  - [ ] `python -m src.diff_ground_truth --domain tree-based` prints: concept coverage (X of 15 found), relationship coverage (X of 30 found), per-relationship type accuracy, label precision (for each automated label, user marks "vague" / "adequate" / "precise" — tool produces an input form or a CSV template).
  - [ ] The diff report is saved to `docs/paper-monitoring/poc/demos/milestone-2/diff-report-YYYYMMDD.md`.
  - [ ] User reviews the diff and the actual automated concept export: `python -m src.explore --user automated_stage2 "XGBoost"` → compare side-by-side with the ground truth export from Milestone 1.
  - [ ] User decision recorded in a milestone review note: "proceed to Milestone 3" OR "iterate on prompts, re-run Milestone 2."
- **Implementation Checklist**:
  - **Schema**: Writes to `concepts` and `concept_relationships` (under `user_id='automated_stage2'` — the `user_id` column is part of the schema added in TASK-M1-001, not in the current schema). Reads both tables for the diff (compares `user_id='default'` ground truth vs `user_id='automated_stage2'`). No new columns in this task.
  - **Wire**: `src/seed.py:main()` at line 200 — extend the existing argparse block with two new flags: `--automated` (action=store_true) and `--domain <name>`. Currently has `--arxiv-id`, `--only-papers`, `--only-textbooks`, `--dry-run`, plus TASK-M1-003's new `--ground-truth`. Add a new branch in `main()` that runs the automated orchestrator when `--automated` is set. The orchestrator is a new function or class (e.g., `src/services/automated_seeder.py:AutomatedSeeder.seed_domain(name)`) that composes: `WikidataClient` (TASK-M2-001) → `WikipediaClient` (TASK-M2-001) → `ConceptExtractor` (TASK-M2-002) → `GraphStore.upsert_concept` + `upsert_concept_relationship` (TASK-M1-001). Second new entry point: `src/diff_ground_truth.py` — standalone CLI (`python -m src.diff_ground_truth`). Also `src/explore.py` (from TASK-M1-004) gains a new `--user <user_id>` flag to target `user_id='automated_stage2'` rows.
  - **Call site**: First caller of `ConceptExtractor` (TASK-M2-002). First caller of `WikidataClient.fetch_ml_concept_topology` and `WikipediaClient.summary`/`full_content` (TASK-M2-001). Existing `Seeder` class at `src/services/seeder.py` is unaffected — the automated path goes through the new orchestrator, not the legacy `Seeder`.
  - **Imports affected**: New file `src/diff_ground_truth.py`. New `src/services/automated_seeder.py` (if using a class) — no existing importers. `src/explore.py` (from TASK-M1-004) gains an optional `user_id` parameter — check that its function signatures remain backward-compatible with existing callers (there are none yet, since TASK-M1-004 introduces it).
  - **Runtime files**: Requires `qwen2.5:14b` pulled in Ollama (runtime precondition — not a file). The 15 tree-based concept seed list is either hardcoded in `src/services/automated_seeder.py` or read from a new YAML at `projects/paper-monitoring/seeds/tree_based_domain.yaml` — does not exist yet, must be created. Writes diff report to `docs/paper-monitoring/poc/demos/milestone-2/diff-report-YYYYMMDD.md` at runtime. Reads ground-truth Markdown files under `projects/paper-monitoring/seeds/tree_based_ground_truth/` (created in TASK-M1-002) for concept-name alignment in the diff. Live HTTP calls to `wikidata.org` and `en.wikipedia.org` — no local mocks.
- **Demo Artifact**: The diff report (Markdown) plus side-by-side export comparison for XGBoost (ground-truth export vs. automated export). Save both to `docs/paper-monitoring/poc/demos/milestone-2/`.

### TASK-M2-004: Regression eval harness for extraction quality
- **Status**: To Do
- **Agent**: test-validator (impl + QA)
- **Complexity**: S
- **Depends on**: TASK-M2-003
- **Context**: Converts the user's quality judgments from TASK-M2-003 into a reusable regression test. Adds `tests/integration/test_extraction_quality.py` that runs ConceptExtractor against the 15 tree-based fixtures and asserts coverage thresholds + relationship-type correctness (not label precision — that stays a human judgment). Marked `@pytest.mark.slow` so it's opt-in.
- **Description**: Lock in Stage 2 quality as a regression baseline so future prompt changes don't silently regress extraction.
- **Acceptance Criteria**:
  - [ ] Test fixture: 15 Wikipedia page summaries (pre-saved as text files) for the tree-based concepts.
  - [ ] `pytest tests/integration/test_extraction_quality.py -m slow` runs ConceptExtractor on each fixture, asserts:
    - [ ] For each fixture, at least 1 concept record is returned.
    - [ ] The primary concept's name (case-insensitive) matches the ground truth.
    - [ ] At least 1 relationship matches the ground truth (type + target, label not checked).
  - [ ] Coverage threshold: >= 80% of fixtures must pass (12 of 15). Below this = regression.
  - [ ] Test is NOT run in regular CI (`slow` marker); user invokes manually when prompt changes.
- **Implementation Checklist**:
  - **Schema**: N/A — this is a test file. No DB writes.
  - **Wire**: New file `tests/integration/test_extraction_quality.py`. Sibling tests in `tests/integration/`: `test_arxiv_live.py`, `test_pipeline_e2e.py`, `test_seeding.py` — follow their pytest conventions (fixtures in `tests/conftest.py`, `@pytest.mark.slow` marker). Pytest already recognizes `slow` marker based on presence of similar `@pytest.mark.slow` usage in `tests/integration/test_arxiv_live.py` — check `pytest.ini` / `pyproject.toml` for marker registration (no `pytest.ini` exists; no `pyproject.toml` found — marker is likely used ad-hoc, so no registration file change needed, but pytest will warn unless it is registered; add `markers = slow: opt-in slow tests` to a new `pytest.ini` if registration is desired).
  - **Call site**: N/A — pytest auto-discovers. Instantiates `ConceptExtractor` (TASK-M2-002) directly with a real `OllamaClient` (not mocked, since this is a live-quality regression test).
  - **Imports affected**: New test file only — no existing imports change. Pulls `ConceptExtractor` from `src/services/concept_extractor.py` (TASK-M2-002), `ExtractedConceptV2` from `src/models/classification.py` (or wherever TASK-M2-002 placed it).
  - **Runtime files**: Reads 15 Wikipedia page summary text fixtures from `projects/paper-monitoring/tests/fixtures/tree_based_wikipedia/` — directory does not exist yet, must be created as part of this task. Each fixture is a `.txt` file containing a pre-saved Wikipedia extract (so test is deterministic without live Wikipedia calls). Ground-truth expectations (expected concept names + expected relationships per fixture) live either in a companion JSON like `tests/fixtures/tree_based_wikipedia/expected.json` (new) or re-parsed from `projects/paper-monitoring/seeds/tree_based_ground_truth/*.md` (TASK-M1-002). Live Ollama runtime required (`qwen2.5:14b` pulled) — the test is `@pytest.mark.slow` and the user runs it manually.
- **Demo Artifact**: Terminal recording of `pytest tests/integration/test_extraction_quality.py -m slow -v` showing all 15 fixtures pass. Save to `docs/paper-monitoring/poc/demos/milestone-2/TASK-M2-004.txt`.

---

## Milestone 3: Full ML/DS/DL Seed (Stage 3 extension)

> **Goal**: Extend the automated pipeline beyond tree-based models to cover major ML/DS/DL concept families (NLP transformers, CNNs, reinforcement learning foundations, classical statistics foundations). The user can run the Concept Explorer on any of these new concepts and produce draft-ready content. The graph browses coherently in Neo4j Browser and Obsidian.
> **Acceptance Criteria**:
> - The concepts table has ≥ 150 distinct concepts after full-seed run (target 200–400, acknowledging Wikidata coverage gaps for post-2020 work).
> - `python -m src.explore "Transformer"` (or RNN, LoRA, SHAP, Gradient Descent, Backpropagation, etc.) produces content-draft-ready exports.
> - User spot-checks 5 concepts from unfamiliar families and confirms output quality matches tree-based expectation.
> - Full graph browse in Neo4j Browser is coherent — cross-family edges (e.g., ATTENTION_MECHANISM BUILDS_ON RECURRENT_NEURAL_NETWORK alternative paths) make sense.
> - **SC-1 of PRD** met: user drafts a real LinkedIn carousel from a Concept Explorer export in < 30 minutes. Recorded as a demo.
> **Demo Gallery**: `docs/paper-monitoring/poc/demos/milestone-3/`
> **Review Checkpoint**: User reviews and approves before Milestone 4 begins.
> **Depends on**: Milestone 2 review passed
> **Status**: To Do

### TASK-M3-001: Seed list expansion — NLP + CV + RL + classical stats concept families
- **Status**: To Do
- **Agent**: architect (drafts the seed list), content-writer (formats it)
- **Complexity**: S
- **Depends on**: Milestone 2 complete
- **Context**: Creates `projects/paper-monitoring/seeds/seed_lists.py` (or YAML) listing concept names grouped by family: NLP transformers (~40), CNNs + CV (~30), reinforcement learning (~30), classical statistics / ML foundations (~30), generative models (~20). Each family is a Python list of canonical concept names (Wikipedia-article-compatible).
- **Description**: The input to the automated pipeline expansion. Not implementation code — a structured list.
- **Acceptance Criteria**:
  - [ ] `seed_lists.py` exports `SEED_FAMILIES: dict[str, list[str]]` with at least 5 families and at least 150 total concept names.
  - [ ] Names are Wikipedia-compatible (e.g., "Transformer (deep learning architecture)" or "Transformer_(machine_learning_model)" — test one via WikipediaClient).
  - [ ] README updated with a "Seed families" section explaining how to add new families.
  - [ ] User reviews and confirms the list is reasonable (~10 min review).
- **Implementation Checklist**:
  - **Schema**: N/A — this task is a data file, not DB code.
  - **Wire**: New file `projects/paper-monitoring/seeds/seed_lists.py` — exports `SEED_FAMILIES: dict[str, list[str]]`. The `seeds/` directory at project root does not exist yet (created by TASK-M1-002 for ground-truth Markdown). This is a second artifact under the same directory. Consumed in TASK-M3-002 by the automated seeder from TASK-M2-003 — `src/services/automated_seeder.py` (or equivalent) imports `SEED_FAMILIES` and iterates families when `--domain all` or `--domain <family>` is passed.
  - **Call site**: `src/services/automated_seeder.py` (TASK-M2-003) — in TASK-M3-002, that module gets a new `--domain all` path that iterates over `SEED_FAMILIES`. Also `src/seed.py:main()` argparse must recognize the `all` value plus any family names declared in `SEED_FAMILIES` for the `--domain` flag (currently only `tree-based` is valid after TASK-M2-003).
  - **Imports affected**: New module `seeds.seed_lists` — no existing importers. The `seeds/` folder needs an `__init__.py` (empty) if Python-importable, or the file can be loaded via `importlib` at runtime (no `__init__.py` needed). Note: there is an unrelated `src/seeds/__init__.py` and `src/seeds/tree_based_prototype.py` from the legacy PoC — do not confuse with the new `seeds/` at project root.
  - **Runtime files**: The file itself is the runtime input. README section "Seed families" must be added — `projects/paper-monitoring/README.md` exists and currently has sections 1–5 plus the "External Visualization Setup" added in TASK-M1-005. Keeps the `> Built with [Claude Code](https://claude.ai/code)` line. One Wikipedia title sanity check during review (via `WikipediaClient` from TASK-M2-001) to confirm at least one sample name resolves.
- **Demo Artifact**: The `seed_lists.py` file itself — link from the demo gallery index.

### TASK-M3-002: Full automated seed run + quality spot-check
- **Status**: To Do
- **Agent**: data-pipeline (runs the pipeline; no code changes expected beyond CLI flag)
- **Complexity**: M
- **Depends on**: TASK-M3-001
- **Context**: Runs `python -m src.seed --automated --domain all` over all seed families. Expected runtime: ~4–8 hours on qwen2.5:14b for 150–300 concepts. User validates quality on ≥ 5 concepts from unfamiliar families.
- **Description**: The actual population run + a qualitative quality check.
- **Acceptance Criteria**:
  - [ ] Pipeline completes without fatal errors (individual concept failures logged but don't halt the run).
  - [ ] `concepts` table (user_id='default' — by this milestone the ground-truth hand-craft is absorbed) has ≥ 150 concepts after run.
  - [ ] User runs `python -m src.explore` on 5 concepts from families OTHER than tree-based (e.g., "Transformer", "Gradient Descent", "Q-Learning", "Variational Autoencoder", "Dropout") and confirms: all 8 fields populated, relationship labels are "adequate" or better, CONTENT_ANGLES are editorially useful.
  - [ ] A spot-check log (`docs/paper-monitoring/poc/demos/milestone-3/spot-check.md`) records the 5 concepts tested and the user's quality judgment.
- **Implementation Checklist**:
  - **Schema**: Writes to `concepts` and `concept_relationships` under `user_id='default'` (promotion from `user_id='automated_stage2'` — whether this means bulk UPDATE of existing Stage 2 rows or a re-run under `default` depends on a decision the user must make during kickoff; AC line 2 of this task implies the absorption). No new columns in this task — all columns already exist from TASK-M1-001.
  - **Wire**: Extends `src/seed.py` `--domain` flag to accept `all` (handled by the automated orchestrator from TASK-M2-003 iterating `SEED_FAMILIES` from TASK-M3-001). A single CLI invocation: `python -m src.seed --automated --domain all`. The seeder orchestrator must catch per-concept failures (Wikidata 404, Wikipedia 404, ConceptExtractor schema failure after 3 retries) and continue — check that TASK-M2-003 already has this graceful-degradation behavior; if not, this task is the forcing function to add it.
  - **Call site**: No new callers — reuses the automated path from TASK-M2-003 + the seed list from TASK-M3-001. Invokes `ConceptExtractor` (TASK-M2-002) hundreds of times.
  - **Imports affected**: None — no new modules. Pure runtime extension.
  - **Runtime files**: Reads `seeds/seed_lists.py` (TASK-M3-001 — must exist). Live Ollama runtime required (`qwen2.5:14b` pulled). Live HTTP calls to Wikidata SPARQL endpoint + Wikipedia API for each of ~150–300 concepts. Writes a run log to `data/logs/` (existing directory — `setup_logging` already writes here per `src/utils/logging_config.py`). Spot-check Markdown written to `docs/paper-monitoring/poc/demos/milestone-3/spot-check.md` at runtime.
- **Demo Artifact**: The spot-check.md + the 5 concept exports. Save all to `docs/paper-monitoring/poc/demos/milestone-3/`.

### TASK-M3-003: PRD SC-1 demo — draft a real LinkedIn carousel from an export
- **Status**: To Do
- **Agent**: none — manual user process
- **Complexity**: S
- **Depends on**: TASK-M3-002
- **Context**: The PoC's primary success criterion SC-1 from PRD §4: user can sit down with an export and draft a LinkedIn carousel in < 30 minutes. This task is the explicit, recorded test of that.
- **Description**: User picks one concept (not XGBoost — the ground truth example shouldn't be the demo), runs the Concept Explorer, drafts a LinkedIn carousel from the export, logs the publication via `src.signal log-publication`.
- **Acceptance Criteria**:
  - [ ] User selects a concept (suggestions: "RLHF", "LoRA", "Mixture of Experts" — something with content energy).
  - [ ] User runs `python -m src.explore "<concept>"` and opens the export.
  - [ ] Within 30 minutes of starting, user has a finished LinkedIn carousel draft (7–10 slides) based on the LINEAGE + KEY_INNOVATIONS + CONTENT_ANGLES fields.
  - [ ] User records the time taken and any points where the export fell short (gap in lineage, weak CONTENT_ANGLES, missing alternative, etc.).
  - [ ] User runs `python -m src.signal log-publication --concept <slug> --channel linkedin --url <URL or "draft">` — even if the post isn't published, log it so the loop instrument captures the usage→draft step.
- **Implementation Checklist**:
  - **Schema**: Reads `concepts` + `concept_relationships` (via `src.explore`), writes one row to `concept_queries` (the explore call) and one row to `content_publications` (the log-publication call). All three tables already added in TASK-M1-001.
  - **Wire**: N/A — no code changes. Uses existing `src/explore.py` (TASK-M1-004) and `src/signal.py` (TASK-M1-004).
  - **Call site**: N/A — manual user workflow.
  - **Imports affected**: N/A.
  - **Runtime files**: Writes one Markdown export under `projects/paper-monitoring/exports/<concept-slug>-YYYYMMDD.md` (directory created at runtime in TASK-M1-004). Writes carousel draft + gap log to `docs/paper-monitoring/poc/demos/milestone-3/TASK-M3-003-carousel-demo.md` at runtime.
- **Demo Artifact**: The LinkedIn carousel draft (text or screenshots) + a brief log of time taken and gaps. Save to `docs/paper-monitoring/poc/demos/milestone-3/TASK-M3-003-carousel-demo.md`.

### TASK-M3-004: Obsidian vault + Neo4j Cypher export for the full graph
- **Status**: To Do
- **Agent**: data-pipeline (runs export), content-writer (README updates)
- **Complexity**: S
- **Depends on**: TASK-M3-002
- **Context**: Re-run the GraphExporter from TASK-M1-005 against the full-seeded graph. Update README's "External Visualization Setup" section with any performance notes (Neo4j Community handles 500+ nodes easily; Obsidian graph view may need filtering for large vaults).
- **Description**: Refresh the external visualization surface with the full graph so the user can browse cross-family connections.
- **Acceptance Criteria**:
  - [ ] `python -m src.export --format obsidian` produces a vault with ≥ 150 concept notes and cross-family wikilinks.
  - [ ] `python -m src.export --format neo4j` produces a Cypher file that loads cleanly into Neo4j Community.
  - [ ] User browses cross-family paths in Neo4j (e.g., `MATCH p=(n:Concept {slug: 'transformer'})-[*1..3]-(m:Concept) RETURN p`) and confirms the edges are coherent and labels are readable.
  - [ ] README updated with any caveats ("Obsidian graph view with 150+ nodes may need the 'Filters' panel to show just a family at a time").
- **Implementation Checklist**:
  - **Schema**: Read-only from `concepts` + `concept_relationships` (both added in TASK-M1-001, populated by TASK-M3-002). No writes.
  - **Wire**: N/A — reuses `src/export.py` CLI and `src/services/graph_exporter.py` from TASK-M1-005. No code changes expected except possibly a performance guard in `GraphExporter.to_obsidian_vault` or `to_neo4j_cypher` if the 150+ concept graph reveals a bottleneck (add `--batch-size` flag only if needed).
  - **Call site**: N/A — same CLI entry as TASK-M1-005.
  - **Imports affected**: None.
  - **Runtime files**: Writes Obsidian vault to `projects/paper-monitoring/obsidian_vault/` (re-populated — deletes prior Milestone 1 contents). Writes Cypher export to `projects/paper-monitoring/cypher_exports/graph-YYYYMMDD.cypher`. Both directories created by TASK-M1-005 at first run. `projects/paper-monitoring/README.md` — append performance caveat to the existing "External Visualization Setup" section from TASK-M1-005. Keeps the `> Built with [Claude Code](https://claude.ai/code)` line.
- **Demo Artifact**: Screenshot of Neo4j Browser showing a cross-family path (e.g., Transformer → Attention Mechanism → RNN → Gradient Descent). Save to `docs/paper-monitoring/poc/demos/milestone-3/TASK-M3-004-neo4j-crossfamily.png`.

---

## Milestone 4: Weekly Monitor — Importance Filter + Trend Resurrection + Pipeline Cutover

> **Goal**: The weekly cron pipeline cuts over from legacy `nodes`/`edges` to the new `papers`/`paper_concept_links` schema. The importance filter is upgraded from simple (upvotes + category) to multi-signal (upvotes + tier + OpenReview + h-index). The trend resurrection signal (citation velocity + HF model adoption) is added. The weekly digest renders both sections.
> **Acceptance Criteria**:
> - Friday cron runs end-to-end against the new schema (papers table, paper_concept_links, citation_snapshots, hf_model_snapshots).
> - Weekly digest at `digests/YYYY-WW.md` has two primary sections: "Must Not Miss" (top-importance new papers) and "Trend Resurrections" (velocity + adoption candidates).
> - User opens the digest file on Monday morning, scans in < 5 minutes, acts on it.
> - PRD SC-4 met (weekly monitor surfaces importance + trend resurrection).
> - Legacy pipeline stops writing to `nodes`/`edges`; legacy tables become read-only historical log.
> **Demo Gallery**: `docs/paper-monitoring/poc/demos/milestone-4/`
> **Review Checkpoint**: User reviews and approves before PoC PHASE-REVIEW.md is drafted.
> **Depends on**: Milestone 3 review passed
> **Status**: To Do

### TASK-M4-001: ImportanceScorer + OpenReview client
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: M
- **Depends on**: Milestone 3 complete
- **Context**: Creates `src/services/importance_scorer.py` (replaces the simple PreFilter formula) and `src/integrations/openreview_client.py` (free registration via `OPENREVIEW_USER`/`OPENREVIEW_PASS` env, with config toggle `importance_use_openreview` defaulting to True). The multi-signal formula from TDD §2.2.1 is configurable via `config.py`.
- **Description**: Upgrade the importance filter. New pipeline order: ingest → tier classify → importance score → trim top-20%.
- **Acceptance Criteria**:
  - [ ] `ImportanceScorer.score(paper, classification, hf, openreview_accepted, author_h_bucket)` returns a float per the TDD §2.2.1 formula.
  - [ ] `OpenReviewClient.is_accepted(arxiv_id)` queries the OpenReview API and returns bool; unauthenticated / failure returns False with log.
  - [ ] Author h-index bucket is a future hook; in PoC `importance_use_h_index=False` default → `author_h_bucket=0` skip.
  - [ ] `ImportanceScorer.select_top(scored, threshold)` trims to top-20% by default (configurable).
  - [ ] Existing `PreFilter` is retained for backward compatibility but the weekly pipeline is wired to use `ImportanceScorer` *after* classification.
  - [ ] Unit tests cover: scoring formula with multiple signal combinations; OpenReviewClient happy path (mocked), failure path, config-disabled path.
- **Implementation Checklist**:
  - **Schema**: N/A — scorer is pure compute, writes nothing. OpenReviewClient is read-only HTTP.
  - **Wire**: Two new files — `src/services/importance_scorer.py` (`ImportanceScorer` class) and `src/integrations/openreview_client.py` (`OpenReviewClient` class). Neither file exists. Full wiring into `src/pipeline.py` happens in TASK-M4-003 (where the Stage 2 → Stage 3 flow gets a new "Stage 2.5: importance scoring" step); this task lays the components. Note: this task's AC "existing `PreFilter` is retained" — confirm no deletions in `src/services/prefilter.py` (currently imported from `src/pipeline.py:26` and used at line 105).
  - **Call site**: No new callers in this task (the pipeline rewire happens in TASK-M4-003). Both new classes are unit-tested in isolation.
  - **Imports affected**: New imports target new names. `src/pipeline.py:26` still imports `PreFilter` — unchanged. `src/models/classification.py:PaperClassification` is read by `ImportanceScorer.score` — already exists at `src/models/classification.py:5`. `src/models/huggingface.py:HFPaper` is read — already exists.
  - **Runtime files**: Reads two new env vars `OPENREVIEW_USER` and `OPENREVIEW_PASS` — add to `projects/paper-monitoring/.env.example` (file must exist per README §3 — verify it does; if not, content-writer creates it). Adds new settings to `src/config.py:Settings` — `importance_use_openreview: bool = True`, `importance_use_h_index: bool = False`, `importance_top_fraction: float = 0.2`, plus signal weights per TDD §2.2.1. Current `Settings` already has `prefilter_top_n`, `prefilter_upvote_weight`, `prefilter_category_priorities` — add importance-scorer settings adjacent to them. No prompt text files read at runtime.
- **Demo Artifact**: A screenshot of `python -m src.pipeline --dry-run` output showing the importance-sorted candidate list with scores broken down by contributing signal. Save to `docs/paper-monitoring/poc/demos/milestone-4/TASK-M4-001.png`.

### TASK-M4-002: TrendResurrector (citation velocity + HF model adoption)
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: L
- **Depends on**: Milestone 3 complete, TASK-M4-001
- **Context**: Creates `src/services/trend_resurrector.py`, `src/integrations/semantic_scholar_client.py`, and extends HuggingFaceFetcher with `fetch_models_by_arxiv`. New tables `citation_snapshots` and `hf_model_snapshots` populated weekly. Cohort defined as papers published 6–24 months ago with citation_count < 50 (see TDD §2.2.3 algorithm).
- **Description**: Build the trend resurrection engine. Weekly batch: snapshot cohort citations, compute 4-week delta, check HF model adoption delta, flag resurrection candidates.
- **Acceptance Criteria**:
  - [ ] `SemanticScholarClient.citation_count(arxiv_id)` returns int or None; respects API key (from env) and rate limit.
  - [ ] `TrendResurrector.snapshot_cohort_citations(cohort)` writes one row per paper to `citation_snapshots`, returns count snapshotted.
  - [ ] `TrendResurrector.detect_velocity_spikes(weeks_lookback=4, threshold=5)` returns list of papers whose delta > threshold.
  - [ ] `TrendResurrector.detect_new_model_adoption(cohort, hf)` compares current HF model set against previous `hf_model_snapshots` row; returns papers with newly-appeared models.
  - [ ] Graceful degradation: missing S2 API key → skip velocity detection with warning; HF failure → skip adoption detection with warning; both down → resurrection section reports "no signals available this week" (not an error).
  - [ ] Cohort cap 500 (configurable) to bound S2 request volume.
  - [ ] Unit tests cover: velocity detection math (4-week delta > threshold); adoption detection diff (new model appears); cohort empty (first week); S2 429 with Retry-After; no API key path.
- **Implementation Checklist**:
  - **Schema**: Writes to `citation_snapshots` and `hf_model_snapshots` — both tables must be added in TASK-M1-001 (not in current schema). Reads `papers` (for cohort selection — papers published 6–24 months ago with citation_count < 50). Uses new `GraphStore.write_citation_snapshot`, `get_citation_delta`, `get_resurrection_cohort` from TASK-M1-001. If `get_resurrection_cohort` signature doesn't accept the 6–24 month + citation_count < 50 filter, extend it here; otherwise reuse as-is.
  - **Wire**: Two new files + one extension. New: `src/services/trend_resurrector.py` (`TrendResurrector` class), `src/integrations/semantic_scholar_client.py` (`SemanticScholarClient` class). Extension: `src/integrations/hf_client.py` gains a new method `fetch_models_by_arxiv(arxiv_id: str) -> list[str]` — `HuggingFaceFetcher` class currently has `fetch_daily_papers` (line 70) and `fetch_week` (line 112); add the new method as a peer, using the `/api/models?filter=arxiv:<id>` HF endpoint. Full wiring into `src/pipeline.py` as Stage 5 happens in TASK-M4-003.
  - **Call site**: New classes — no upstream callers until TASK-M4-003 adds `_run_trend_resurrection()` to `src/pipeline.py`. The new `HuggingFaceFetcher.fetch_models_by_arxiv` method is called from `TrendResurrector.detect_new_model_adoption` — verify `hf_client.py` existing callers (`src/pipeline.py:60` — `_fetch_hf` → `fetcher.fetch_week`) are not affected by adding a new method.
  - **Imports affected**: New files — no existing importers. `hf_client.py` adds one new method; no import changes. Ensure no model class rename occurs in `src/models/huggingface.py` (which currently defines `HFPaper`).
  - **Runtime files**: Reads `SEMANTIC_SCHOLAR_API_KEY` from env — new env var, add to `.env.example`. Add new settings to `src/config.py`: `s2_api_key: str | None = None`, `s2_rate_limit_sleep: float = 1.0`, `trend_cohort_cap: int = 500`, `trend_velocity_threshold: int = 5`, `trend_weeks_lookback: int = 4`. `config.py` currently has the HF block at lines 29–30 — add an adjacent "Semantic Scholar / Trend Resurrection" block. No prompt files.
- **Demo Artifact**: A sample trend-resurrections fragment (Markdown) with ≥ 2 candidates flagged against a seeded cohort (test data). Save to `docs/paper-monitoring/poc/demos/milestone-4/TASK-M4-002-sample.md`.

### TASK-M4-003: Weekly pipeline cutover to new schema + digest renderer update
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: L
- **Depends on**: TASK-M4-001, TASK-M4-002
- **Context**: Rewrites the storage stage of `src/pipeline.py` to write to the new `papers` + `paper_concept_links` tables instead of `nodes` + `edges`. Adds the trend resurrection batch as Stage 5. Updates `src/services/renderer.py` + Jinja2 templates to emit the two-section digest (Must Not Miss / Trend Resurrections) and the companion Markdown (`digest.md.j2`).
- **Description**: The pipeline cutover. After this lands, the legacy `nodes`/`edges` writes stop. Also: update README to reflect the new digest format.
- **Acceptance Criteria**:
  - [ ] `src/pipeline.py` writes to `papers` + `paper_concept_links` instead of `nodes` + `edges` for new papers.
  - [ ] Legacy tables are no longer written to (kept read-only for the dashboard's historical view until it migrates in MVP).
  - [ ] New pipeline stage: `_run_trend_resurrection()` called after `_run_storage_and_rendering()`.
  - [ ] `DigestRenderer` produces both `digests/YYYY-WW.html` and `digests/YYYY-WW.md`; the Markdown version follows UX-SPEC §11.
  - [ ] Digest has two top sections per UX-SPEC: "Must Not Miss" (high-importance new papers), "Trend Resurrections" (velocity + adoption candidates). Tier breakdown and classification failures sections still present below.
  - [ ] Digest header includes: "Monitor run: <timestamp> | Papers evaluated: N | High-importance: M | Resurging: K".
  - [ ] End-to-end integration test (`tests/integration/test_pipeline_e2e.py`) updated to use the new schema; all existing tests pass.
  - [ ] Cron tab entry and `run_weekly.sh` unchanged (no new env variables beyond those already set in Milestone 2).
- **Implementation Checklist**:
  - **Schema**: Writes stop going to legacy `nodes`/`edges` (in `src/pipeline.py:_run_storage_and_rendering` at line 257: `store.upsert_node(paper_node_id, "paper", ...)` and line 262–266: `_linker.link_paper_to_concepts(...)` which writes BUILDS_ON edges). Writes now go to `papers` (via new `GraphStore.upsert_paper`) and `paper_concept_links` (via `GraphStore.link_paper_to_concept`) — both added in TASK-M1-001. Also writes `citation_snapshots` + `hf_model_snapshots` via Stage 5. Legacy `nodes`/`edges` tables remain but no new writes — confirm the dashboard at `src/dashboard/app.py` still reads them via `store.get_all_papers` (line 231) and `store.get_all_concepts` (line 298) without error (those methods only query `nodes`/`edges` — they won't see new papers but won't crash).
  - **Wire**: Major edits to `src/pipeline.py` at these specific sites:
    - `_run_storage_and_rendering` (line 201) — replace `store.upsert_node(paper_node_id, "paper", ...)` at line 257 with `store.upsert_paper(paper_record)`; replace `_linker.link_paper_to_concepts(paper_node_id, concept_names, store)` at line 262 with the equivalent call that writes to `paper_concept_links`. `ConceptLinker` at `src/services/linker.py:31` currently writes BUILDS_ON edges to the `edges` table via `store.upsert_edge` (line 105); add a new method `ConceptLinker.link_paper_to_concept_rows` or rewrite the existing one — decide in implementation. `paper_node_id` string convention `"paper:{arxiv_id}"` (line 256) may become just `arxiv_id` if `papers.arxiv_id` is the PK.
    - New function `_run_trend_resurrection(store, cfg)` added after `_run_storage_and_rendering`. Invoked from `run_pipeline` (line 417) after Stage 3 (`_run_storage_and_rendering` call at line 469) and before the existing Stage 4 (`_run_knowledge_bank_expansion` at line 476). Decision point: does Stage 4 (T5 survey expansion) stay or retire? AC says "_run_trend_resurrection called after _run_storage_and_rendering" — Stage 4 probably retires or is gated off once the automated seed from Milestones 2-3 replaces T5 surveys as the concept source. Confirm during implementation.
    - `DigestRenderer` at `src/services/renderer.py:13` — extend `render()` to produce both `.html` and `.md` outputs. Currently line 55 only loads `digest.html.j2`. Add loading of a new `digest.md.j2` template (does not exist yet — create at `src/templates/digest.md.j2`). Add new sections "Must Not Miss" and "Trend Resurrections" in both templates, alongside existing tier breakdown.
  - **Call site**: `_run_storage_and_rendering` callers: only `run_pipeline` at line 469. `_run_trend_resurrection` is new, one caller: `run_pipeline`. `DigestRenderer.render` callers: only `_run_storage_and_rendering` at line 283 — signature change (returning two paths, or keeping single path + writing second file as side effect) must be checked by the one caller. The E2E test at `tests/integration/test_pipeline_e2e.py` queries legacy `store.get_edges_from(f"paper:{arxiv_id}", "BUILDS_ON")` in multiple places (lines 367, 374, 381, 400) — must be rewritten to query `paper_concept_links` (via new `GraphStore.get_concept_links_for_paper` or similar). Same for tests at lines 339 (`test_paper_nodes_upserted`), 364 (`test_builds_on_edges_for_paper_001`), 371, 378, 397. Unit tests in `tests/unit/test_linker.py` and `tests/unit/test_renderer.py` will need updates if signatures change.
  - **Imports affected**: No class renames required, but the story is more subtle:
    - If `ConceptLinker.link_paper_to_concepts` is rewritten to target `paper_concept_links`, then its one caller at `src/pipeline.py:262` stays put syntactically but semantically changes. Its other caller is `src/services/seeder.py:125` (legacy seeding path — must decide: rewire to new schema, or leave seeder on legacy path since seeder is being replaced by automated seeder from Milestones 2–3).
    - If a new method is added instead (e.g., `link_paper_to_concept_rows`), existing `link_paper_to_concepts` is left intact for the legacy seeder; `src/pipeline.py` switches to calling the new method.
    - `store.get_papers_for_digest` at `graph_store.py:625` currently queries the legacy `nodes` table — this is called from the dashboard (`src/dashboard/app.py`) and possibly from renderer/templates. Confirm which surface uses it and decide whether to add a parallel `get_papers_v2` method or rewrite. The templates (`src/templates/digest.html.j2`, `partials/paper_card.html.j2`, `partials/concept_badge.html.j2`) currently render `DigestEntry` from `src/models/graph.py:57`; DigestEntry composition may need to change to include importance score + resurrection flags (backward-incompatible change — every renderer test updates).
  - **Runtime files**: Reads templates at runtime from `src/templates/` — existing files `digest.html.j2`, `partials/paper_card.html.j2`, `partials/concept_badge.html.j2` (all present). Must CREATE `src/templates/digest.md.j2` (new — does not exist). Writes digest files to `projects/paper-monitoring/digests/` — directory exists (has `.gitkeep`). `run_weekly.sh` at `projects/paper-monitoring/run_weekly.sh` — verified, AC says unchanged (no new env vars beyond Milestone 2 additions). README `projects/paper-monitoring/README.md` — update the "What the digest contains" section (if present) to describe the two new sections; keep `> Built with [Claude Code](https://claude.ai/code)` line. No prompt text files beyond what Milestones 2 and 4 already added.
- **Demo Artifact**: A fully-rendered `digests/2026-WXX.md` from a dry-run with seeded cohort + fresh arXiv pull. Save to `docs/paper-monitoring/poc/demos/milestone-4/TASK-M4-003-digest.md`.

### TASK-M4-004: End-to-end validation against PRD SC-4 (weekly monitor in practice)
- **Status**: To Do
- **Agent**: none — manual user process
- **Complexity**: S
- **Depends on**: TASK-M4-003
- **Context**: Let the new cron run for one real Friday cycle against the live ecosystem. User reviews the resulting digest on Monday and confirms: (a) scannable in < 5 min, (b) high-importance section surfaces papers the user actually wants to read, (c) trend resurrection section surfaces things that are meaningfully accelerating. Any failure here is a Milestone 4 review flag.
- **Description**: The PoC's final validation gate. Real run, real data, real weekly workflow.
- **Acceptance Criteria**:
  - [ ] Cron fires on Friday, runs end-to-end without error.
  - [ ] Monday morning: user opens `digests/YYYY-WW.md`.
  - [ ] User reads it in < 5 minutes, notes which papers they would read and which resurrection candidates they find genuinely interesting.
  - [ ] User records the validation in a Markdown note with three judgments: (a) completeness of high-importance section, (b) precision of high-importance section (would I read these?), (c) usefulness of resurrection section.
  - [ ] At least one concept from the digest is explored via `python -m src.explore` (closes the loop with Milestone 3's Concept Explorer).
- **Implementation Checklist**:
  - **Schema**: Read-only — user reviews the digest file that TASK-M4-003 produced. Implicit reads: `papers`, `paper_concept_links`, `citation_snapshots`, `hf_model_snapshots`, `concept_queries` (when the user runs `src.explore` on a concept from the digest). Writes: one row to `concept_queries` via the explore call.
  - **Wire**: N/A — no code changes. Exercises the full Friday cron path end-to-end: `run_weekly.sh` → `python -m src.pipeline` → `run_pipeline()` at `src/pipeline.py:417` through all stages including the new trend resurrection.
  - **Call site**: N/A — manual user workflow.
  - **Imports affected**: N/A.
  - **Runtime files**: Reads the digest Markdown produced by TASK-M4-003 at `projects/paper-monitoring/digests/YYYY-WW.md`. Writes validation note to `docs/paper-monitoring/poc/demos/milestone-4/TASK-M4-004-validation.md`. The Friday cron needs Ollama running (`run_weekly.sh` already starts it at line 27–44 via `open -a Ollama`); the user must verify that `qwen2.5:14b` is pulled (required after TASK-M2-002) and `SEMANTIC_SCHOLAR_API_KEY` + `OPENREVIEW_USER`/`OPENREVIEW_PASS` env vars are set in `.env` (from TASK-M4-001 and TASK-M4-002). Cron schedule remains as documented in `run_weekly.sh` header (`0 18 * * 5 caffeinate -i ...`).
- **Demo Artifact**: The Monday review note + the digest it reviews. Save to `docs/paper-monitoring/poc/demos/milestone-4/TASK-M4-004-validation.md`.

---

## Dependency Graph

```
Milestone 1 (Schema + Stage 1 Manual)
  TASK-M1-001 (Schema DDL) ────────────────────┐
         |                                     |
         v                                     v
  TASK-M1-002 (Hand-craft 15 concepts) ──► TASK-M1-003 (Seed loader)
                                               |
                                               v
                                          TASK-M1-004 (Explorer CLI + signal)
                                               |
                                               v
                                          TASK-M1-005 (GraphExporter — Obsidian + Neo4j)
                                               |
                                               v  [USER REVIEW GATE]
                                               |
Milestone 2 (Stage 2 Automated on Tree-based)  |
  TASK-M2-001 (Wikidata + Wikipedia) ──────────┤
  TASK-M2-002 (ConceptExtractor 14b) ──────────┤
         |                                     |
         v                                     v
  TASK-M2-003 (Seed run + diff report) ──► TASK-M2-004 (Regression eval)
                                               |
                                               v  [USER REVIEW GATE]
                                               |
Milestone 3 (Stage 3 Full Seed)                |
  TASK-M3-001 (Seed list expansion)            |
         |                                     |
         v                                     v
  TASK-M3-002 (Full seed run + spot-check) ──► TASK-M3-003 (LinkedIn carousel demo)
                                               |
                                               v
                                          TASK-M3-004 (Full graph export)
                                               |
                                               v  [USER REVIEW GATE]
                                               |
Milestone 4 (Weekly Monitor + Cutover)         |
  TASK-M4-001 (ImportanceScorer + OpenReview) ─┤
         |                                     |
         v                                     v
  TASK-M4-002 (TrendResurrector) ─────────► TASK-M4-003 (Cutover + new digest)
                                               |
                                               v
                                          TASK-M4-004 (E2E validation SC-4)
                                               |
                                               v  [POC COMPLETE — PHASE-REVIEW.md]
```

---

## Completed Milestones Log

### Milestone 1 — Approved 2026-04-20

**Milestone**: Schema Redesign + Stage 1 Manual Prototype (tree-based models)
**Approved by**: User (no revision notes)
**BA verdict**: ALIGNED

**Tasks**: TASK-M1-001, TASK-M1-002, TASK-M1-003, TASK-M1-004, TASK-M1-005 — all Done (2026-04-19)
**Demo Gallery**: `docs/paper-monitoring/poc/demos/milestone-1/`

**Outcome**: User validated the concept graph in Obsidian (wikilink navigation) and Neo4j Browser (BUILDS_ON lineage with labeled edges). Schema confirmed as the foundation for Milestone 2 automated extraction. Two bugs fixed during validation (wikilink slug mismatch, missing Limitations section). BL-012 and BL-013 logged to BACKLOG.md.
