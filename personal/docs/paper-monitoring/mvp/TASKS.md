# Task Breakdown — Paper Monitoring (MVP)

> **Status**: Active
> **Phase**: MVP
> **Last Updated**: 2026-04-17
> **Depends on**: PRD.md (MVP), TDD.md (MVP), DATA-SOURCES.md (MVP) — all must be approved

## Progress Summary
| Status | Count |
|--------|-------|
| Done | 0 |
| In Progress | 0 |
| To Do | 28 |
| Blocked | 0 |

---

## Milestone 1: "I can see and edit a hand-crafted knowledge graph"

> **Goal**: An interactive, editable graph of ~15 hand-crafted tree-based model concepts. The user validates the schema, relationship types, and editing UX before any LLM touches the graph. The test domain is **tree-based models** (Decision Tree, Random Forest, Gradient Boosting, XGBoost, LightGBM, CatBoost) — the user has full mastery and can immediately judge quality.
> **Acceptance Criteria**:
> - Graph visualization shows ~15 nodes with all 7 relationship types represented
> - User can click a node, see its properties, and edit them inline
> - User can add a new node, add an edge between two nodes, delete an edge, and delete a node — all through the UI
> - Relationships are correct and useful for the tree-based domain (user validates from domain expertise)
> - Nodes and edges track `edited_by: "user" | "llm"` for provenance
> **Observable Deliverable**: Interactive, editable graph of tree-based models in the Streamlit dashboard
> **Review Checkpoint**: User reviews and approves before Milestone 2 begins
> **Status**: To Do

### TASK-001: Pydantic Models for Concept-First Schema
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Small
- **Depends on**: None
- **Context**: TDD Section 10. New models: `PaperAnalysis`, `SearchResult`, `WeeklyChanges`, `TrendingTopic`, `CategoryProposal`, `AnalysisLinks`. Retain `PaperClassification` for backward compatibility. All node/edge models must include `edited_by: str` field (`"user"` or `"llm"`) for provenance tracking.
- **Description**: Create all new Pydantic models defined in the MVP TDD. These are data contracts used by every new component.
- **Acceptance Criteria**:
  - [ ] `PaperAnalysis` model with all fields: problem, technique, tier, results_vs_baselines, linking fields, failure handling
  - [ ] `SearchResult`, `WeeklyChanges`, `TrendingTopic`, `CategoryProposal`, `AnalysisLinks` models match TDD definitions
  - [ ] All node/edge property models include `edited_by: str` field (default `"llm"`, set to `"user"` for manual edits)
  - [ ] `PaperClassification` retained unchanged for backward compatibility
  - [ ] Unit tests validate construction, defaults, and required field enforcement for all new models

### TASK-002: GraphStore Mutation Methods for Manual Editing
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Small
- **Depends on**: TASK-001
- **Context**: TDD Section 2.4.6. GraphStore needs full CRUD for the editing UI. Existing methods cover `upsert_node`, `upsert_edge`, `get_node`, `get_edges_from/to`. New methods: `delete_node()`, `delete_edge()`, `update_node_properties()`, `add_node()` (alias for upsert with existence check), `add_edge()` (alias for upsert with existence check). Also add `get_technique_index()`, `get_problem_index()`, `get_nodes_created_since()`, `get_edges_created_since()` for later milestones.
- **Description**: Add mutation and query methods to GraphStore so the UI and pipeline can create, update, and delete any node or edge.
- **Acceptance Criteria**:
  - [ ] `delete_node(node_id)` removes the node and all connected edges; returns count of removed edges
  - [ ] `delete_edge(source_id, target_id, relationship_type)` removes a specific edge
  - [ ] `update_node_properties(node_id, properties_patch)` merges a partial dict into the existing properties JSON (does not overwrite unmentioned keys)
  - [ ] `add_node(node_id, node_type, label, properties)` creates a node; raises if node already exists (distinct from upsert)
  - [ ] `add_edge(source_id, target_id, relationship_type, weight, properties)` creates an edge; raises if edge already exists
  - [ ] All mutations set `updated_at` timestamp on affected rows
  - [ ] `get_technique_index()`, `get_problem_index()` return all labels for the respective node types
  - [ ] `get_nodes_created_since(since_date, node_type)` and `get_edges_created_since(since_date, relationship_type)` query by `created_at`
  - [ ] Unit tests for each new method including edge cases (delete nonexistent, update nonexistent)

