# Phase Review --- Paper Monitoring / PoC

> **Phase completed**: 2026-04-16
> **Reviewed by**: architect
> **User approved**: [x] Yes — 2026-04-16

## Phase Summary
- **Goal**: Prove that a zero-cost, fully local pipeline can ingest arXiv papers weekly, classify them by a 5-tier importance taxonomy using a 7B local LLM, link them to a seeded knowledge bank of foundational concepts, and produce a useful digest --- all without paid APIs or cloud infrastructure.
- **Outcome**: Goal met. The pipeline runs end-to-end unattended, classifies papers with structured output, links to a knowledge bank that exceeded the target size, and renders both an HTML digest and a Streamlit dashboard. All 6 PRD success criteria passed.
- **Duration**: 2026-04-13 to 2026-04-16 (4 days)
- **Milestones completed**: 8 of 8 (28 tasks across 8 sprints, all Done)

## Success Criteria Results

| Criterion | Target | Result | Verdict |
|-----------|--------|--------|---------|
| SC-1: Unattended pipeline | cron fires, pipeline runs without intervention | cron installed, pipeline verified end-to-end from dashboard and cron | PASS |
| SC-2: 3-5 valuable papers per digest | User considers papers genuinely valuable | 30 papers classified per run (T3:24, T4:4, T5:2). Summaries adequate for PoC; richer extraction deferred to MVP | PASS |
| SC-3: Tier + summary + concepts per paper | Every paper has structured classification output | All fields populated --- tier, confidence, summary, key_contributions, concept links. Verified via SkillClaw (2604.08377) | PASS |
| SC-4: 150-300 foundational concepts | Knowledge bank breadth | 492 concepts from 17 landmark papers, 9 surveys, 2 textbooks, + weekly expansion | EXCEEDED |
| SC-5: Zero ongoing cost | No paid APIs, no cloud | Ollama local (qwen2.5:7b), arXiv free, HF free | PASS |
| SC-6: Dashboard at localhost:8501 | Cards, filter, pipeline trigger | Streamlit app with paper cards, tier filter, Knowledge Bank tab, subprocess pipeline trigger | PASS |

## Key Stats

- **Tasks**: 28 completed, 0 remaining, 2 deferred to backlog (TASK-029, TASK-030)
- **Tests**: 250, all passing
- **Pipeline throughput**: 10,312 papers fetched -> 30 pre-filtered -> 30 classified -> digest rendered
- **Classification runtime**: ~15 minutes on Apple Silicon M4 (30 papers at ~30s each with qwen2.5:7b, ollama_timeout=300s)
- **Knowledge bank**: 492 concepts, grown from 166 (papers/surveys) to 389 (textbooks) to 492 (weekly T5 expansion)
- **Seeding sources**: 17 landmark papers, 9 surveys, 2 textbooks (Murphy PML: 3 chapters, Sutton RL: 3 chapters), 45 textbook chunks processed with zero extraction failures

## What Worked

1. **Graph-first schema (nodes + edges in SQLite)**. The decision to use proper graph tables rather than embedded JSON arrays paid off immediately --- clean queries for concept linking, prerequisite traversal, and knowledge bank expansion. The schema maps directly to a future graph database migration without restructuring.

2. **Schema-constrained Ollama output**. The critical fix of the entire PoC. `format="json"` alone was insufficient --- qwen2.5:7b returned free-form JSON summaries instead of the expected Pydantic structure. Switching to `format=response_model.model_json_schema()` forces the model to emit the exact schema. Without this, the entire classification pipeline would have been unreliable. This pattern should be carried forward to every Ollama integration.

3. **T5 survey auto-expansion of knowledge bank**. The "learning loop" where T5 (survey) papers automatically get concept extraction after classification. The knowledge bank grew from 470 to 492 concepts in a single pipeline run. Over months, this compounds. This is also the project's commercial signal instrument.

4. **Source-type-aware concept extraction prompts**. Different source types (landmark: 1-3 concepts, survey: 20-40, textbook: 5-15 per chunk) produce dramatically different quality. A one-size-fits-all prompt would either under-extract from surveys or over-extract noise from individual papers.

5. **Subprocess pipeline execution from dashboard**. Using `subprocess.Popen` instead of threading means the pipeline survives browser refresh and page navigation. The reader thread + queue pattern provides live progress without coupling the pipeline to Streamlit's rerun model.

6. **30-day arXiv lookback with top-30 pre-filter**. Papers published late in the week need time to accumulate HF upvotes. The 30-day window provides a fairer scoring opportunity while `paper_exists()` deduplication prevents re-processing. Reducing `prefilter_top_n` from 100 to 30 cut runtime from ~50 minutes to ~15 minutes --- critical for a local-only system.

