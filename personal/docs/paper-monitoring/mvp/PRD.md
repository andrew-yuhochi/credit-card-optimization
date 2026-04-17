# Product Requirements Document — Paper Monitoring (MVP)

> **Status**: In Review
> **Author**: Architect Agent
> **Last Updated**: 2026-04-17
> **Phase**: MVP
> **Preceding Phase**: PoC completed 2026-04-16

## 1. Problem Statement

The PoC proved that a zero-cost, fully local pipeline can ingest arXiv papers weekly, classify them by importance, and link them to a foundational knowledge bank. But the PoC also revealed a fundamental limitation: the system treats papers as primary citizens and concepts as supporting metadata. After five years, a user remembers the concepts — attention mechanism, residual connections, policy gradient — not which paper introduced them.

The MVP reframes the entire system around a core principle: **concepts are primary citizens, papers are supporting evidence.**

The user's goal: **understand any paper in 30 seconds.** Specifically:
- What problem does this paper address?
- What technique does it propose, and what is its core design?
- How does it compare to existing approaches?
- What do I need to know to evaluate it?
- Is this practically relevant to my work?

The PoC's flat summary and 2-bullet key_contributions cannot answer these questions. The MVP replaces this with structured decomposition into Problem, Technique, Concept, Category, and Paper nodes connected by 7 relationship types — producing a navigable knowledge graph, not a paper list.

## 2. Target User

**Primary user**: The project owner — a single Data Scientist and ML Engineer based in Canada. This remains a personal tool. Single-user throughout MVP.

**Context evolution from PoC**: The user has been running the PoC weekly pipeline since 2026-04-16. They are now familiar with the dashboard, knowledge bank, and classification output. The MVP addresses gaps the user identified during PoC validation: shallow extraction, flat concept browsing, no personal engagement tracking, and no landscape-shift visibility.

**Interaction model**: Weekly reading of the digest and dashboard. Occasional browsing of the knowledge graph to understand how concepts and techniques relate. Marking papers as read, adding personal notes, searching for specific concepts or techniques.

## 3. Success Criteria

### Daily Usability Criteria

- [ ] **SC-1**: When I see a new paper, I understand in 30 seconds what it does, how it's novel, and what I need to know to evaluate it — via structured Problem/Technique/Results decomposition on the paper card.
- [ ] **SC-2**: I can find any technique or concept and understand its relation to other concepts in under 30 seconds — via ranked search (name first) and graph visualization.
- [ ] **SC-3**: The weekly digest tells me what shifted in the landscape, not just what's new — via the "What changed in my graph" section.
- [ ] **SC-4**: Pipeline runs unattended every Friday without manual intervention (carried from PoC — already working).
- [ ] **SC-5**: No manual data cleanup needed after each run — semantic deduplication keeps the knowledge bank clean automatically.
- [ ] **SC-6**: Configuration changes don't require editing code (carried from PoC — already working via `config.py` and env vars).
- [ ] **SC-6b**: I can correct any LLM-generated relationship or node property through the dashboard — add missing edges, remove incorrect ones, edit node fields, and trust that my corrections persist through pipeline re-runs.

### Reliability Criteria

- [ ] **SC-7**: Pipeline runs for 3 consecutive months without requiring attention beyond weekly digest review.
- [ ] **SC-8**: Knowledge bank scales to 800+ concepts without performance issues in search or linking.
- [ ] **SC-9**: The richer extraction schema (Problem/Technique/baselines) produces reliably structured output from the LLM.

### Commercial Signal Criteria

- [ ] **SC-10**: Knowledge bank exceeds 800 concepts after textbook seeding.
- [ ] **SC-11**: More than 70% of classified papers link to 2+ existing concepts (indicates the knowledge bank is broad enough to be useful).
- [ ] **SC-12**: The "What changed" digest section surfaces non-obvious connections at least 2 out of 4 weeks.

## 4. Scope — What's IN