### TASK-003: Graph Visualization Component
- **Status**: To Do
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-002
- **Context**: TDD Section 2.5.2. New "Graph" tab in dashboard using `streamlit-agraph` (fallback: pyvis with iframe). Renders neighborhood of a selected node. Node click events trigger re-render. Nodes colored by type: Problem=red, Technique=blue, Concept=green, Category=gray, Paper=yellow. Edge labels show relationship type.
- **Description**: Implement the interactive graph visualization in the Streamlit dashboard. This is the foundation for the manual editing UI.
- **Acceptance Criteria**:
  - [ ] `streamlit-agraph` added to requirements.txt with pinned version
  - [ ] New "Graph" tab in dashboard renders an interactive node-edge graph
  - [ ] `get_node_neighborhood(node_id, depth)` returns `{"nodes": [...], "edges": [...]}` with type-based colors
  - [ ] Click a node: re-render graph centered on clicked node (neighborhood depth=1)
  - [ ] Node type filter: checkboxes to show/hide Problem, Technique, Concept, Category, Paper nodes
  - [ ] Nodes display labels and are colored by type; edge labels show relationship type
  - [ ] Zoom and pan controls work
  - [ ] Graph remains responsive with 50+ visible nodes
- **Notes**: If `streamlit-agraph` click events are unreliable, switch to pyvis with iframe embedding. The data contract (nodes + edges JSON) is the same for both.

### TASK-004: Manual Graph Editing UI
- **Status**: To Do
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-003
- **Context**: BL-012 promoted to MVP scope. The graph visualization is not just a viewer — it is an editor. All edits set `edited_by: "user"` in the node/edge properties. Edits are immediate (no save button). User edits will be preserved during LLM re-classification in later milestones.
- **Description**: Add editing capabilities to the graph visualization: add/remove nodes and edges, edit node properties, change relationship types.
- **Acceptance Criteria**:
  - [ ] **Add node**: Form in sidebar to create a new node (select type, enter label, fill properties). Node appears in graph immediately
  - [ ] **Edit node properties**: Click a node to open a properties panel. Edit any field (label, description, approach, innovation_type, etc.). Changes save immediately via `update_node_properties()`
  - [ ] **Delete node**: Button in properties panel to delete the selected node. Confirmation dialog. Removes node and all connected edges
  - [ ] **Add edge**: Select two nodes (click source, then target), choose relationship type from dropdown, confirm. Edge appears immediately
  - [ ] **Delete edge**: Click an edge (or select from edge list on a node), delete button. Edge removed immediately
  - [ ] **Change edge type**: Delete + re-add (or direct update if GraphStore supports it). UI shows this as a single "change type" dropdown
  - [ ] All user edits set `edited_by: "user"` in node/edge properties
  - [ ] Editing actions are logged (Python `logging` module) for auditability

### TASK-005: Hand-Craft Tree-Based Models Graph
- **Status**: To Do
- **Agent**: data-pipeline (impl)
- **Complexity**: Small
- **Depends on**: TASK-004
- **Context**: This is the manual prototype — ~15 nodes that the user knows intimately. The user will validate whether the schema, relationships, and UI work by interacting with concepts they can judge without any LLM assistance. All nodes are hand-crafted (either via UI or a seed script) and marked `edited_by: "user"`.
- **Description**: Create ~15 hand-crafted nodes in the tree-based models family, connected with all 7 relationship types. Provide a seed script that can be re-run, plus document how to add more via the UI.
- **Acceptance Criteria**:
  - [ ] **Problem node**: "How to build accurate predictive models from tabular data"
  - [ ] **Technique nodes** (6): Decision Tree, Random Forest, Gradient Boosting, XGBoost, LightGBM, CatBoost
  - [ ] **Concept nodes** (8): Information Gain, Gini Impurity, Bagging, Boosting, Ensemble Methods, Feature Importance, Overfitting, Pruning
  - [ ] **All 7 relationship types** represented:
    - PREREQUISITE_OF: Information Gain -> Decision Tree (concept -> concept); Gini Impurity -> Decision Tree
    - ADDRESSES: Decision Tree -> Problem; Random Forest -> Problem; etc.
    - BASELINE_OF: Decision Tree -> Random Forest; Decision Tree -> Gradient Boosting
    - ALTERNATIVE_TO: XGBoost <-> LightGBM; XGBoost <-> CatBoost; LightGBM <-> CatBoost
    - BUILDS_ON: Random Forest -> Bagging; Gradient Boosting -> Boosting; Random Forest -> Decision Tree (as concept)
    - BELONGS_TO: All techniques BELONGS_TO Category "Tree-Based Models"; concepts BELONGS_TO Category "Ensemble Methods"
    - INTRODUCES: Paper "Breiman 2001 - Random Forests" INTRODUCES Technique "Random Forest"; Paper "Chen & Guestrin 2016 - XGBoost" INTRODUCES Technique "XGBoost"
  - [ ] **Category node** (1): "Tree-Based Models" — validates BELONGS_TO edges
  - [ ] **Paper nodes** (2): Breiman 2001 (Random Forests), Chen & Guestrin 2016 (XGBoost) — validates INTRODUCES edges
  - [ ] Total: ~17 nodes (1 Problem + 6 Techniques + 8 Concepts + 1 Category + 2 Papers), all 7 edge types exercised
  - [ ] All nodes marked `edited_by: "user"`
  - [ ] Seed script at `src/seeds/tree_based_prototype.py` — idempotent, safe to re-run
  - [ ] User can add/edit/delete any node or edge via the UI after seeding
