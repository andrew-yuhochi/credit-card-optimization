# Technical Design Document — Paper Monitoring (MVP)

> **Status**: In Review
> **Author**: Architect Agent
> **Last Updated**: 2026-04-17
> **Phase**: MVP
> **Depends on**: PRD.md (MVP), PoC TDD.md (reference), PoC PHASE-REVIEW.md (learnings)

## 1. Architecture Overview

The MVP retains the PoC's batch-oriented, fully-local architecture but restructures the data model around the **concept-first principle**: Problems, Techniques, and Concepts are primary citizens; Papers are evidence nodes.

### What Changes from PoC

| Layer | PoC | MVP |
|-------|-----|-----|
| **Graph schema** | 2 node types (Concept, Paper), 3 edge types | 5 node types (Problem, Technique, Concept, Category, Paper), 7 edge types |
| **Extraction** | Flat summary + key_contributions | Structured Problem/Technique decomposition with innovation type, baselines, limitations |
| **LLM interface** | Direct OllamaClient calls | LLM abstraction layer (Ollama primary, cheap API fallback) |
| **Knowledge bank** | 492 concepts, flat browsing | 800+ concepts, hierarchical taxonomy, semantic dedup |
| **Search** | Flat text match across all fields | Ranked field-priority search |
| **User engagement** | None | Read status, notes, flags, last_accessed_at |
| **Digest** | Paper list grouped by tier | Paper list + "What changed in my graph" section |
| **Navigation** | Card layout + list | Interactive graph visualization |

### What Does Not Change

- Entry points: `pipeline.py`, `seed.py`, `run_weekly.sh`, cron schedule
- Data sources: arXiv API, HuggingFace Daily Papers API, textbook PDFs
- Infrastructure: SQLite, Ollama, Streamlit, local-only execution
- Ingestion layer: ArxivFetcher, HuggingFaceFetcher, PdfExtractor, PreFilter
- Scheduling: cron + caffeinate (Friday 6 PM)

### Component Map (MVP)

```
+-----------------------------+     +-----------------------------+
|  Seeding CLI                |     |  Weekly Pipeline            |
+-----------------------------+     +-----------------------------+
| seed.py                     |     | pipeline.py                 |
|  |- ArxivFetcher            |     |  |- ArxivFetcher            |
|  |- PdfExtractor            |     |  |- HuggingFaceFetcher      |
|  |- LLMClient (abstraction) |     |  |- PreFilter               |
|  |- ConceptExtractor (new)  |     |  |- LLMClient (abstraction) |
|  |- ConceptLinker            |     |  |- PaperAnalyzer (new)     |
|  |- GraphStore               |     |  |- ConceptLinker            |
+-----------------------------+     |  |- GraphStore               |
                                    |  |- DigestRenderer (updated) |
+-----------------------------+     |  |- ChangeDetector (new)     |
|  Dedup CLI (new)            |     +-----------------------------+
+-----------------------------+
| dedup.py                    |     +-----------------------------+
|  |- EmbeddingService (new)  |     |  Streamlit Dashboard        |
|  |- GraphStore               |     +-----------------------------+
+-----------------------------+     | app.py                      |
                                    |  |- GraphStore               |
+-----------------------------+     |  |- SearchService (new)      |
|  Taxonomy CLI (new)         |     |  |- GraphVisualization (new) |
+-----------------------------+     |  |- UserInteraction (new)    |
| taxonomy.py                 |     +-----------------------------+
|  |- LLMClient               |
|  |- GraphStore               |
+-----------------------------+

+-------------------------------------------------------------+
|  Shared Infrastructure                                       |
+-------------------------------------------------------------+
| SQLite (graph schema v2)  | Pydantic models v2              |
| LLMClient (abstraction)   | Config (config.py)               |
| EmbeddingService           | Logging                          |
+-------------------------------------------------------------+
```

---

## 2. Component Design

### 2.1 Data Ingestion Layer

**Unchanged from PoC**: ArxivFetcher, HuggingFaceFetcher, PdfExtractor, PreFilter. These components are stable and tested (250 tests passing). No modifications required.

### 2.2 Processing & Transformation Layer

#### 2.2.1 LLMClient — Abstraction Layer (New)

**Responsibility**: Abstract the LLM inference interface so the system can use Ollama (primary) or a cheap API model (fallback) without changing caller code.

**Why now**: The PoC's richer extraction schema (Problem/Technique decomposition) is significantly more demanding than flat summary extraction. If `qwen2.5:7b` cannot produce reliable structured output, the system needs to fall back to a larger local model or a cheap cloud API without touching every caller.

**Interface**:
```python
from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel | None:
        """Send a prompt and return a validated Pydantic model, or None on failure."""
        ...

class OllamaLLMClient(LLMClient):
    """Wraps the existing OllamaClient. Primary implementation."""
    ...

class APILLMClient(LLMClient):
    """Optional fallback for cheap cloud APIs (Claude Haiku, GPT-4o-mini).
    Not implemented in Milestone 1. Stubbed for future use."""
    ...
```

**Migration from PoC**: The existing `OllamaClient` in `integrations/ollama_client.py` becomes `OllamaLLMClient`. The `OllamaClassifier` is refactored to accept an `LLMClient` dependency instead of directly importing `OllamaClient`. All retry logic, schema-constrained format, and error handling remain in `OllamaLLMClient`.

**Configuration**:
```python
# config.py additions
llm_provider: str = "ollama"  # "ollama" or "api" (future)
llm_api_model: str | None = None  # e.g., "claude-haiku-4-20250514"
llm_api_key_env: str | None = None  # env var name containing the API key
```

**Trade-off**: Adding an abstraction layer for a single implementation adds indirection. Justified because (a) the PoC PHASE-REVIEW explicitly flagged this as Medium-severity tech debt, and (b) testing `qwen2.5:7b` against the richer schema is the first MVP milestone — if it fails, the fallback path needs to exist.

#### 2.2.2 PaperAnalyzer (Replaces classify_paper)

**Responsibility**: Extract the concept-first decomposition from a paper abstract. Replaces the PoC's `OllamaClassifier.classify_paper()` with a richer extraction that produces Problem, Technique, and Paper evidence nodes.

**Interface**:
```python
class PaperAnalyzer:
    def __init__(self, llm_client: LLMClient, store: GraphStore):
        ...

    def analyze_paper(
        self,
        paper: ArxivPaper,
        concept_index: list[str],
        technique_index: list[str],
        problem_index: list[str],
    ) -> PaperAnalysis:
        """Analyze a paper and return structured decomposition."""
        ...
```

**Prompt template** (concept-first extraction):