### Completed in PoC (carried forward)

These PoC capabilities remain operational and are not rebuilt:

- **arXiv ingestion**: 30-day lookback, 5 categories, dedup by ID, 429-aware retry logic
- **HuggingFace enrichment**: Community upvote signal for pre-filtering
- **Pre-filter scoring**: top-30 candidates by upvote + category priority
- **5-tier classification**: Game-changer through Survey taxonomy
- **Weekly cron + caffeinate scheduling**: Unattended Friday 6 PM execution
- **Streamlit dashboard**: Paper cards, tier filter, pipeline trigger, Knowledge Bank tab
- **T5 auto-expansion**: Survey papers automatically get concept extraction
- **Schema-constrained Ollama output**: `format=model_json_schema()` pattern

### MVP Feature 1: Concept-First Schema Redesign (BL-007)

**Core principle**: Problems, Techniques, and Concepts are the durable, primary nodes. Papers are leaf nodes that provide evidence.

**Five node types**:

| Node Type | Role | Example |
|-----------|------|---------|
| **Problem** | The question being addressed | "How to make LLM agent skills improve over time" |
| **Technique** | A specific approach/method/architecture | "SkillClaw (collective evolution via agentic evolver)" |
| **Concept** | Foundational knowledge unit (from knowledge bank) | "LLM agents", "attention mechanism", "tool use" |
| **Category** | Grouping — auto-generated taxonomy | "ML Algorithms", "Optimization", "NLP" |
| **Paper** | Evidence — introduces/validates techniques | "SkillClaw: Let Skills Evolve..." (arXiv:2604.08377) |

**Seven relationship types**:

| Edge | Connects | Answers |
|------|----------|---------|
| PREREQUISITE_OF | concept -> concept | "What do I need to know first?" |
| ADDRESSES | technique -> problem | "What problem does this technique tackle?" |
| BASELINE_OF | technique -> technique | "What established method does this compare against?" |
| ALTERNATIVE_TO | technique <-> technique | "What other approaches tackle the same problem?" |
| INTRODUCES | paper -> technique | "Which paper proposed this technique?" |
| BUILDS_ON | technique -> concept | "What existing concepts does this technique use?" |
| BELONGS_TO | concept/technique -> category | "What domain does this belong to?" |

**Richer paper extraction**: Each paper classified with:

| Field | What it answers |
|-------|----------------|
| Problem statement | "What specific problem does this paper address?" |
| Approach/architecture | "What's the core design?" |
| Key technique name | How you recall it ("SkillClaw", "Flash Attention") |
| Innovation type | architecture / problem_framing / loss_trick / eval / dataset |
| Results vs. baselines | "How much better, over what?" |
| Practical relevance | "Why would I use this at work?" |
| Limitations | "What doesn't it do well?" |

**Example — SkillClaw in the concept-first schema**:
```
Problem: "How to make LLM agent skills improve over time"
  +-- ADDRESSES <-- Technique: "SkillClaw"
  |     +-- innovation_type: architecture
  |     +-- practical_relevance: "Use when building multi-user agent systems"
  |     +-- INTRODUCES <-- Paper: 2604.08377 (evidence: +88% on WildClawBench)
  |     +-- BUILDS_ON --> Concept: "LLM agents", "tool use", "skill libraries"
  |     +-- ALTERNATIVE_TO <-> Technique: "Voyager", "JARVIS"
  +-- ADDRESSES <-- Technique: "Voyager"
        +-- INTRODUCES <-- Paper: 2305.16291
```

**Subsumes**: BL-004 (paper decomposition) and BL-006 (split concept relationships).

### MVP Feature 2: Comprehensive Textbook Seeding (BL-002)

Expand the knowledge bank from 492 concepts (PoC) to 800+ concepts by seeding from 5 textbooks across ~86 chapters. Infrastructure already exists from PoC (PdfExtractor, chunked chapter processing, source-type-aware prompts). The remaining work is processing time.