- **Notes**: The user will spend time interacting with this graph in the review checkpoint. The goal is to validate: (1) Does the schema capture the right information? (2) Are the relationship types sufficient? (3) Is the editing UX adequate? (4) Are any node types or edge types missing?

---

## Milestone 2: "The LLM extraction produces a useful graph"

> **Goal**: Run LLM extraction on ~10 real items in the tree-based domain and compare the output against the M1 hand-crafted ground truth. This validates extraction quality and determines whether `qwen2.5:7b` is sufficient or a larger model is needed.
> **Acceptance Criteria**:
> - LLM-extracted graph overlaid with the hand-crafted prototype — differences are visible
> - ~5 regular papers about tree-based methods classified with structured Problem/Technique decomposition
> - ~2 survey papers about ensemble methods / tree-based models classified
> - ~2 textbook chapters (e.g., Murphy or Hastie on decision trees / ensembles) seeded
> - ~1 landmark paper (e.g., original Random Forest or XGBoost paper) classified
> - LLM output compared against M1 ground truth: correct Problem, Technique, Concept nodes and relationships?
> - Model decision documented: qwen2.5:7b sufficient, or need to upgrade?
> **Observable Deliverable**: LLM-extracted graph overlaid with the manual prototype, differences visible in the graph editor
> **Review Checkpoint**: User reviews and approves before Milestone 3 begins
> **Depends on**: Milestone 1 review passed
> **Status**: To Do

### TASK-006: LLM Abstraction Layer
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Small
- **Depends on**: None (can start in parallel with M1 tasks)
- **Context**: TDD Section 2.2.1. Extract `LLMClient` ABC in `integrations/llm_client.py`. Refactor existing `OllamaClient` into `OllamaLLMClient` implementing the ABC. Add `APILLMClient` stub (raises NotImplementedError). All existing callers receive `LLMClient` via dependency injection.
- **Description**: Create the LLM abstraction layer so the system can swap between Ollama and an API fallback without changing caller code.
- **Acceptance Criteria**:
  - [ ] `LLMClient` ABC in `src/integrations/llm_client.py` with `chat(system_prompt, user_prompt, response_model) -> BaseModel | None`
  - [ ] `OllamaLLMClient` in `src/integrations/ollama_client.py` implements `LLMClient`, wrapping existing retry/schema-constrained logic
  - [ ] `APILLMClient` stub in `src/integrations/llm_client.py` raises `NotImplementedError`
  - [ ] `OllamaClassifier`, `Seeder`, and `ConceptExtractor` accept `LLMClient` via constructor injection
  - [ ] Config additions: `llm_provider`, `llm_api_model`, `llm_api_key_env`
  - [ ] All existing tests pass (250+) — this is a refactor, not a behavior change

### TASK-007: PaperAnalyzer — Concept-First Extraction
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-001, TASK-006
- **Context**: TDD Section 2.2.2. New `PaperAnalyzer` class in `services/classifier.py`. Uses `LLMClient` and the concept-first extraction prompt. Accepts concept, technique, and problem indexes to reduce duplicate node creation.
- **Description**: Implement the PaperAnalyzer that extracts Problem, Technique, Innovation Type, Results vs. Baselines, Practical Relevance, and Limitations from a paper abstract.
- **Acceptance Criteria**:
  - [ ] `PaperAnalyzer.analyze_paper(paper, concept_index, technique_index, problem_index)` returns `PaperAnalysis`
  - [ ] Prompt includes concept, technique, and problem indexes for dedup guidance
  - [ ] Prompt includes 3-5 few-shot examples
  - [ ] On LLM failure (all retries exhausted), returns `PaperAnalysis` with `classification_failed=True`
  - [ ] All LLM-created nodes/edges set `edited_by: "llm"` in properties
  - [ ] Unit tests with mocked LLMClient verify prompt construction and failure path