```
System prompt:
  You are an expert ML researcher analyzing research papers. For each paper,
  extract a structured decomposition following this schema:

  1. PROBLEM: What specific problem does this paper address?
     - Give a concise name and one-sentence description
     - Check if this matches an existing problem: {problem_index}

  2. TECHNIQUE: What approach/method does the paper propose?
     - name: How practitioners refer to it (e.g., "SkillClaw", "Flash Attention")
     - approach: Core design in 2-3 sentences
     - innovation_type: one of [architecture, problem_framing, loss_trick,
       eval_methodology, dataset, training_technique]
     - practical_relevance: When would a practitioner use this? 1-2 sentences
     - limitations: What doesn't it handle? 1-2 sentences
     - Check if this matches an existing technique: {technique_index}

  3. TIER CLASSIFICATION: Use this 5-tier taxonomy:
     [same tier definitions as PoC with few-shot examples]

  4. BASELINES AND ALTERNATIVES:
     - results_vs_baselines: What specific baselines were compared? What were
       the key metrics and improvements?
     - existing_alternatives: What other techniques address the same problem?
       Check: {technique_index}

  5. FOUNDATIONAL CONCEPTS: What concepts from the knowledge bank does this
     technique build on? Check: {concept_index}

  Return a JSON object with exactly these fields:
  {
    "problem_name": "<concise problem name>",
    "problem_description": "<one-sentence description>",
    "is_existing_problem": <true if matches problem_index>,
    "technique_name": "<practitioner name>",
    "technique_approach": "<2-3 sentence core design>",
    "innovation_type": "<architecture|problem_framing|loss_trick|eval_methodology|dataset|training_technique>",
    "practical_relevance": "<1-2 sentences>",
    "limitations": "<1-2 sentences>",
    "is_existing_technique": <true if matches technique_index>,
    "tier": <integer 1-5>,
    "confidence": "<high|medium|low>",
    "reasoning": "<1-2 sentences explaining tier>",
    "results_vs_baselines": "<specific metrics and comparisons>",
    "alternative_technique_names": ["<existing technique names from index>"],
    "baseline_technique_names": ["<existing technique names from index>"],
    "foundational_concept_names": ["<concept names from knowledge bank>"]
  }

User prompt:
  Title: {title}
  Abstract: {abstract}
  Categories: {categories}
  Published: {published_date}
```

**Output model**: `PaperAnalysis` (see Section 10, Pydantic models).

**Key design decision**: The prompt asks the LLM to check against existing indexes (problem, technique, concept) so it can identify when a paper addresses a known problem or extends a known technique — rather than creating duplicates. The indexes are injected into the system prompt the same way the PoC injected the concept index.

#### 2.2.3 ConceptExtractor (Refactored from extract_concepts)

**Responsibility**: Extract foundational concepts from text (paper abstract, textbook chapter). Refactored from `OllamaClassifier.extract_concepts()` to accept `LLMClient` and to produce the MVP node types.

**Interface**:
```python
class ConceptExtractor:
    def __init__(self, llm_client: LLMClient):
        ...

    def extract_concepts(
        self,
        text: str,
        source_id: str,
        source_type: str = "manual_seed",
    ) -> list[ExtractedConcept]:
        """Extract foundational concepts from text. Same behavior as PoC
        but accepts LLMClient instead of direct OllamaClient."""
        ...
```

**Change from PoC**: Minimal. The extraction prompt and source-type guidance are unchanged. The only structural change is dependency injection of `LLMClient` instead of direct `OllamaClient` import.

#### 2.2.4 ChangeDetector (New)

**Responsibility**: Compute "what changed in my graph" by querying edge timestamps and node creation dates.

**Interface**:
```python
class ChangeDetector:
    def __init__(self, store: GraphStore):
        ...

    def detect_weekly_changes(self, run_date: str) -> WeeklyChanges:
        """Detect new nodes and edges created in the past 7 days."""
        ...

    def detect_trends(self, run_date: str, window_weeks: int = 4) -> list[TrendingTopic]:
        """Detect concepts/problems gaining the most connections over a rolling window."""
        ...
```

**Implementation**:
- **Layer 1 (weekly changes)**: Query `nodes WHERE created_at >= (run_date - 7 days)` grouped by `node_type`. Query `edges WHERE created_at >= (run_date - 7 days)` grouped by `relationship_type` and target node. Produces counts and specific examples.
- **Layer 2 (trends)**: Query edge creation timestamps over a 4-week rolling window, grouped by target Problem/Technique/Concept nodes. Rank by `(new_edges_this_week) + (new_edges_past_4_weeks * 0.7)` decay factor. Configurable threshold for what counts as "trending" (default: 3+ new connections in 4 weeks).

#### 2.2.5 TaxonomyGenerator (New)

**Responsibility**: Auto-generate hierarchical concept groupings using LLM clustering.

**Interface**:
```python
class TaxonomyGenerator:
    def __init__(self, llm_client: LLMClient, store: GraphStore):
        ...

    def generate_taxonomy(self) -> list[CategoryProposal]:
        """Cluster existing concepts into categories. Returns proposals for user review."""
        ...

    def apply_taxonomy(self, approved_categories: list[CategoryProposal]) -> None:
        """Create Category nodes and BELONGS_TO edges for approved groupings."""
        ...
```

**Approach**:
1. Load all Concept and Technique nodes with their descriptions and domain tags
2. If the set is large (>200), group by existing `domain_tags` first to create manageable batches
3. Prompt the LLM: "Given these concepts: [{name: description}, ...], propose 10-20 categories that group them meaningfully. For each category, provide a name, description, and list of concept names that belong to it."
4. Return proposals as `list[CategoryProposal]` for user review
5. On approval, create Category nodes and BELONGS_TO edges

**CLI entry point**: `python -m src.taxonomy --generate` (propose), `python -m src.taxonomy --apply` (after user reviews the proposals)

#### 2.2.6 EmbeddingService (New)

**Responsibility**: Generate embeddings for concept descriptions. Used by the deduplication CLI.

**Interface**:
```python
class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        ...

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two embedding vectors."""
        ...
```

**Library**: `sentence-transformers` with `all-MiniLM-L6-v2` (~90 MB, runs on CPU). This model is sufficient for concept description similarity and does not compete with Ollama for GPU memory.

**Trade-off**: Adding `sentence-transformers` as a dependency (~200 MB installed) for a single feature (dedup). Justified because (a) embedding-based similarity is fundamentally more capable than name-based fuzzy matching for the dedup use case, and (b) the same embeddings could later power search ranking improvements.

#### 2.2.7 SearchService (New)

**Responsibility**: Ranked field-priority search across all node types.

**Interface**:
```python
class SearchService:
    def __init__(self, store: GraphStore):
        ...

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        """Search across all node types with field-priority ranking."""
        ...
```

**Ranking algorithm**:
1. **Priority 1 (score=100)**: Exact name match (case-insensitive) on any node's `label` field
2. **Priority 2 (score=80)**: Prefix match on `label` (query is a prefix of the node name)
3. **Priority 3 (score=60)**: Substring match on `label`
4. **Priority 4 (score=40)**: Exact match on technique `approach` or `innovation_type` (from node properties)
5. **Priority 5 (score=20)**: Substring match on `description` or other properties fields
6. Within each priority level, sort by node type: Concept > Technique > Problem > Category > Paper

**Implementation**: SQLite query with `CASE WHEN` scoring in SQL, or Python post-processing of `LIKE` queries. For 800-1000 nodes, Python post-processing is fast enough (<50ms). No full-text search index needed at MVP scale.

### 2.3 Analytical / Business Logic Layer

#### 2.3.1 Classification Flow (Updated)