7. **Documentation-first workflow with milestone-based delivery**. Every sprint produced a testable deliverable. The PRD success criteria were written before any code and served as the final validation checklist. No scope ambiguity.

## What Didn't Work

1. **`format="json"` was not enough for structured output.** This cost significant debugging time. The Ollama documentation implies `format="json"` produces structured output, but qwen2.5:7b treats it as "output some JSON" rather than "output this specific JSON structure." The fix (schema-constrained format) should be the default pattern going forward.
   - **Impact**: Delayed textbook seeding (TASK-027) until the root cause was found and fixed. All prior Ollama calls worked only because they happened to match the expected structure by luck (shorter prompts, simpler schemas).

2. **Textbook page ranges were initially incorrect.** The first attempt at seeding used guessed page ranges that didn't match the actual table of contents. TOC inspection was needed for each PDF.
   - **Impact**: Required manual correction. For MVP (BL-002: 5 books, ~86 chapters), every page range must be TOC-verified upfront.

3. **arXiv 429 rate limit treated as fatal 4xx.** The original retry logic retried only on 5xx and aborted on all 4xx. arXiv returns 429 (Too Many Requests) when the 3-second courtesy delay is insufficient during high-traffic periods. Fixed during TASK-023 to retry with backoff using the `Retry-After` header.
   - **Impact**: Pipeline would have silently failed during peak arXiv traffic. Fixed.

4. **Dashboard search is flat text match.** Searching for "attention" returns every concept that mentions "attention" in any field, burying the actual "Attention Mechanism" concept. No field-priority ranking.
   - **Impact**: Knowledge Bank tab search is near-useless for targeted lookup. BL-008 addresses this for MVP.

5. **Classification output is too shallow.** Current extraction produces a 1-sentence summary and 2 bullet points for key_contributions. Not enough to understand what a paper actually does without reading it. The user's SkillClaw example demonstrated this gap clearly.
   - **Impact**: The core value proposition ("understand papers without reading them") is only partially met. BL-007 (concept-first schema) addresses this with structured Problem/Technique/Paper decomposition.

6. **4-week prompt validation was not completed.** The original TASK-017 planned 4 weeks of subjective prompt tuning. This was shortened to a single end-to-end production validation because the MVP will completely rewrite prompts under BL-007's new extraction schema, making PoC prompt tuning wasted effort.
   - **Impact**: Prompt quality for the current tier taxonomy is "good enough for PoC" but not validated over time. Acceptable --- the prompts will be rewritten.

## Known Technical Debt

| Area | Description | Severity | Recommended Phase |
|------|-------------|----------|-------------------|
| Ollama client | No LLM abstraction layer --- OllamaClient is called directly everywhere. Adding a second model (e.g., larger model for richer extraction) requires touching every caller | Medium | MVP (when evaluating qwen2.5:7b vs larger models for BL-007 extraction) |
| Concept matching | `difflib.SequenceMatcher` fuzzy matching (ratio >= 0.85) will not scale beyond ~500 concepts. O(n) scan per paper, no indexing | Medium | MVP (after BL-002 pushes concept count toward 800+) |
| Search | Flat text match across all fields, no ranking, no prefix matching | Medium | MVP (BL-008) |
| Concept relationships | Single `BUILDS_ON` edge type is too coarse --- doesn't distinguish prerequisites from alternatives or baselines | High | MVP (BL-007 introduces ADDRESSES, BASELINE_OF, ALTERNATIVE_TO) |
| Knowledge bank structure | Flat --- no taxonomy, hierarchy, or grouping. 492 concepts with no navigable structure | High | MVP (BL-009 concept taxonomy) |
| User engagement | System has zero memory of what the user has read, flagged, or annotated. Knowledge bank feels static, not personal | High | MVP (BL-011 user interaction layer) |
| Inline CSS | All HTML digest styling is inline in Jinja2 templates. Intentional PoC shortcut | Low | Never (digest may be replaced by dashboard-only workflow in MVP) |
| Database migrations | No migration tooling. Schema changes require manual ALTER TABLE or database rebuild | Medium | MVP (before BL-007 schema migration) |
| Textbook coverage | Only 2 of 5 target textbooks seeded (6 chapters of ~86 total). PDFs downloaded, configs written, code ready --- just needs Ollama runtime | Low | MVP (BL-002, run early) |

## Unresolved Backlog