### TASK-008: Updated ConceptLinker for Concept-First Schema
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Small
- **Depends on**: TASK-001, TASK-002
- **Context**: TDD Section 2.3.2. Replace `link_paper_to_concepts()` with `link_paper_analysis()`. Creates Problem, Technique nodes and all edge types. Uses `normalize_concept_name()` for node IDs. Must preserve `edited_by: "user"` edges during re-classification — never overwrite user edits.
- **Description**: Update ConceptLinker to create the full concept-first graph structure from a PaperAnalysis, respecting user-edited nodes/edges.
- **Acceptance Criteria**:
  - [ ] `link_paper_analysis(analysis, paper_node_id, store)` creates all nodes and edges from a `PaperAnalysis`
  - [ ] Problem, Technique, ADDRESSES, INTRODUCES, BUILDS_ON, BASELINE_OF, ALTERNATIVE_TO edges created correctly
  - [ ] Existing edges with `edited_by: "user"` are never overwritten or deleted by the linker
  - [ ] Returns `AnalysisLinks` summary
  - [ ] Handles missing matches gracefully (logs, skips, continues)
  - [ ] Unit tests verify all edge types and user-edit preservation

### TASK-009: Tree-Based Domain LLM Validation Run
- **Status**: To Do
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-005, TASK-007, TASK-008
- **Context**: This is the quality gate for LLM extraction. Run ~10 real items through PaperAnalyzer + ConceptLinker, ALL in the tree-based domain where the user can immediately judge correctness against the M1 hand-crafted ground truth.
- **Description**: Process ~10 real items through the LLM pipeline and compare results against the hand-crafted prototype. Document quality findings and model decision.
- **Acceptance Criteria**:
  - [ ] ~5 regular papers about tree-based methods (mix of tiers) processed through PaperAnalyzer
  - [ ] ~2 survey papers about ensemble methods / tree-based models processed
  - [ ] ~2 textbook chapters (Murphy or Hastie chapters on decision trees / ensemble methods) seeded via ConceptExtractor
  - [ ] ~1 landmark paper (e.g., original Random Forest paper by Breiman, or XGBoost paper by Chen & Guestrin) processed
  - [ ] LLM-extracted nodes visible alongside M1 hand-crafted nodes in the graph editor (different `edited_by` values distinguish them)
  - [ ] Quality comparison documented: which Problem, Technique, Concept nodes did the LLM get right? Which relationships are wrong? Which are missing?
  - [ ] Model decision recorded: `qwen2.5:7b` sufficient, or need `qwen2.5:14b` / `phi4:14b` / API fallback?
  - [ ] Any needed prompt adjustments identified and documented

---

## Milestone 3: "The full knowledge bank is populated"

> **Goal**: Extend beyond the tree-based prototype to seed the full knowledge bank from 5 textbooks (~86 chapters). Semantic deduplication keeps it clean. The graph is browsable at scale.
> **Acceptance Criteria**:
> - Knowledge Bank tab shows 800+ concepts after seeding
> - Fewer than 10 concept pairs at >0.90 cosine similarity (post-dedup)
> - Graph visualization handles 800+ nodes (neighborhood-based rendering, not full graph)
> - User browses and spot-checks quality across multiple domains
> **Observable Deliverable**: Complete knowledge graph with 800+ concepts, clean and browsable
> **Review Checkpoint**: User reviews and approves before Milestone 4 begins
> **Depends on**: Milestone 2 review passed
> **Status**: To Do

### TASK-010: Complete Textbook Seeding — All 5 Books
- **Status**: To Do
- **Agent**: data-pipeline (impl)
- **Complexity**: Medium
- **Depends on**: TASK-006
- **Context**: BL-002. Infrastructure exists from PoC (PdfExtractor, chunked chapter processing). PDFs already downloaded. Murphy PML: 20 remaining chapters. Hastie ESL: 17 chapters. Bishop PRML: 14 chapters. Zhang D2L: 17 key chapters. Sutton RL: 12 remaining chapters. Estimated ~5 hours of Ollama processing total.
- **Description**: Run textbook seeding for all remaining chapters across 5 books.
- **Acceptance Criteria**:
  - [ ] Murphy PML: all 23 chapters seeded (20 remaining + verify 3 existing)
  - [ ] Hastie ESL: all 17 chapters seeded
  - [ ] Bishop PRML: all 14 chapters seeded
  - [ ] Sutton RL: remaining 12 chapters seeded (skip Psychology/Neuroscience)
  - [ ] Zhang D2L: 17 key chapters seeded (skip Builders Guide, Computational Performance, Appendices)
  - [ ] TOC page ranges verified for all books before running
  - [ ] Knowledge bank exceeds 800 concepts (pre-dedup)
  - [ ] No extraction failures (all chunks processed)

### TASK-011: EmbeddingService for Semantic Deduplication
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Small
- **Depends on**: None (can start in parallel)
- **Context**: TDD Section 2.2.6. `EmbeddingService` using `sentence-transformers` with `all-MiniLM-L6-v2`. Runs on CPU — does not compete with Ollama for GPU.
- **Description**: Implement the embedding service that generates vector representations of concept descriptions.
- **Acceptance Criteria**:
  - [ ] `EmbeddingService.embed(texts)` returns `list[list[float]]` using `all-MiniLM-L6-v2`
  - [ ] `EmbeddingService.cosine_similarity(a, b)` computes cosine similarity between two vectors
  - [ ] `sentence-transformers` added to `requirements.txt` with pinned version
  - [ ] Unit tests verify embedding output shape and cosine similarity computation