The PoC classification flow was:
```
Paper -> OllamaClassifier.classify_paper() -> PaperClassification -> ConceptLinker -> BUILDS_ON edges
```

The MVP classification flow is:
```
Paper -> PaperAnalyzer.analyze_paper() -> PaperAnalysis
  -> Create/link Problem node (ADDRESSES edge)
  -> Create/link Technique node (INTRODUCES edge from Paper, ADDRESSES edge to Problem)
  -> Create BUILDS_ON edges from Technique to matched Concepts
  -> Create BASELINE_OF / ALTERNATIVE_TO edges between Techniques
  -> Store Paper node with evidence-only fields
```

**Pipeline integration**: `_run_classification()` in `pipeline.py` is updated to:
1. Load concept index, technique index, and problem index from GraphStore
2. Call `PaperAnalyzer.analyze_paper()` for each candidate paper
3. Call `_store_analysis_results()` (new) to create all nodes and edges
4. Continue to T5 expansion (unchanged) and digest rendering (updated)

#### 2.3.2 ConceptLinker (Updated)

The PoC ConceptLinker matched concept names only. The MVP version also matches technique names and problem names against their respective indexes.

**Updated interface**:
```python
class ConceptLinker:
    def link_paper_analysis(
        self,
        analysis: PaperAnalysis,
        paper_node_id: str,
        store: GraphStore,
    ) -> AnalysisLinks:
        """Create all nodes and edges from a paper analysis.
        Returns summary of created links."""
        ...
```

This single method replaces the separate `link_paper_to_concepts` and handles:
- Problem node: upsert if `is_existing_problem=True` matches, else create new
- Technique node: upsert if `is_existing_technique=True` matches, else create new
- Paper -> Technique: INTRODUCES edge
- Technique -> Problem: ADDRESSES edge
- Technique -> Concept: BUILDS_ON edges (fuzzy-matched as before)
- Technique -> Technique: BASELINE_OF and ALTERNATIVE_TO edges (matched against technique index)

### 2.4 Storage Layer

#### 2.4.1 Database Schema v2

The MVP schema extends the PoC schema with new node types and edge types. The core `nodes` and `edges` tables are unchanged structurally — the extension is in the data, not the DDL.

```sql
-- ============================================================
-- CORE GRAPH TABLES (unchanged DDL from PoC)
-- ============================================================

CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,    -- "problem", "technique", "concept", "category", "paper"
    label TEXT NOT NULL,
    properties TEXT,            -- JSON blob (schema varies by node_type)
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_nodes_type ON nodes(node_type);
CREATE INDEX idx_nodes_label ON nodes(label);

CREATE TABLE edges (
    source_id TEXT NOT NULL REFERENCES nodes(id),
    target_id TEXT NOT NULL REFERENCES nodes(id),
    relationship_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    properties TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (source_id, target_id, relationship_type)
);

CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_edges_type ON edges(relationship_type);

-- ============================================================
-- SUPPORTING TABLES (unchanged from PoC)
-- ============================================================

CREATE TABLE weekly_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    papers_fetched INTEGER DEFAULT 0,
    papers_classified INTEGER DEFAULT 0,
    papers_failed INTEGER DEFAULT 0,
    digest_path TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    error_message TEXT
);

CREATE INDEX idx_runs_date ON weekly_runs(run_date);
```

**Key insight**: The DDL does not change. The graph schema's flexibility means new node types and edge types are just new values in the `node_type` and `relationship_type` columns. No ALTER TABLE or new tables needed.

#### 2.4.2 Node ID Conventions (Updated)

| Node Type | ID Format | Example |
|-----------|-----------|---------|
| Problem | `problem:{normalized_name}` | `problem:how_to_make_llm_agent_skills_improve_over_time` |
| Technique | `technique:{normalized_name}` | `technique:skillclaw`, `technique:flash_attention` |
| Concept | `concept:{normalized_name}` | `concept:attention_mechanism`, `concept:backpropagation` |
| Category | `category:{normalized_name}` | `category:ml_algorithms`, `category:optimization` |
| Paper | `paper:{arxiv_id}` | `paper:2604.08377`, `paper:1706.03762` |

Normalization uses the existing `normalize_concept_name()` utility from `src/utils/normalize.py` (6-step pipeline: strip, lowercase, whitespace-to-underscore, non-word-to-underscore, collapse underscores, strip underscores).

#### 2.4.3 Node Properties (Updated JSON Blobs)

**Problem node `properties`**:
```json
{
  "description": "One-sentence description of the problem",
  "first_seen_date": "2026-04-17",
  "paper_count": 3
}
```

**Technique node `properties`**:
```json
{
  "approach": "2-3 sentence description of the core design",
  "innovation_type": "architecture",
  "practical_relevance": "When would a practitioner use this? 1-2 sentences",
  "limitations": "What doesn't it handle? 1-2 sentences",
  "first_seen_date": "2026-04-17"
}
```

**Concept node `properties`** (unchanged from PoC):
```json
{
  "description": "~200 word description of the concept",
  "domain_tags": ["deep learning", "nlp"],
  "source_ids": ["paper:1706.03762"],
  "seeded_from": "landmark_paper"
}
```

**Category node `properties`**:
```json
{
  "description": "One-sentence description of this category",
  "generated_at": "2026-04-17",
  "user_adjusted": false
}
```

**Paper node `properties`** (updated — evidence-only + user interaction):
```json
{
  "title": "SkillClaw: Let Skills Evolve...",
  "authors": ["Author 1", "Author 2"],
  "abstract": "...",
  "arxiv_id": "2604.08377",
  "arxiv_url": "https://arxiv.org/abs/2604.08377",
  "pdf_url": "https://arxiv.org/pdf/2604.08377",
  "primary_category": "cs.LG",
  "all_categories": ["cs.LG", "cs.AI"],
  "published_date": "2026-04-11",
  "hf_upvotes": 42,
  "prefilter_score": 89,
  "tier": 2,
  "confidence": "high",
  "reasoning": "Introduces a novel architecture...",
  "results_vs_baselines": "+88% on WildClawBench over Voyager",
  "run_date": "2026-04-17",
  "classification_failed": false,
  "user_status": "unseen",
  "user_notes": "",
  "last_accessed_at": null,
  "flagged_for_review": false
}
```

Note: `summary` and `key_contributions` from PoC are replaced by the Problem/Technique decomposition. The paper itself carries only `results_vs_baselines` as evidence. The technique carries the approach, innovation type, practical relevance, and limitations.

#### 2.4.4 Edge Relationship Types (Updated)

| Relationship | Source -> Target | Meaning | New in MVP? |
|-------------|-----------------|---------|-------------|
| `PREREQUISITE_OF` | Concept -> Concept | Understanding A is required before B | No (PoC) |
| `BUILDS_ON` | Technique -> Concept | This technique uses/extends this concept | Updated (was Paper->Concept) |
| `INTRODUCES` | Paper -> Technique | This paper proposed this technique | Updated (was Paper->Concept) |
| `ADDRESSES` | Technique -> Problem | This technique tackles this problem | Yes |
| `BASELINE_OF` | Technique -> Technique | Established method this technique compares against | Yes |
| `ALTERNATIVE_TO` | Technique <-> Technique | Both address the same problem differently | Yes |
| `BELONGS_TO` | Concept/Technique -> Category | Domain membership | Yes |