Items from BACKLOG.md not addressed in this phase:

| Backlog ID | Description | Priority Reassessment | Recommendation |
|-----------|-------------|----------------------|----------------|
| BL-007 | Knowledge graph redesign --- concept-first schema with Problem, Technique, Concept, Category, Paper node types and 7 relationship types | High (unchanged) | **Promote first** --- everything else builds on this schema |
| BL-002 | Comprehensive textbook seeding (5 books, ~86 chapters) | High (unchanged) | Promote early --- expands knowledge bank before new schema is populated |
| BL-003 | Semantic concept deduplication (embedding-based) | High (unchanged) | Promote --- depends on BL-002 expanding concept count |
| BL-009 | Concept taxonomy (auto-generated hierarchical grouping) | High (unchanged) | Promote --- pairs with BL-007 (Category node type) |
| BL-010 | "What changed in my graph" digest section + trending + content opportunities | High (unchanged) | Promote layers 1-2 for MVP daily use. Layer 3 (content opportunities) can wait |
| BL-011 | User interaction layer (read status, notes, last accessed, flagged) | High (unchanged) | Promote --- prerequisite for BL-010 personalization and prevents KB abandonment |
| BL-004 | Paper decomposition (problem / solution / result) | High -> Subsumed | **Subsumed by BL-007** --- the concept-first schema includes structured extraction |
| BL-006 | Split concept relationships (prerequisites vs alternatives) | High -> Subsumed | **Subsumed by BL-007** --- new relationship types cover this |
| BL-008 | Search ranking (concepts first, field-priority matching) | Medium (unchanged) | Promote --- applies regardless of whether UI stays Streamlit or moves to graph viz |
| BL-001 | Knowledge graph visualization (primary dashboard UI) | Medium (unchanged) | Promote for MVP --- natural fit for graph-native data model |
| BL-005 | External learning gateway (NotebookLM integration) | Medium (unchanged) | Defer --- investigate NotebookLM API capabilities first, low urgency |

## Commercial Signal Results

- **Instrument**: T5 survey auto-expansion of knowledge bank. Measures whether the system "gets smarter" over time by organically growing its concept vocabulary from weekly survey papers.
- **Data collected**: In the first production pipeline run, 2 T5 surveys were classified. Concept extraction produced 22 new concepts, growing the knowledge bank from 470 to 492. The system correctly identified survey papers (not misclassifying research papers as surveys) and the extracted concepts were relevant to their source surveys.
- **Interpretation**: The mechanism works. A single weekly run produced measurable knowledge bank growth. Over 3+ months of weekly runs, this should compound meaningfully --- each new concept improves future classification accuracy by expanding the concept index. The compounding effect is the commercial thesis: the longer you use it, the smarter it gets.
- **Recommendation**: Continue measuring. Track knowledge bank size over time (weekly snapshot). After 3 months of MVP use, evaluate: (a) is the growth rate sustaining or flattening? (b) are the auto-extracted concepts high quality or noisy? (c) does the expanded concept index measurably improve classification linking? These answers inform the Beta decision.

## Recommendations for Next Phase

### 1. Prioritize

**BL-007 (concept-first schema redesign) must be the first MVP milestone.** Every other backlog item depends on or benefits from this new schema:
- BL-004 and BL-006 are subsumed by it
- BL-009 (taxonomy) needs the Category node type it introduces
- BL-010 (graph changes digest) needs the richer edge types to compute meaningful deltas
- BL-011 (user interaction) needs the new Paper node fields
- BL-001 (graph visualization) needs the richer graph structure to be worth building
- BL-003 (semantic dedup) benefits from richer concept descriptions

**BL-002 (textbook seeding) should run immediately after BL-007.** The code and configs already exist. Running seeding early maximizes knowledge bank coverage before the new schema is populated by weekly runs. Estimated ~5 hours of Ollama processing.