### TASK-012: Semantic Deduplication CLI
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-010, TASK-011
- **Context**: TDD Section 2.2.6, BL-003. CLI at `src/dedup.py`. Embeds all concept name+description pairs, clusters by cosine similarity, proposes merges. Merge preserves user-edited nodes (never auto-merge a node with `edited_by: "user"`).
- **Description**: Build the deduplication CLI that identifies and merges semantically equivalent concepts.
- **Acceptance Criteria**:
  - [ ] `python -m src.dedup --dry-run` reports proposed merges without modifying the database
  - [ ] `python -m src.dedup --apply` executes merges: keeps richer description, unions domain_tags, re-links all edges to surviving node, deletes merged node
  - [ ] Similarity threshold configurable via `PM_DEDUP_SIMILARITY_THRESHOLD` (default 0.90)
  - [ ] User-edited nodes (`edited_by: "user"`) are never auto-merged — flagged for manual review instead
  - [ ] Known test cases: "Bellman Equation" / "Bellman Equations" merged; "prior distribution" / "posterior distribution" NOT merged
  - [ ] Post-dedup: fewer than 10 concept pairs at >0.90 cosine similarity

---

## Milestone 4: "I can interact with papers and find things fast"

> **Goal**: The user can mark papers as read, add notes, flag papers for review, and search by concept/technique name with instant ranked results.
> **Acceptance Criteria**:
> - Mark 5 papers with different statuses (unseen -> skimmed -> read -> deep-dived)
> - Add personal notes to 3 papers
> - Search for "attention" and verify "Attention Mechanism" appears first
> - Search for "random forest" and verify the technique node appears
> **Observable Deliverable**: Mark papers, add notes, search and find concepts instantly
> **Review Checkpoint**: User reviews and approves before Milestone 5 begins
> **Depends on**: Milestone 3 review passed
> **Status**: To Do

### TASK-013: Database Migration and User Interaction Backend
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Small
- **Depends on**: TASK-002
- **Context**: TDD Section 2.4.5. Migration adds default user interaction fields to existing Paper nodes. Fields: `user_status` (unseen/skimmed/read/deep-dived), `user_notes`, `last_accessed_at`, `flagged_for_review`. Also `update_paper_interaction()`, `get_papers_by_status()`, `get_flagged_papers()`.
- **Description**: Write the migration script and user interaction query methods for GraphStore.
- **Acceptance Criteria**:
  - [ ] `src/migrations/001_mvp_schema.py` — idempotent script adding user interaction defaults to all existing Paper nodes
  - [ ] Script backs up database before modifying
  - [ ] `update_paper_interaction(paper_id, user_status, user_notes, flagged)` — partial updates work (setting status does not clear notes)
  - [ ] `last_accessed_at` auto-set on any interaction update
  - [ ] `get_papers_by_status(status)` and `get_flagged_papers()` return filtered results
  - [ ] Unit tests for all interaction methods

### TASK-014: User Interaction Dashboard UI
- **Status**: To Do
- **Agent**: data-pipeline (impl)
- **Complexity**: Small
- **Depends on**: TASK-013
- **Context**: TDD Section 2.5.2. On each paper card: status dropdown, notes text box, flag toggle. Changes save immediately. Papers filterable by status and flagged state.
- **Description**: Add user interaction controls to the dashboard paper cards.
- **Acceptance Criteria**:
  - [ ] Each paper card shows a status dropdown (unseen/skimmed/read/deep-dived)
  - [ ] Each paper card has a notes text area (expandable)
  - [ ] Each paper card has a flag/bookmark toggle
  - [ ] Changes save immediately to the database (no separate "save" button)
  - [ ] Papers filterable by status and flagged state
  - [ ] `last_accessed_at` updates when any interaction occurs

### TASK-015: SearchService — Ranked Field-Priority Search
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Small
- **Depends on**: TASK-002
- **Context**: TDD Section 2.2.7, BL-008. Priority ranking: exact name (100) > prefix (80) > substring on label (60) > approach/innovation_type (40) > description (20). Within each priority, sort by node type: Concept > Technique > Problem > Category > Paper.
- **Description**: Implement ranked search across all node types with field-priority scoring.
- **Acceptance Criteria**:
  - [ ] `SearchService.search(query, node_types, limit)` returns `list[SearchResult]` ranked by field priority
  - [ ] Searching "attention" returns "Attention Mechanism" as top result
  - [ ] Case-insensitive matching; search across all node types by default
  - [ ] Response time under 100ms for 1000 nodes
  - [ ] Unit tests for each priority level