**Edge direction for ALTERNATIVE_TO**: Bidirectional — when technique A is an alternative to technique B, create two edges: `A->B` and `B->A`. This ensures both nodes appear in the other's neighborhood during graph traversal.

#### 2.4.5 Migration Strategy

**Approach**: Incremental migration scripts, not rebuild-from-scratch.

**Rationale**: The PoC database contains 492 concepts with prerequisite edges, weekly pipeline history, and classified papers. Rebuilding from scratch would lose weekly run history and require re-seeding (which works but takes ~5 hours of Ollama time). Migration scripts preserve existing data.

**Migration steps**:

1. **Back up database**: Copy `paper_monitoring.db` to `paper_monitoring.db.bak`
2. **No DDL changes needed**: The nodes+edges schema already supports new node types and edge types — they're just new values in the `node_type` and `relationship_type` columns
3. **Re-type existing edges**: Existing `BUILDS_ON` edges (paper -> concept) are semantically correct but should now go from technique -> concept. For PoC papers that don't have technique nodes yet, keep the edges as-is (paper -> concept) as a legacy representation
4. **Add user interaction fields**: Update Paper node `properties` JSON to add default values for `user_status: "unseen"`, `user_notes: ""`, `last_accessed_at: null`, `flagged_for_review: false`
5. **Verify**: Run existing tests to confirm no regressions

**Migration script**: `src/migrations/001_mvp_schema.py` — idempotent, safe to re-run.

#### 2.4.6 GraphStore Updates

New methods added to `GraphStore`:

```python
class GraphStore:
    # --- Existing methods (unchanged) ---
    def upsert_node(self, node_id, node_type, label, properties): ...
    def get_node(self, node_id): ...
    def get_nodes_by_type(self, node_type): ...
    def get_concept_index(self) -> list[str]: ...
    def upsert_edge(self, source_id, target_id, relationship_type, weight, properties): ...
    def get_edges_from(self, node_id, relationship_type): ...
    def get_edges_to(self, node_id, relationship_type): ...
    def paper_exists(self, arxiv_id): ...
    def get_all_papers(self, limit): ...
    def get_all_concepts(self): ...

    # --- New methods for MVP ---
    def get_technique_index(self) -> list[str]:
        """Return all technique node labels."""
        ...

    def get_problem_index(self) -> list[str]:
        """Return all problem node labels."""
        ...

    def get_nodes_created_since(self, since_date: str, node_type: str | None = None) -> list[Node]:
        """Return nodes created after a given date, optionally filtered by type."""
        ...

    def get_edges_created_since(self, since_date: str, relationship_type: str | None = None) -> list[Edge]:
        """Return edges created after a given date, optionally filtered by type."""
        ...

    def update_paper_interaction(self, paper_id: str, user_status: str | None = None,
                                  user_notes: str | None = None, flagged: bool | None = None) -> None:
        """Update user interaction fields on a paper node's properties JSON."""
        ...

    def search_nodes(self, query: str, node_types: list[str] | None = None, limit: int = 20) -> list[dict]:
        """Search nodes by label and properties with field-priority scoring."""
        ...

    def get_node_neighborhood(self, node_id: str, depth: int = 1) -> dict:
        """Return a node and all nodes/edges within N hops. Used by graph visualization."""
        ...

    # --- Mutation methods for manual graph editing (BL-012) ---

    def add_node(self, node_id: str, node_type: str, label: str,
                 properties: dict, edited_by: str = "user") -> None:
        """Create a new node with provenance tracking. Sets edited_by in properties."""
        ...

    def delete_node(self, node_id: str) -> None:
        """Delete a node and all edges connected to it (both incoming and outgoing).
        Raises ValueError if node does not exist."""
        ...

    def update_node_properties(self, node_id: str, properties: dict,
                                edited_by: str = "user") -> None:
        """Merge updated properties into an existing node's properties JSON.
        Sets edited_by field to track provenance. Does not overwrite fields
        not present in the update dict."""
        ...

    def add_edge(self, source_id: str, target_id: str, relationship_type: str,
                 weight: float = 1.0, properties: dict | None = None,
                 edited_by: str = "user") -> None:
        """Create a new edge with provenance tracking. Sets edited_by in
        edge properties. For ALTERNATIVE_TO, automatically creates the
        reverse edge as well."""
        ...

    def delete_edge(self, source_id: str, target_id: str, relationship_type: str) -> None:
        """Delete an edge. For ALTERNATIVE_TO, automatically deletes the
        reverse edge as well. Raises ValueError if edge does not exist."""
        ...
```

#### 2.4.7 Provenance Tracking

**Purpose**: Track whether each node and edge was created/modified by the LLM pipeline or by the user manually. This enables the pipeline to preserve user authority during re-classification and provides visual transparency in the dashboard.

**Implementation**: The `edited_by` field is stored inside the `properties` JSON blob on both nodes and edges. Values are `"llm"` (default, set by the pipeline) or `"user"` (set by manual editing through the dashboard).

**Node provenance**:
```json
{
  "description": "...",
  "edited_by": "user",
  "edited_at": "2026-04-17T14:30:00"
}
```

**Edge provenance**:
```json
{
  "edited_by": "llm",
  "edited_at": "2026-04-17T18:15:00"
}
```

**Pipeline behavior during re-classification**:

When a paper is re-run through the pipeline (e.g., after a prompt improvement or model upgrade), the pipeline must respect user edits:

1. **Nodes with `edited_by: "user"`**: The pipeline does NOT overwrite any properties on these nodes. If the LLM produces a different description or innovation_type, the user's version is preserved. The pipeline logs a warning: `"Skipping update to user-edited node {node_id}"`.

2. **Edges with `edited_by: "user"`**: The pipeline does NOT delete or modify these edges. If the LLM no longer produces a relationship that the user manually added, the edge persists. If the LLM produces a conflicting edge (e.g., different relationship_type between the same two nodes), the user's edge takes precedence.

3. **New LLM-generated edges**: If the LLM produces a new edge that doesn't conflict with any user edge, it is created normally with `edited_by: "llm"`.

4. **Deleted nodes/edges**: If the user deleted a node or edge, the pipeline does not recreate it. This is tracked by storing deleted IDs in a `deleted_by_user` set (persisted in a lightweight `user_overrides` table or a JSON file).

**Trade-off**: Storing provenance in the JSON blob rather than as a top-level column avoids DDL changes to the nodes/edges tables. The trade-off is that querying "all user-edited nodes" requires JSON extraction (`json_extract(properties, '$.edited_by')`), which is slower than a column filter. At MVP scale (<2000 nodes), this is acceptable.

### 2.5 Presentation Layer

#### 2.5.1 DigestRenderer (Updated)

**Changes from PoC**:
- Paper cards now show: Problem name, Technique name + approach, Results vs. Baselines, Practical Relevance, Innovation Type badge, Tier badge — instead of flat summary and key_contributions
- New "What Changed in My Graph" section at the top of the digest (before paper list)
- T1/T2 section shows the full concept-first decomposition prominently
- Linked concepts remain as hover badges but are now on the Technique, not the Paper