**Textbooks**:

| Textbook | Chapters | Status |
|----------|----------|--------|
| Murphy — *Probabilistic ML* (2022) | 23 chapters | 3 done in PoC, 20 remaining |
| Sutton & Barto — *RL: An Introduction* (2020) | 15 chapters (skip Psychology/Neuroscience) | 3 done in PoC, 12 remaining |
| Hastie et al. — *Elements of Statistical Learning* (2009) | 17 chapters | PDF downloaded, 0 done |
| Bishop — *Pattern Recognition and ML* (2006) | 14 chapters | PDF downloaded, 0 done |
| Zhang et al. — *Dive into Deep Learning* (2023) | 17 key chapters (skip Builders Guide, Computational Perf., Appendices) | PDF downloaded, 0 done |

### MVP Feature 3: Semantic Concept Deduplication (BL-003)

Embedding-based deduplication to merge semantically equivalent concepts (e.g., "MDP" vs "Markov Decision Process", "Bellman Equation" vs "Bellman Equations"). Uses concept descriptions — not just names — to distinguish true duplicates from legitimately different concepts with similar names (e.g., "prior distribution" vs "posterior distribution").

- Dry-run mode to preview merges before applying
- CLI: `python -m src.dedup --dry-run` / `python -m src.dedup --apply`
- Configurable cosine similarity threshold (default ~0.90)

### MVP Feature 4: User Interaction Layer (BL-011)

Fields on Paper node to track the user's engagement:

| Field | Type | Purpose |
|-------|------|---------|
| `user_status` | enum: unseen / skimmed / read / deep-dived | Track engagement depth |
| `user_notes` | freetext | Personal notes — doubles as personal search index |
| `last_accessed_at` | timestamp | Auto-updated on view/interact |
| `flagged_for_review` | boolean | Star/bookmark toggle |