### TASK-016: Dashboard Search Integration
- **Status**: To Do
- **Agent**: data-pipeline (impl)
- **Complexity**: Small
- **Depends on**: TASK-014, TASK-015
- **Context**: Replace flat text-match in Knowledge Bank tab with SearchService. Clicking a search result offers "View in Graph" to switch to the Graph tab centered on that node.
- **Description**: Integrate ranked search into the dashboard and connect it to graph navigation.
- **Acceptance Criteria**:
  - [ ] Knowledge Bank search bar uses SearchService
  - [ ] Results show: node type badge (color-coded), label, match field snippet, score
  - [ ] Clicking a result offers "View in Graph" — switches to Graph tab centered on that node
  - [ ] Empty query shows all concepts grouped alphabetically

---

## Milestone 5: "Concepts are organized and browsable"

> **Goal**: Knowledge bank shows concepts grouped into auto-generated categories. User can browse by category and adjust groupings.
> **Acceptance Criteria**:
> - Knowledge Bank shows a taxonomy tree with 10-20 categories
> - Each category contains 3+ concepts/techniques
> - Groupings make intuitive sense (e.g., "Optimization" contains SGD, Adam, learning rate scheduling)
> - User can reassign a concept to a different category via the dashboard
> **Observable Deliverable**: Concepts grouped into browsable categories
> **Review Checkpoint**: User reviews and approves before Milestone 6 begins
> **Depends on**: Milestone 4 review passed
> **Status**: To Do

### TASK-017: TaxonomyGenerator — LLM Clustering
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-006, TASK-002
- **Context**: TDD Section 2.2.5, BL-009. Loads all Concept and Technique nodes, batches if >200, prompts LLM to propose categories. Returns `list[CategoryProposal]`.
- **Description**: Implement the auto-taxonomy generator that clusters concepts into meaningful categories.
- **Acceptance Criteria**:
  - [ ] `generate_taxonomy()` loads all concept + technique nodes and prompts LLM
  - [ ] Returns `list[CategoryProposal]` with category name, description, member lists
  - [ ] For >200 concepts, batches by existing `domain_tags`
  - [ ] Configurable max categories (default 20) and min per category (default 3)
  - [ ] `apply_taxonomy(proposals)` creates Category nodes and BELONGS_TO edges
  - [ ] Unit tests with mocked LLMClient

### TASK-018: Taxonomy CLI and Dashboard Browsing
- **Status**: To Do
- **Agent**: data-pipeline (impl)
- **Complexity**: Small
- **Depends on**: TASK-017
- **Context**: CLI at `src/taxonomy.py`. `--generate` writes proposals to JSON for review. `--apply` reads edited JSON and creates nodes/edges. Dashboard shows taxonomy tree in Knowledge Bank tab.
- **Description**: Create the taxonomy CLI and add category browsing to the dashboard.
- **Acceptance Criteria**:
  - [ ] `python -m src.taxonomy --generate` writes proposals to `data/taxonomy_proposals.json`
  - [ ] `python -m src.taxonomy --apply` creates Category nodes + BELONGS_TO edges from (possibly edited) JSON
  - [ ] Re-running `--generate` is idempotent (no duplicate categories)
  - [ ] Dashboard Knowledge Bank tab shows category sidebar/tree for browsing
  - [ ] User can reassign a concept to a different category via the dashboard

---

## Milestone 6: "The digest tells me what shifted"

> **Goal**: The weekly digest has a "What changed in my graph" section showing new techniques, new problems, trending concepts, and landscape shifts.
> **Acceptance Criteria**:
> - Run the weekly pipeline
> - Digest shows "What Changed" section at the top with new techniques and problems
> - Trending concepts section shows topics with increasing connections over the past 4 weeks
> - "What Changed" section is meaningful — not just "30 new papers"
> **Observable Deliverable**: Meaningful digest with landscape shifts
> **Review Checkpoint**: User reviews and approves before Milestone 7 begins
> **Depends on**: Milestone 5 review passed
> **Status**: To Do

### TASK-019: ChangeDetector — Weekly Changes
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Small
- **Depends on**: TASK-002
- **Context**: TDD Section 2.2.4. Queries nodes/edges created in past 7 days, grouped by type. Returns `WeeklyChanges` with human-readable summary.
- **Description**: Implement weekly graph change detection.
- **Acceptance Criteria**:
  - [ ] `detect_weekly_changes(run_date)` returns `WeeklyChanges` with new techniques, problems, edge counts
  - [ ] Summary is human-readable: "This week: 3 new techniques, 1 new problem, 12 new relationships"
  - [ ] New techniques include their associated problem name and introducing paper title
  - [ ] Returns empty `WeeklyChanges` (not error) when no changes detected
  - [ ] Unit tests with pre-populated in-memory database