**Updated template structure**:
```
templates/
├── digest.html.j2              # Main digest (updated)
└── partials/
    ├── paper_card.html.j2      # Updated for concept-first fields
    ├── concept_badge.html.j2   # Unchanged
    └── changes_section.html.j2 # New — "What changed" section
```

#### 2.5.2 Dashboard Updates

**Paper Cards (updated)**:
- Show: Problem, Technique (name + approach), Innovation Type badge, Practical Relevance, Results vs. Baselines, Tier badge
- User interaction controls: status dropdown (unseen/skimmed/read/deep-dived), notes text box, flag toggle
- `last_accessed_at` auto-updates when the user opens/interacts with a card

**Knowledge Bank Tab (updated)**:
- Ranked search bar (SearchService)
- Browse by taxonomy (Category tree → Concepts/Techniques within each category)
- Concept cards show prerequisites (PREREQUISITE_OF edges) and related techniques (BUILDS_ON edges)

**Graph Visualization Tab (new)**:

The graph renders as a **2D force-directed graph** using the `st-link-analysis` Streamlit component (MIT), which wraps Cytoscape.js. This is the primary daily-use interface for exploring the knowledge graph. Installable via `pip install st-link-analysis` — no Node.js, no npm build step, no custom React component.

Visual requirements (all provided out of the box by `st-link-analysis`, configured via Python):
- **2D force-directed layout**: fCoSE algorithm (default). Nodes repel/attract; clusters form naturally by connectivity. Settles quickly for graphs up to ~2000 nodes
- **Directed arrows on edges**: `directed=True` renders arrowheads at the target end of every edge
- **Edge colors and captions by relationship type**: `EdgeStyle` per `relationship_type` (e.g., ADDRESSES=orange, BUILDS_ON=teal, INTRODUCES=purple, BASELINE_OF=gray, ALTERNATIVE_TO=pink, BELONGS_TO=black, PREREQUISITE_OF=blue). Each edge displays its type as a caption along the line
- **Always-visible node labels**: `NodeStyle(caption="label", ...)` — labels rendered on the node itself, not only on hover. Readable at default zoom for ~17 to ~800 nodes
- **Node colors by type**: `NodeStyle` per `node_type` — Problem=red, Technique=blue, Concept=green, Category=gray, Paper=yellow
- **Click callback**: `on_click` event returns the selected node's ID to Python. The component's return value is written to `st.session_state.selected_node_id`. This is the bidirectional bridge that drives the editing sidebar
- **Neighbor highlight on click**: Built-in — clicking a node highlights its immediate neighbors and dims the rest. No Python code required
- **Zoom, pan, fullscreen**: Built-in browser controls
- **Hop slider (1–5)**: Implemented in Python — ~20 lines. The slider updates `st.session_state.hop_depth`; the filter runs a BFS from `selected_node_id` in `GraphStore.get_node_neighborhood(selected_node_id, depth)`; the filtered nodes+edges are passed to `st_link_analysis()` on the next render. Full graph shown when no node is selected
- **Node type filter (checkboxes)**: Same Python-side pattern as the hop slider. Checkbox state in `st.session_state` drives a filter on the nodes list before rendering

All of the above is configured in Python and rendered in a Streamlit-native iframe. There is no custom React component to build or maintain.

**Graph Editing UI (BL-012)**:

The graph visualization tab doubles as the primary editing interface. All editing interactions happen in the Streamlit sidebar, driven by the node selected in the Cytoscape graph (via the component's click callback).

- **Add node**: Sidebar form with fields for node type (dropdown: Problem/Technique/Concept), label (text input), and type-specific properties (description, innovation_type, etc.). On submit, the node is persisted via `add_node()` and appears in the graph after Streamlit re-renders. `edited_by` is set to `"user"`.
- **Edit node properties**: Clicking a node in the graph triggers the component's click callback, which writes the node ID to `st.session_state.selected_node_id`. The sidebar then loads that node's properties into an editable form. Changes save on an explicit "Update" button via `update_node_properties()`. `edited_by` is set to `"user"` on save.
- **Delete node**: Available from the properties panel via a "Delete" button with confirmation dialog ("Delete node '{label}' and all its edges? This cannot be undone."). Cascades to remove all connected edges.
- **Add edge**: Source node selected by clicking a node in the graph; target node and relationship type selected from dropdowns in the sidebar (relationship type filtered to valid pairs for the source-target node type combination, e.g., PREREQUISITE_OF only for Concept->Concept). Submit creates the edge immediately with `edited_by: "user"`.
- **Delete edge**: Select from edge list in the node properties panel, then click "Delete". Confirmation dialog for safety. For ALTERNATIVE_TO edges, both directions are deleted.
- **Visual provenance indicator**: User-edited vs. LLM-edited nodes are visually distinct via `NodeStyle` — `edited_by: "user"` nodes use a solid/brighter fill or a thicker border; `edited_by: "llm"` nodes use a lower opacity or standard border. Configured as two `NodeStyle` entries distinguished by a synthetic `node_type_variant` field that folds `edited_by` into the styling key.

**Technology choice**: `st-link-analysis` (MIT, pip-installable, Cytoscape.js under the hood). Single-stage delivery — the component is imported, configured, and rendered directly in `app.py`. No build infrastructure, no `dist/` folder, no React scaffold.

**Why not 3d-force-graph**: 3D navigation was tested as an HTML prototype (TASK-003). Found disorienting in practice — camera jumps on click, node labels not readable when the camera is pulled back, fly-through controls require muscle memory the user does not want to build for a daily tool. Polishing the 3D UX to production quality was estimated at 8–15 dev-days (custom Streamlit component + bidirectional bridge + label LOD tuning + camera animation tuning). `st-link-analysis` covers every visual and interaction requirement (directed arrows, color-coded edges with captions, always-visible labels, click callback, neighbor highlight, hop slider, type filter) in 1–2 dev-days of Python configuration. The 3D rotation, distance fog, and WASD fly-through are lost — they were not daily-use features anyway.
**Why not true hyperbolic H3 layout**: The only open-source H3 implementation (pyh3) is dead since 2015. H3 also requires a strict tree — this graph has cycles (ALTERNATIVE_TO, BUILDS_ON). fCoSE 2D force-directed produces equivalent readability at this scale.

**Data contract** (unchanged, library-agnostic): `get_node_neighborhood(node_id, depth)` returns `{"nodes": [...], "edges": [...]}` with type-based color fields. If the library ever changes, only the rendering call site changes — the data contract does not.

---

## 3. Technology Stack

| Layer | Technology | Rationale | Change from PoC? |
|-------|-----------|-----------|-------------------|
| Language | Python 3.11+ | Unchanged | No |
| LLM (primary) | Ollama + `qwen2.5:7b` | Zero cost, local, schema-constrained output | No |
| LLM (fallback) | Ollama + `qwen2.5:14b` / `phi4:14b` / cheap API | If 7B can't handle richer extraction | New |
| Database | SQLite via `sqlite3` | Same schema, new node/edge types | No DDL changes |
| Embeddings | `sentence-transformers` + `all-MiniLM-L6-v2` | Semantic dedup. ~90 MB model, CPU-only | New |
| Graph viz | `st-link-analysis` (Cytoscape.js) | 2D force-directed graph via Python config — directed arrows, edge colors/captions, always-visible labels, click callback, neighbor highlight | New (replaces streamlit-agraph) |
| Dashboard | Streamlit | Carried from PoC, extended with new tabs | Extended |
| HTML rendering | Jinja2 | Carried from PoC, updated templates | Extended |
| arXiv client | `requests` + `xml.etree` | Unchanged | No |
| HuggingFace client | `requests` + `json` | Unchanged | No |
| PDF extraction | PyMuPDF (`fitz`) | Unchanged | No |
| Data validation | Pydantic v2 | Unchanged, new models added | Extended |
| Scheduling | cron + `caffeinate -i` | Unchanged | No |
| Fuzzy matching | `difflib.SequenceMatcher` | Unchanged for concept linking | No |

**New dependencies for MVP**:
```
sentence-transformers==3.4.1   # Semantic embeddings for dedup
st-link-analysis==0.4.0        # 2D graph visualization (Cytoscape.js via Streamlit)
```

---

## 4. Data Flow Diagram

### Weekly Pipeline (MVP — Updated)

```
cron (Friday 18:00) + caffeinate -i
        |
        v
  pipeline.py
        |
  [Stages 1-2: Unchanged from PoC]
        |
        v
  Stage 1: Fetch arXiv + HF, dedup, pre-filter -> top 30 candidates
        |
        v
  Stage 2: Classification (updated)
        |
        v
+----------------------+     +----------------------+
| PaperAnalyzer        |     | GraphStore indexes   |
| analyze_paper()      |<----| - concept_index      |
| (LLMClient)          |     | - technique_index    |
+----------+-----------+     | - problem_index      |
           |                 +----------------------+
           v
    PaperAnalysis
    - problem_name/desc
    - technique_name/approach/innovation_type
    - practical_relevance, limitations
    - results_vs_baselines
    - tier, confidence, reasoning
    - alternative/baseline technique names
    - foundational concept names
           |
           v
  Stage 3: Storage (updated)
           |
           v
+----------------------+
| ConceptLinker        |
| link_paper_analysis()|
+----------+-----------+
           |
           v
  GraphStore:
    - Upsert Problem node + ADDRESSES edge
    - Upsert Technique node + INTRODUCES edge (Paper->Technique)
    - BUILDS_ON edges (Technique->Concepts)
    - BASELINE_OF / ALTERNATIVE_TO edges (Technique<->Technique)
    - Store Paper node (evidence + user interaction defaults)
           |
           v
  Stage 4: T5 Expansion (unchanged from PoC)
           |
           v
  Stage 5: Digest Rendering (updated)
           |
           v
+----------------------+
| ChangeDetector       |
| detect_weekly_changes|
| detect_trends        |
+----------+-----------+
           |
           v
+----------------------+
| DigestRenderer       |
| (updated templates)  |
+----------+-----------+
           |
           v
  digests/YYYY-MM-DD.html
  (with "What Changed" section)
```

---

## 5. Security Considerations

### No Changes from PoC

- No API keys required (unless cheap API fallback is activated — then key goes in `.env`, gitignored)
- No PII collected or stored
- All data is publicly available academic metadata
- SQLite is a local file; no network access to the database
- Jinja2 autoescape prevents XSS in rendered HTML
- User notes are stored locally — no privacy concern for a single-user tool

### New for MVP

- **If API fallback is used**: The API key is stored in `.env` (gitignored), referenced by env var name in config (`llm_api_key_env`). The key is never logged, never stored in the database, never committed to git.
- **User interaction data**: Read status, notes, and flags are stored in the Paper node's `properties` JSON. This is personal workflow data on the user's local machine — no sensitivity concern.
- **Embedding model**: `all-MiniLM-L6-v2` runs locally on CPU. No data is sent to external services for embedding computation.

---

## 6. Error Handling Strategy

### Unchanged from PoC

All PoC error handling patterns carry forward:
- ArxivFetcher: retry 3x with backoff on 5xx/429, abort on persistent failure
- HuggingFaceFetcher: degrade gracefully on any error
- OllamaLLMClient: retry up to 3 attempts on malformed JSON, return None on exhaustion
- Pipeline: try/except wrapper, mark run as failed on unhandled exception
- Logging: Python `logging` module, stderr + rotating file

### New Error Handling

| Component | Failure Mode | Behavior |
|-----------|-------------|----------|
| PaperAnalyzer | LLM returns incomplete analysis (missing problem/technique) | Log warning, fall back to PoC-style flat classification (tier + summary only). Paper appears in digest with reduced information |
| PaperAnalyzer | LLM invents technique names not in paper | Accept — the user validates during reading. Over time, prompt tuning improves accuracy |
| ConceptLinker | No matching technique for BASELINE_OF/ALTERNATIVE_TO | Log info, skip those edges. Paper still links to Problem and Concepts |
| ChangeDetector | No changes detected (first run or quiet week) | Return empty `WeeklyChanges`. Digest shows "No significant changes this week" |
| TaxonomyGenerator | LLM proposes incoherent categories | User reviews and rejects in CLI. No changes applied to database |
| EmbeddingService | Model fails to load (disk space, corrupted download) | Raise with clear error: "Embedding model not found. Install with: pip install sentence-transformers" |
| GraphVisualization | Too many nodes to render (>500 visible) | Filter by node type or show neighborhood only. Log warning about large graph |
| SearchService | No results for query | Return empty list. Dashboard shows "No results for '{query}'" |
| Migration script | Fails mid-migration | Database backup exists. Script is idempotent — safe to re-run after fixing the issue |

---

## 7. Configuration & Environment

### config.py Updates

```python
class Settings(BaseSettings):
    # --- Existing (unchanged) ---
    project_root: Path = ...
    db_path: Path = ...
    digest_output_dir: Path = ...
    template_dir: Path = ...
    log_dir: Path = ...
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout: int = 300
    ollama_max_retries: int = 3
    arxiv_categories: list[str] = [...]
    arxiv_fetch_delay: float = 3.0
    arxiv_max_results_per_category: int = 500
    arxiv_lookback_days: int = 30
    hf_fetch_delay: float = 1.0
    prefilter_top_n: int = 30
    prefilter_upvote_weight: float = 2.0
    prefilter_category_priorities: dict[str, int] = {...}
    concept_match_threshold: float = 0.85
    log_level: str = "INFO"

    # --- New for MVP ---
    llm_provider: str = "ollama"                    # "ollama" or "api"
    llm_api_model: str | None = None                # e.g., "claude-haiku-4-20250514"
    llm_api_key_env: str | None = None              # env var name for API key

    embedding_model: str = "all-MiniLM-L6-v2"      # for semantic dedup
    dedup_similarity_threshold: float = 0.90        # cosine similarity for merge

    taxonomy_max_categories: int = 20               # max auto-generated categories
    taxonomy_min_concepts_per_category: int = 3     # min concepts to form a category

    trend_window_weeks: int = 4                     # rolling window for trend detection
    trend_min_connections: int = 3                   # min new connections to be "trending"
    trend_decay_factor: float = 0.7                 # decay for older connections

    search_result_limit: int = 20                   # max search results

    class Config:
        env_file = ".env"
        env_prefix = "PM_"
        extra = "ignore"
```

### .env.example Updates

```bash
# Paper Monitoring — Environment Configuration (MVP)
# Copy to .env and adjust values as needed

# Ollama (primary LLM)
PM_OLLAMA_HOST=http://localhost:11434
PM_OLLAMA_MODEL=qwen2.5:7b

# LLM provider: "ollama" (default) or "api" (fallback)
PM_LLM_PROVIDER=ollama
# PM_LLM_API_MODEL=claude-haiku-4-20250514
# PM_LLM_API_KEY_ENV=ANTHROPIC_API_KEY

# Pre-filter tuning
PM_PREFILTER_TOP_N=30
PM_PREFILTER_UPVOTE_WEIGHT=2.0

# Semantic dedup
PM_DEDUP_SIMILARITY_THRESHOLD=0.90

# Logging
PM_LOG_LEVEL=INFO
```

---

## 8. Project Directory Structure (MVP)

Changes from PoC are marked with `(new)` or `(updated)`.

```
projects/paper-monitoring/
├── src/
│   ├── __init__.py
│   ├── config.py                       # (updated) new settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── arxiv.py                    # Unchanged
│   │   ├── huggingface.py              # Unchanged
│   │   ├── classification.py           # (updated) PaperAnalysis model
│   │   ├── graph.py                    # (updated) new node/edge models
│   │   ├── seeding.py                  # Unchanged
│   │   ├── search.py                   # (new) SearchResult model
│   │   ├── changes.py                  # (new) WeeklyChanges, TrendingTopic
│   │   └── taxonomy.py                 # (new) CategoryProposal
│   ├── services/
│   │   ├── __init__.py
│   │   ├── prefilter.py                # Unchanged
│   │   ├── classifier.py               # (updated) -> PaperAnalyzer + ConceptExtractor
│   │   ├── linker.py                   # (updated) link_paper_analysis()
│   │   ├── renderer.py                 # (updated) concept-first cards + changes section
│   │   ├── seeder.py                   # Unchanged
│   │   ├── search.py                   # (new) SearchService
│   │   ├── change_detector.py          # (new) ChangeDetector
│   │   ├── taxonomy.py                 # (new) TaxonomyGenerator
│   │   └── dedup.py                    # (new) deduplication logic
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── arxiv_client.py             # Unchanged
│   │   ├── hf_client.py                # Unchanged
│   │   ├── ollama_client.py            # (updated) -> OllamaLLMClient implementing LLMClient
│   │   ├── llm_client.py              # (new) LLMClient ABC + APILLMClient stub
│   │   ├── pdf_extractor.py            # Unchanged
│   │   └── embedding_service.py        # (new) EmbeddingService
│   ├── store/
│   │   ├── __init__.py
│   │   └── graph_store.py              # (updated) new query methods
│   ├── migrations/                     # (new)
│   │   ├── __init__.py
│   │   └── 001_mvp_schema.py           # PoC -> MVP data migration
│   ├── templates/
│   │   ├── digest.html.j2              # (updated)
│   │   └── partials/
│   │       ├── paper_card.html.j2      # (updated) concept-first fields
│   │       ├── concept_badge.html.j2   # Unchanged
│   │       └── changes_section.html.j2 # (new)
│   ├── dashboard/
│   │   ├── app.py                      # (updated) new tabs, interaction, graph viz via st-link-analysis
│   │   └── graph_3d.py                 # (legacy, replaced by st-link-analysis call in app.py)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging_config.py           # Unchanged
│   │   └── normalize.py                # Unchanged
│   ├── pipeline.py                     # (updated) PaperAnalyzer + ChangeDetector
│   ├── seed.py                         # (updated) uses LLMClient
│   ├── dedup.py                        # (new) CLI entry point
│   └── taxonomy.py                     # (new) CLI entry point
├── tests/                              # Updated with new test files
├── data/
│   ├── paper_monitoring.db
│   ├── paper_monitoring.db.bak         # (new) pre-migration backup
│   ├── textbooks/
│   └── logs/
├── digests/
├── run_weekly.sh
├── run_dashboard.sh
├── requirements.txt                    # (updated) new dependencies
├── .env.example                        # (updated)
├── .gitignore
└── README.md
```

---

## 9. Extensibility Notes

### Neo4j Migration Path (Unchanged)

The nodes+edges schema continues to map directly to Neo4j. The new node types (`problem`, `technique`, `category`) become Neo4j node labels. The new edge types become Neo4j relationship types. No structural changes needed for migration.

### Graph Visualization Upgrade Path

The graph delivery collapses to a single stage after the M1 review decision (2026-04-17):

1. **Stage 1 — 3D HTML prototype** (TASK-003, Done): `st.components.v1.html` with CDN-loaded `3d-force-graph`. Validated the node/edge data contract and confirmed that 3D navigation is disorienting in daily use. Decision: do not pursue 3D further.
2. **Stage 2 — st-link-analysis integration** (TASK-004): `st_link_analysis()` called directly in `app.py`. All visual features (directed arrows, color-coded edges with captions, always-visible labels, click callback, neighbor highlight) are configured via Python `NodeStyle` and `EdgeStyle`. BFS hop-slider and node-type filter are Python-side re-renders. Editing sidebar driven by the click callback's return value. No custom component scaffold.

**Future upgrade path**:
- **If the graph exceeds ~2000 visible nodes** and performance degrades, consider migrating to Sigma.js (WebGL-based) or graphology + Sigma — both produce 2D force-directed output with better rendering throughput than Cytoscape.js. The data contract (`get_node_neighborhood` returning nodes + edges JSON) is library-agnostic; only the rendering call site changes.
- **At Beta phase** when Streamlit is replaced, the React frontend can render the same nodes/edges JSON with any graph library. Current front-runner is Cytoscape.js again (so the visual style carries over), but this is not a binding decision.

### LLM Provider Swap

The `LLMClient` abstraction means adding a new LLM provider (e.g., a local model via `llama.cpp`, or a different API) requires only:
1. Implement the `LLMClient` interface
2. Add a config option for the new provider
3. Register it in the factory function

No caller code changes needed.

---

## 10. Three-Stage Prototype Strategy

Development proceeds through three validation stages, each building on the previous stage's confirmed output. The test domain is **tree-based models** (Decision Trees, Random Forests, XGBoost, Gradient Boosting, LightGBM, CatBoost) — chosen because the user has deep domain expertise, making quality assessment immediate.

### Stage 1 — Hand-crafted prototype (Milestone 1)

**Goal**: Validate the graph schema, GraphStore operations, visualization, and manual editing UI without any LLM dependency.

**Approach**: Manually author 15 tree-based concepts with hand-drawn relationships across all 5 node types and 7 edge types. Example nodes:
- Problem: "How to handle tabular data with mixed feature types"
- Technique: "XGBoost", "Random Forest", "LightGBM"
- Concept: "Decision Tree", "Ensemble Methods", "Gradient Boosting", "Bagging"
- Category: "Tree-Based Methods"
- Paper: Breiman 2001 (Random Forests), Chen & Guestrin 2016 (XGBoost)

Example edges: `Decision Tree PREREQUISITE_OF Random Forest`, `XGBoost ALTERNATIVE_TO LightGBM`, `Random Forest BUILDS_ON Bagging`, `XGBoost INTRODUCES Paper:1603.02754`.

**Validates**:
- DDL and GraphStore CRUD operations work correctly with all node/edge types
- Graph visualization renders the 5 node types with correct coloring and interaction
- Manual editing UI (add/remove/edit nodes and edges) works end-to-end
- Search ranking returns correct results across node types
- The data model feels right for navigation and daily use

**Exit criteria**: User reviews the 15-node prototype in the dashboard, performs manual edits, and confirms the schema and UI are solid. No LLM required.

### Stage 2 — LLM extraction prototype (Milestone 2)

**Goal**: Validate extraction prompt quality and `qwen2.5:7b` structured output reliability against known ground truth from Stage 1.

**Approach**: Select 15 real arXiv papers in the tree-based domain (or closely related). Run each through `PaperAnalyzer.analyze_paper()` with the concept-first extraction prompt. Compare LLM output against the hand-crafted graph from Stage 1.

**Validates**:
- LLM reliably produces valid JSON matching `PaperAnalysis` schema
- Extracted problems, techniques, and relationships are semantically correct
- ConceptLinker correctly matches LLM output to existing graph nodes
- BASELINE_OF and ALTERNATIVE_TO edges are accurate
- Error rate is low enough that manual correction is a polish step, not a rebuild

**Quality gate**: This is the decision point for `qwen2.5:7b`. If fewer than 12 of 15 papers produce correct decompositions:
1. Evaluate `qwen2.5:14b` locally (fits in 16 GB RAM)
2. If still insufficient, evaluate `phi4:14b`
3. Last resort: cheap cloud API fallback (< $5/month)

The pipeline does NOT proceed to Stage 3 until this gate passes.

**Exit criteria**: At least 12/15 papers correctly decomposed. Manual corrections needed are minor (property text edits, edge additions) — not wholesale restructuring of the extracted graph.

### Stage 3 — Full dataset extension (Milestones 3+)

**Goal**: Scale to the complete knowledge bank and validate ongoing pipeline operation.

**Approach**: Run textbook seeding (800+ concepts), enable weekly pipeline with the new extraction schema, and validate deduplication, taxonomy, and digest rendering at scale.

**Validates**:
- Textbook seeding produces clean concepts without excessive duplication
- Semantic dedup correctly merges equivalents while preserving distinct concepts
- Auto-generated taxonomy produces coherent categories
- Weekly digest "What changed" section surfaces meaningful insights
- Graph visualization remains performant with 800+ nodes

**Depends on**: Stage 1 (schema confirmed) and Stage 2 (extraction quality confirmed).

---

## 11. Pydantic Data Models (MVP)

### New Models

```python
# models/classification.py (updated)

class PaperAnalysis(BaseModel):
    """Concept-first decomposition of a paper. Replaces PaperClassification for new papers."""
    # Problem
    problem_name: str
    problem_description: str
    is_existing_problem: bool = False

    # Technique
    technique_name: str
    technique_approach: str
    innovation_type: str  # architecture|problem_framing|loss_trick|eval_methodology|dataset|training_technique
    practical_relevance: str
    limitations: str
    is_existing_technique: bool = False

    # Classification
    tier: int | None  # 1-5
    confidence: str | None  # high|medium|low
    reasoning: str | None

    # Evidence
    results_vs_baselines: str

    # Linking
    alternative_technique_names: list[str] = []
    baseline_technique_names: list[str] = []
    foundational_concept_names: list[str] = []

    # Failure handling
    classification_failed: bool = False
    raw_response: str | None = None


class PaperClassification(BaseModel):
    """PoC classification model. Retained for backward compatibility with existing papers."""
    tier: int | None
    confidence: str | None
    reasoning: str | None
    summary: str | None
    key_contributions: list[str] = []
    foundational_concept_names: list[str] = []
    classification_failed: bool = False
    raw_response: str | None = None


# models/search.py (new)

class SearchResult(BaseModel):
    node_id: str
    node_type: str
    label: str
    score: float
    properties: dict = {}
    match_field: str  # which field matched: "label", "approach", "description"


# models/changes.py (new)

class WeeklyChanges(BaseModel):
    new_techniques: list[dict] = []     # [{name, problem, paper_title}]
    new_problems: list[dict] = []       # [{name, technique_count}]
    new_edges: dict = {}                # {relationship_type: count}
    summary: str = ""                   # Human-readable summary

class TrendingTopic(BaseModel):
    node_id: str
    node_type: str
    label: str
    new_connections_this_week: int
    new_connections_4_weeks: int
    trend_score: float


# models/taxonomy.py (new)

class CategoryProposal(BaseModel):
    category_name: str
    category_description: str
    concept_names: list[str]    # concepts that belong to this category
    technique_names: list[str]  # techniques that belong to this category


# models/graph.py (updated — added AnalysisLinks)

class AnalysisLinks(BaseModel):
    """Summary of nodes and edges created from a PaperAnalysis."""
    problem_node_id: str | None = None
    technique_node_id: str | None = None
    paper_node_id: str
    concepts_linked: int = 0
    baselines_linked: int = 0
    alternatives_linked: int = 0
    problem_is_new: bool = False
    technique_is_new: bool = False
```

---

## 12. Known Shortcuts & Technical Debt

| Shortcut | Rationale | Resolution Path |
|----------|-----------|-----------------|
| `difflib.SequenceMatcher` still used for concept linking | Embedding-based matching deferred to post-MVP. 800 concepts is manageable with O(n) scan | Replace with embedding index if concept count exceeds 1500 |
| Inline CSS in HTML digest templates | Carried from PoC. Dashboard is the primary UI now | Extract to stylesheet if digest becomes a standalone product |
| No database migration framework (Alembic) | Single idempotent migration script is sufficient for one schema transition | Add Alembic if schema changes become frequent |
| Taxonomy is batch-generated, not incremental | Full re-clustering required when new concepts are added. Acceptable for monthly taxonomy refresh | Add incremental taxonomy (assign new concepts to existing categories) if refresh becomes burdensome |
| ALTERNATIVE_TO edges are bidirectional (two rows per pair) | Simplifies graph traversal queries at the cost of storage duplication | Accept — storage cost is negligible for the expected edge count |
| `st-link-analysis` BFS hop-slider requires full Python re-render on slider change | The slider updates session state, which re-filters nodes/edges and re-calls the component. Acceptable at <500 visible nodes | If interaction feels slow at scale, move to client-side BFS via JavaScript injection or migrate to a graph library with a streaming/partial-update API |
| APILLMClient is a stub, not implemented | Only needed if local models fail quality checks | Implement when/if the fallback is activated |
| Search is Python post-processing, not SQLite FTS | Fast enough for <1000 nodes | Add SQLite FTS5 virtual table if node count exceeds 2000 or search latency is noticeable |