**BL-011 (user interaction layer) should be the third milestone.** Preventing knowledge base abandonment (the #1 PKM failure mode) is more urgent than visualization polish.

### 2. Defer

- **BL-005 (NotebookLM integration)**: Low urgency. Investigate API capabilities but don't build until the core schema and interaction layer are solid.
- **BL-010 layer 3 (content opportunities)**: Only relevant when the user begins active content creation. Layers 1-2 ("what changed this week" and "trending concepts") are MVP-ready and high-value.
- **Custom trained classifier**: Not needed until 6+ months of labeled data accumulates. qwen2.5:7b with schema-constrained output is sufficient for now.

### 3. Reconsider

- **Is qwen2.5:7b sufficient for the richer extraction?** BL-007's concept-first schema requires extracting Problem, Technique, and structured fields (approach, innovation type, practical relevance, limitations) from paper abstracts. This is significantly more demanding than the current tier + summary + key_contributions extraction. Test qwen2.5:7b against the new prompts early in MVP. If quality is insufficient, evaluate qwen2.5:14b or phi4:14b (both fit in 16 GB RAM on Apple Silicon). The zero-cost constraint still holds --- just need a larger local model.

- **Database migration strategy.** BL-007 changes the graph schema significantly (new node types, new edge types, new fields). The PoC has no migration tooling. Before implementing BL-007, decide: (a) add lightweight migration scripts (recommended), or (b) rebuild the database from scratch (acceptable if seeding is fast enough). Option (b) is simpler but loses the existing weekly pipeline data.

- **Streamlit vs. dedicated graph visualization.** The current Streamlit dashboard was adequate for PoC but BL-001 envisions an interactive node-edge graph. Evaluate whether a Streamlit-embedded library (e.g., streamlit-agraph, pyvis) is sufficient or whether a dedicated frontend (React + D3/Cytoscape.js) is needed. The MVP should stay with Streamlit unless the visualization requirements clearly outgrow it.

### 4. New Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| qwen2.5:7b cannot reliably extract Problem/Technique/Concept decomposition from abstracts | Medium | High | Test with 10 papers early in BL-007. Fall back to qwen2.5:14b or phi4:14b if needed |
| Schema migration breaks existing pipeline data | Medium | Medium | Write idempotent migration scripts. Back up database before migration. Consider rebuild-from-scratch if migration is complex |
| Concept count beyond 800 degrades fuzzy matching performance | High | Low | BL-003 (semantic dedup) reduces count; also consider indexing or embedding-based lookup to replace difflib |
| Auto-generated taxonomy (BL-009) produces incoherent groupings | Medium | Medium | LLM proposes, user reviews and corrects. Start with a small taxonomy and grow iteratively |
| Weekly cron job fails silently during MVP development | Low | Low | Cron remains installed. Check `data/logs/pipeline.log` weekly. Add digest-written notification (email or desktop notification) if silent failures occur |

## Updated Roadmap

**MVP focus areas (in milestone order):**

1. **Milestone 1: Schema redesign (BL-007)** --- New node types (Problem, Technique, Concept, Category, Paper), new edge types (ADDRESSES, BASELINE_OF, ALTERNATIVE_TO, INTRODUCES, BUILDS_ON, PREREQUISITE_OF, BELONGS_TO), migration scripts, prompt rewrite, Pydantic model updates
2. **Milestone 2: Knowledge bank expansion (BL-002 + BL-003)** --- Full textbook seeding across 5 books (~86 chapters), followed by semantic deduplication to clean up the expanded concept set
3. **Milestone 3: User interaction layer (BL-011)** --- Read status, inline notes, last accessed, flagged-for-review on paper cards
4. **Milestone 4: Concept taxonomy (BL-009)** --- Auto-generated hierarchical grouping of concepts, LLM-proposed with user adjustment
5. **Milestone 5: Graph changes digest (BL-010 layers 1-2)** --- "What changed in my graph this week" section with trending concepts
6. **Milestone 6: Search and visualization (BL-008 + BL-001)** --- Ranked search with field priority, graph visualization as primary navigation UI

**Features to drop or defer:**
- BL-005 (NotebookLM integration): Defer to late MVP or Beta
- BL-010 layer 3 (content opportunities): Defer until user begins content creation
- Custom trained classifier: Defer to Beta (needs 6+ months of labeled data)
- Full website hosting: Remains out of scope for MVP

**Timeline expectation:** MVP should target ~3 months of iterative development and daily use, validating each milestone before proceeding to the next. The cron job continues running weekly throughout, providing ongoing data and regression validation.

## Verdict

**PASS.** The PoC achieved all 6 success criteria. The pipeline ingests, classifies, links, and renders papers without manual intervention or paid services. The knowledge bank exceeded its target size and demonstrated organic growth through the T5 auto-expansion mechanism. The schema-constrained Ollama output pattern and graph-first SQLite design are solid foundations for the MVP.

The PoC also successfully surfaced the project's most important insight through the user's design conversation: **concepts are primary citizens, papers are supporting evidence.** This reframes the entire MVP around BL-007's concept-first schema rather than incremental improvements to the current paper-centric model.

The project is ready for MVP phase transition. The recommended starting point is BL-007 (concept-first schema redesign), which is the foundational change that every other MVP feature depends on.