### TASK-020: ChangeDetector — Trend Detection
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Small
- **Depends on**: TASK-019
- **Context**: TDD Section 2.2.4. Rolling 4-week window. Trend score = `new_this_week + (new_4_weeks * 0.7)`. Configurable window, threshold, decay.
- **Description**: Implement trend detection for concepts and problems gaining traction.
- **Acceptance Criteria**:
  - [ ] `detect_trends(run_date, window_weeks)` returns `list[TrendingTopic]` sorted by trend_score
  - [ ] Trend score = `new_connections_this_week + (new_connections_4_weeks * 0.7)`
  - [ ] Only includes topics with `trend_min_connections` (default 3) or more new connections
  - [ ] Returns empty list when no trends detected
  - [ ] Unit tests with synthetic multi-week data

### TASK-021: Updated Pipeline and Digest with "What Changed"
- **Status**: To Do
- **Agent**: data-pipeline (impl), test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-007, TASK-008, TASK-020
- **Context**: TDD Sections 2.3.1, 2.5.1. Update `pipeline.py` to use PaperAnalyzer + updated ConceptLinker. New `changes_section.html.j2` template. Pipeline calls ChangeDetector before rendering. PoC-era papers display with legacy card layout.
- **Description**: Wire PaperAnalyzer into the pipeline and add the "What Changed" section to the digest and dashboard.
- **Acceptance Criteria**:
  - [ ] Pipeline uses `PaperAnalyzer.analyze_paper()` instead of `OllamaClassifier.classify_paper()`
  - [ ] Pipeline loads technique and problem indexes in addition to concept index
  - [ ] Dashboard paper cards show: Problem, Technique, Innovation Type badge, Practical Relevance, Results vs. Baselines, Tier badge
  - [ ] PoC-era papers display correctly with legacy fields (no broken cards)
  - [ ] "What Changed" section at top of weekly digest HTML with new techniques, problems, trends
  - [ ] Dashboard shows the same "What Changed" information on the main page
  - [ ] End-to-end integration test updated for new classification flow

---

## Milestone 7: "MVP hardening and phase review"

> **Goal**: Verify all MVP success criteria are met. Full test suite. Documentation. 4-week validation. Commercial signal evaluation. Phase review.
> **Acceptance Criteria**:
> - All 12 success criteria from PRD Section 3 evaluated
> - Pipeline has run for at least 4 consecutive weeks with new schema
> - PHASE-REVIEW.md produced with verdict
> **Observable Deliverable**: All success criteria evaluated, phase review document with recommendation
> **Review Checkpoint**: User decides whether to proceed to Beta
> **Depends on**: Milestone 6 review passed + 4 weeks of pipeline operation
> **Status**: To Do

### TASK-022: Full Test Suite Update
- **Status**: To Do
- **Agent**: test-validator (QA)
- **Complexity**: Medium
- **Depends on**: TASK-021
- **Context**: Update e2e integration test for new classification flow. Ensure all new components have unit tests. Target: 80%+ coverage on core logic, 350+ total tests.
- **Description**: Comprehensive test update to validate all MVP components work together.
- **Acceptance Criteria**:
  - [ ] End-to-end integration test updated for concept-first classification flow
  - [ ] All new services have unit tests with mocked dependencies
  - [ ] All tests pass (target: 350+ total tests)
  - [ ] Coverage report: 80%+ on `src/services/`, `src/store/`, `src/integrations/`
  - [ ] No regressions from PoC test suite

### TASK-023: README and Documentation Update
- **Status**: To Do
- **Agent**: content-writer (docs)
- **Complexity**: Small
- **Depends on**: TASK-022
- **Context**: Update README for MVP features. Document new CLIs (dedup, taxonomy). Verify "Built with Claude Code" line. Update setup instructions for new dependencies.
- **Description**: Update project documentation for the MVP.
- **Acceptance Criteria**:
  - [ ] README reflects MVP features and architecture
  - [ ] Setup instructions include new dependencies (sentence-transformers, streamlit-agraph)
  - [ ] CLI commands documented: `dedup`, `taxonomy`
  - [ ] "Built with Claude Code" line present
  - [ ] TASKS.md fully updated with completion dates

### TASK-024: 4-Week Pipeline Validation
- **Status**: To Do
- **Agent**: none — manual user process
- **Complexity**: Medium
- **Depends on**: TASK-021
- **Context**: Run the weekly pipeline for 4 consecutive weeks with the concept-first schema. Validate extraction quality, graph growth, digest usefulness. This runs in parallel with later milestones once the pipeline is updated.
- **Description**: Validate concept-first pipeline over 4 weeks of weekly operation.
- **Acceptance Criteria**:
  - [ ] Pipeline runs successfully for 4 consecutive Fridays
  - [ ] Extraction quality: Problem/Technique decomposition meaningful for 80%+ of classified papers
  - [ ] Knowledge bank grows weekly (new concepts from T5 surveys)
  - [ ] "What Changed" section is useful at least 2 out of 4 weeks
  - [ ] No silent failures or data corruption
  - [ ] Prompt tuning documented if needed