Design decisions:
- Low friction: status is a dropdown, notes is a text box, flag is a toggle. No mandatory fields
- `last_accessed_at` auto-updates — zero friction
- Notes double as personal search terms (user's words match queries better than academic language)

### MVP Feature 5: Search Ranking (BL-008)

Replace flat text match with ranked field-priority search across all node types:

1. **Concept/technique/problem name** — exact or prefix match (highest priority)
2. **Technique name from papers** — name field of Technique nodes
3. **Description and other fields** — full-text match (lowest priority)

Searching for "attention" returns "Attention Mechanism" at the top, not buried under every concept that mentions "attention" in its description.

### MVP Feature 6: Concept Taxonomy (BL-009)

Auto-generated hierarchical grouping of concepts using LLM clustering:

- Category nodes (e.g., "ML Algorithms", "Optimization", "NLP") with BELONGS_TO edges
- LLM proposes groupings based on existing concept descriptions and domain tags
- User reviews and adjusts groupings via the dashboard
- Taxonomy is browsable: click a category to see all its concepts/techniques
- Re-clustering can propose new groups as the knowledge bank grows

### MVP Feature 7: "What Changed in My Graph" Digest (BL-010, Layers 1-2)

New section in the weekly digest that surfaces how the knowledge graph evolved, not just what papers appeared:

**Layer 1 — This week's graph changes** (always shown):
- New techniques added, new problems identified
- New ALTERNATIVE_TO / BASELINE_OF edges (competitive landscape shifts)
- Example: "This week: 2 new alternatives to Flash Attention, 1 new technique addressing long-context inference"

**Layer 2 — Accumulating trends** (rolling 4-week window):
- Concepts/problems gaining the most new connections over recent weeks
- Example: "Reinforcement Learning cluster growing: +4 techniques, +2 problems in the past 4 weeks"

Implementation approach:
- Query edge `created_at` timestamps grouped by target nodes
- Rank by new edges this week + rolling 4-week connections with decay factor
- Configurable thresholds for what counts as "trending"

### MVP Feature 8: Manual Graph Editing (BL-012)

The LLM will inevitably produce incorrect relationships, miss connections, or hallucinate nodes. The user must be the authority over the knowledge graph. Manual editing ensures every LLM error can be corrected immediately, and that corrections persist permanently.

**Editing capabilities**:

| Action | Description | Example |
|--------|-------------|---------|
| Add node | Create a Problem, Technique, or Concept the LLM missed | Manually add Concept: "Skill Libraries" |
| Delete node | Remove a noise node the LLM hallucinated | Delete Technique: "Generic Framework v2" (not a real technique) |
| Edit node properties | Fix descriptions, correct innovation_type, update practical_relevance | Change innovation_type from "architecture" to "training_technique" |
| Add edge | Create a relationship the LLM missed | Add ALTERNATIVE_TO between "XGBoost" and "LightGBM" |
| Remove edge | Delete an incorrect relationship | Remove BASELINE_OF between "Decision Tree" and "Neural Network" |
| Change edge type | Reclassify a relationship | Change BUILDS_ON to PREREQUISITE_OF between two concepts |

**Provenance tracking**: Every node and edge carries an `edited_by` field with value `"user"` or `"llm"`. When the user modifies a node or edge, the field is set to `"user"`. This provides:
- **Transparency**: The user can see which parts of the graph are LLM-generated vs. manually curated
- **Pipeline safety**: During re-classification (re-running a paper through the pipeline), user-edited nodes and edges are preserved — the pipeline skips or defers to any node/edge where `edited_by = "user"`
- **Authority**: User edits always override LLM output. If a conflict arises during re-classification, the user's version wins

**Design principles**:
- Edits are immediate — no save button, no approval workflow
- User edits override LLM output unconditionally
- Edits persist through re-classification runs
- Low-friction UI: sidebar form for adding nodes, inline properties panel for editing, delete with confirmation, edge creation via select-source-then-target workflow

**Subsumes**: No prior backlog items. Complements BL-007 (concept-first schema) — the richer schema makes editing more important because there are more relationship types to get wrong.

### MVP Feature 9: Knowledge Graph Visualization (BL-001)

Interactive graph visualization as primary navigation UI for the knowledge bank:

- Nodes colored by type (Problem, Technique, Concept, Category, Paper)
- Click a concept to see its prerequisites and related techniques
- Click a problem to see all approaches (techniques) that address it
- Click a technique to see its baselines, alternatives, and introducing paper
- Zoom, pan, and filter by node type
- Embedded in the Streamlit dashboard (streamlit-agraph or pyvis)

### Development Strategy: Three-Stage Prototype

Development follows a three-stage prototype approach designed to validate each layer of the system independently before scaling. The domain for the initial prototype is **tree-based models** (Decision Trees, Random Forests, XGBoost, Gradient Boosting, LightGBM, CatBoost) — a domain the user knows deeply, making quality assessment immediate and reliable.

**Stage 1 — Hand-crafted prototype (M1)**: 15 manually authored tree-based concepts with hand-drawn relationships. Validates the graph schema design, GraphStore operations, visualization rendering, and manual editing UI. No LLM involvement. Success criteria: the 5 node types and 7 edge types can represent the tree-based domain accurately; the user can navigate, search, and edit the graph; the data model feels right for daily use.

**Stage 2 — LLM extraction prototype (M2)**: 15 real arXiv papers processed through the LLM extraction pipeline (PaperAnalyzer + ConceptLinker). Validates extraction prompt quality, structured output reliability, and concept linking accuracy with `qwen2.5:7b`. This is the **quality decision point** for the local LLM: if `qwen2.5:7b` cannot reliably produce the concept-first decomposition, evaluate `qwen2.5:14b` or `phi4:14b` before proceeding. Success criteria: the LLM correctly identifies problems, techniques, and relationships for at least 12 of 15 papers; manual corrections needed are minor (property edits, not wholesale restructuring).

**Stage 3 — Full dataset extension (M3+)**: Extend to the complete textbook seeding (800+ concepts) and ongoing weekly pipeline. Validates scale, deduplication, taxonomy generation, and digest rendering. Only proceeds after M1 and M2 confirm the schema and extraction quality are solid.

**Why tree-based models**: The user has deep expertise in this domain, which means (a) hand-crafting 15 concepts with correct relationships is fast, (b) evaluating LLM extraction quality is immediate — no need to look things up, and (c) errors in relationships are obvious ("Random Forest is not a baseline for Linear Regression" is instantly detectable).

### LLM Constraint

- **Primary**: Ollama with local models (zero cost). `qwen2.5:7b` carried from PoC
- **Fallback**: Cheap cloud API models (e.g., Claude Haiku, GPT-4o-mini) may be considered if local models cannot handle the richer extraction quality required by the concept-first schema. Cost must remain minimal (< $5/month estimated)
- **Decision point**: **M2 (Stage 2 — LLM extraction prototype) is the quality gate for `qwen2.5:7b`**. Process 15 real papers and evaluate extraction quality against hand-crafted ground truth from M1. If extraction quality is insufficient (fewer than 12/15 papers correctly decomposed), evaluate `qwen2.5:14b` or `phi4:14b` locally before considering paid APIs. M3+ does not proceed until this gate passes

## 5. Scope — What's OUT

The following are explicitly excluded from the MVP:

- **User accounts or authentication**: Single-user tool. Multi-tenant data model columns (`user_id`) are present but inactive
- **Multi-user UI or sharing**: Personal tool only
- **Full website hosting / deployment**: Runs locally on the user's iMac
- **BL-005: NotebookLM integration**: Investigate API capabilities, but do not build until the core schema and interaction layer are solid
- **BL-010 Layer 3: Content creation opportunities**: Deferred until the user begins active content creation
- **Custom trained classifier**: Needs 6+ months of labeled data to be viable
- **Email or push notifications**: Opening the dashboard weekly is sufficient
- **Mobile or responsive design**: Desktop-only on the user's iMac
- **Additional data sources**: Semantic Scholar, OpenReview, industry blogs remain excluded
- **Citation count enrichment**: Near-zero for new papers; remains deferred
- **React frontend**: Streamlit remains the UI layer for MVP. Graph visualization is embedded via Streamlit-compatible libraries

## 6. User Workflow

### Weekly automated workflow (unchanged from PoC)

1. **Friday 6 PM**: cron triggers `run_weekly.sh` wrapped in `caffeinate -i`
2. Pipeline fetches 30 days of arXiv papers, enriches with HF upvotes, pre-filters to top 30
3. Papers are classified using the concept-first extraction schema (Problem, Technique, innovation type, results vs. baselines, practical relevance, limitations)
4. Classified papers create/link to Problem and Technique nodes in the graph
5. T5 surveys get concept extraction (knowledge bank expansion)
6. Results stored in SQLite; HTML digest rendered with "What changed" section
7. **~6:15 PM**: Pipeline completes

### User reading workflow (evolved from PoC)

1. Open the Streamlit dashboard or the weekly digest HTML
2. **Scan the "What changed" section**: Which problems are gaining traction? Which techniques are trending? Any new alternatives to approaches I use?
3. **Review new papers**: Each card shows Problem, Technique, Results vs. Baselines, Practical Relevance — understand the paper in 30 seconds
4. **Mark engagement**: Set status (skimmed / read / deep-dived), add personal notes, flag papers for later
5. **Explore the graph**: Click on a concept to see its prerequisites. Click on a problem to see all approaches. Navigate visually through the knowledge graph
6. **Search**: Type a concept or technique name, get ranked results instantly
7. **Browse taxonomy**: Explore the knowledge bank by category (ML Algorithms, Optimization, NLP, etc.)

### Periodic maintenance

- Review auto-generated taxonomy groupings and adjust as needed (monthly or after major knowledge bank expansion)
- Check deduplication dry-run output after textbook seeding batches

## 7. Assumptions

Carried from PoC (unchanged):
- **A-1**: Apple Silicon iMac with 16+ GB RAM (confirmed: M4)
- **A-2**: iMac powered on Fridays at 6 PM
- **A-3**: arXiv API remains free and unauthenticated
- **A-4**: HuggingFace Daily Papers API remains free and unauthenticated

New for MVP:
- **A-5**: `qwen2.5:7b` can reliably extract the richer concept-first schema (Problem, Technique, innovation type, results, limitations) from paper abstracts. If not, `qwen2.5:14b` or `phi4:14b` fits in 16 GB RAM as a local fallback
- **A-6**: Textbook PDFs remain available at their download URLs. PDFs are already downloaded to `data/textbooks/`; this assumption applies only if re-download is needed
- **A-7**: Embedding-based semantic similarity (for deduplication) can run locally using a small model — no paid embedding API needed. `sentence-transformers` with a small model (e.g., `all-MiniLM-L6-v2`) is sufficient
- **A-8**: 800+ concepts can be clustered into a meaningful taxonomy by the LLM in a single batch prompt. If the set is too large, cluster in segments by domain tag
- **A-9**: Streamlit-embedded graph visualization libraries (streamlit-agraph or pyvis) provide adequate interactivity for a personal tool. If not, the graph JSON export enables a standalone viewer

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `qwen2.5:7b` cannot reliably extract Problem/Technique/Concept decomposition from abstracts | Medium | High | Test with 10 papers early in Milestone 1. Fall back to `qwen2.5:14b` or `phi4:14b` locally. Cheap API fallback as last resort (< $5/month) |
| Schema migration breaks existing pipeline data | Medium | Medium | Write idempotent migration scripts. Back up database before migration. Rebuild-from-scratch option available since seeding is automated |
| Concept count beyond 800 degrades fuzzy matching performance | High | Low | BL-003 semantic dedup reduces count. Consider indexed or embedding-based lookup to replace `difflib` |
| Auto-generated taxonomy produces incoherent groupings | Medium | Medium | LLM proposes, user reviews and corrects. Start small, grow iteratively |
| Streamlit graph visualization is too slow for 800+ nodes | Medium | Medium | Filter by node type or category. Render only the neighborhood of a selected node, not the full graph. Consider pyvis over streamlit-agraph for performance |
| Textbook seeding page ranges incorrect | Medium | Low | TOC-verify every page range before running. PoC experience showed this is critical |
| Weekly cron fails silently during MVP development | Low | Low | Check `data/logs/pipeline.log` weekly. Cron remains installed throughout |
| Embedding model for dedup requires too much RAM alongside Ollama | Low | Medium | Run dedup CLI separately from pipeline (not concurrently). Use a small model (~90 MB for MiniLM) |

## 9. Future Considerations

These are referenced for context but are explicitly not part of the MVP:

- **BL-005: NotebookLM integration**: One-click deep-dive from paper card to interactive Q&A. Requires investigation of NotebookLM's API/ingestion capabilities
- **BL-010 Layer 3: Content creation opportunities**: Topics with enough depth in the knowledge bank for a "here's what you need to know about X" writeup. Deferred until the user begins content creation
- **Custom trained classifier**: After 6+ months of labeled data, fine-tune a lightweight classifier to replace or augment prompt-based classification
- **Full website hosting**: Replace local Streamlit with a hosted site for public access
- **Multi-user support**: Activate the `user_id` columns, add auth, share knowledge banks
- **Email/push digest delivery**: Notify when the weekly digest is ready
- **Additional data sources**: Semantic Scholar (citation velocity for older papers), OpenReview (conference decisions and reviews)
- **Neo4j migration**: Export the graph from SQLite to a production graph database. The nodes+edges schema is designed for direct migration