### TASK-025: Commercial Signal Evaluation
- **Status**: To Do
- **Agent**: architect (phase review)
- **Complexity**: Small
- **Depends on**: TASK-024
- **Context**: MVP-GOALS.md Commercial Signal Instrument. Evaluate: (a) knowledge bank > 800 concepts, (b) >70% of papers link to 2+ concepts, (c) "what changed" valuable 2/4 weeks.
- **Description**: Evaluate the commercial signal instrument after 4 weeks of MVP operation.
- **Acceptance Criteria**:
  - [ ] Knowledge bank size documented (target: >800)
  - [ ] Concept reuse rate calculated: % of classified papers linking to 2+ existing concepts
  - [ ] "What changed" usefulness rated by user (target: valuable 2/4 weeks)
  - [ ] Results documented in PHASE-REVIEW.md

### TASK-026: MVP Phase Review
- **Status**: To Do
- **Agent**: architect (phase review)
- **Complexity**: Small
- **Depends on**: TASK-022, TASK-023, TASK-024, TASK-025
- **Context**: Produce `docs/paper-monitoring/mvp/PHASE-REVIEW.md` using template. Evaluate all 12 success criteria. Document known debt. Recommend next phase.
- **Description**: Produce the MVP phase review document.
- **Acceptance Criteria**:
  - [ ] PHASE-REVIEW.md covers all 12 success criteria with PASS/FAIL verdicts
  - [ ] Known technical debt documented with severity
  - [ ] Unresolved backlog items assessed
  - [ ] Commercial signal results interpreted
  - [ ] Recommendation: proceed to Beta, extend MVP, or maintain as personal tool
  - [ ] User reviews and approves

---

## Dependency Graph

```
TASK-001 (Pydantic Models)
  |
  +-- TASK-002 (GraphStore Mutations) ----+
  |     |                                  |
  |     +-- TASK-003 (Graph Viz)          |
  |     |     |                            |
  |     |     +-- TASK-004 (Editing UI)   |
  |     |           |                      |
  |     |           +-- TASK-005 (Hand-craft Tree-Based) [END OF M1]
  |     |                 |
  |     |                 +-- TASK-009 (LLM Validation Run) [also TASK-007, TASK-008]
  |     |
  |     +-- TASK-008 (Updated ConceptLinker) [also TASK-001]
  |     +-- TASK-013 (Migration + User Interaction Backend)
  |     +-- TASK-015 (SearchService)
  |     +-- TASK-019 (ChangeDetector Weekly)
  |
  +-- TASK-007 (PaperAnalyzer) [also TASK-006]
  +-- TASK-017 (TaxonomyGenerator) [also TASK-006]

TASK-006 (LLM Abstraction) — independent, can start in parallel with M1
  |
  +-- TASK-007 (PaperAnalyzer) [also TASK-001]
  +-- TASK-010 (Textbook Seeding)
  +-- TASK-017 (TaxonomyGenerator) [also TASK-002]

TASK-011 (EmbeddingService) — independent, can start anytime
  |
  +-- TASK-012 (Dedup CLI) [also TASK-010]

TASK-009 (LLM Validation Run) → END OF M2

TASK-010 + TASK-012 → END OF M3

TASK-013 → TASK-014 (User Interaction UI)
TASK-015 → TASK-016 (Dashboard Search) [also TASK-014]
→ END OF M4

TASK-017 → TASK-018 (Taxonomy CLI + Dashboard)
→ END OF M5

TASK-019 → TASK-020 (Trend Detection)
TASK-007 + TASK-008 + TASK-020 → TASK-021 (Pipeline + Digest Update)
→ END OF M6

TASK-021 → TASK-022 (Test Suite) → TASK-023 (README)
TASK-021 → TASK-024 (4-Week Validation) → TASK-025 (Commercial Signal)
TASK-022 + TASK-023 + TASK-025 → TASK-026 (Phase Review)
→ END OF M7
```

### Parallelism Opportunities

The following can run in parallel to accelerate delivery:
- **TASK-006** (LLM Abstraction) can start alongside M1 tasks since it is a refactor of existing code
- **TASK-011** (EmbeddingService) has no dependencies and can start anytime
- **TASK-019** (ChangeDetector) depends only on TASK-002 and can start once M1 is done
- **TASK-024** (4-Week Validation) begins as soon as TASK-021 is done and runs in parallel with M7 test/doc work

---

## Completed Milestones Log
<!-- Move completed milestones here with completion date and review outcome -->
