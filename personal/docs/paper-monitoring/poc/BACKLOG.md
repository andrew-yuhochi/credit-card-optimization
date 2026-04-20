# Backlog — Paper Monitoring

> **Purpose**: Track requirements discovered during implementation that were NOT in the original PRD.
> **Rule**: Items here are **not approved for implementation** until explicitly promoted to TASKS.md by the user.
> **Last Updated**: 2026-04-19

## Backlog Items

| ID | Requirement | Source | Date | Priority | Status |
|----|------------|--------|------|----------|--------|
| BL-001 | Knowledge graph visualization as primary dashboard UI | User request during PoC review | 2026-04-16 | Medium | Backlogged |
| BL-002 | Comprehensive textbook seeding (5 books, ~86 chapters) | TASK-029 in TASKS.md, deferred from PoC | 2026-04-16 | High | Backlogged |
| BL-003 | Semantic concept deduplication (embedding-based) | TASK-030 in TASKS.md, deferred from PoC | 2026-04-16 | High | Backlogged |
| BL-004 | Paper decomposition: problem / solution / result structure | User request, SkillClaw example | 2026-04-16 | High | Backlogged |
| BL-005 | External learning gateway (NotebookLM integration) | User request | 2026-04-16 | Medium | Backlogged |
| BL-006 | Split concept relationships: prerequisites vs. alternative approaches | User request | 2026-04-16 | High | Backlogged |
| BL-007 | Knowledge graph redesign: relationship types + extractable information schema | User request, design discussion | 2026-04-16 | High | Backlogged |
| BL-008 | Search: prioritize name and technique/architecture over description fields | User request, current search returns too many irrelevant matches | 2026-04-16 | Medium | Backlogged |
| BL-009 | Concept taxonomy: hierarchical grouping / tagging of concepts | User request, concepts are flat with no navigable structure | 2026-04-16 | High | Backlogged |
| BL-010 | "What changed in my graph" digest + trending concepts + content opportunities | User request, monetization angle | 2026-04-16 | High | Backlogged |
| BL-011 | User interaction layer: read status, inline notes, last accessed, flagged | Design discussion, PKM research | 2026-04-16 | High | Backlogged |
| BL-012 | Edge-type distinction in Obsidian graph view (relationship-type icons/section headers) | Milestone 1 user validation | 2026-04-19 | Medium | Backlogged |
| BL-013 | Concept type distinction in Obsidian graph view (color-by-tag via frontmatter tags field) | Milestone 1 user validation | 2026-04-19 | Medium | Backlogged |
| BL-014 | Wikidata SPARQL label-matching fix: seed labels like "Gradient Boosting" return 0 results; Wikidata stores these as `Q-entity` labels not matching exactly — add QID-based lookup as primary path | TASK-M2-003 run observation | 2026-04-20 | Medium | Backlogged |
| BL-015 | Wikipedia title override table for concepts with non-standard names (e.g. "Information Gain / ID3 / C4.5", "Oblivious Trees") — current fallback to concept-name-only text degrades extraction quality | TASK-M2-003 run observation | 2026-04-20 | Medium | Backlogged |

## Item Detail

### BL-001: Knowledge Graph Visualization Dashboard
- **Source**: User stated the UI will evolve to a knowledge graph visualization, and deferred all current UI feedback in favor of this future direction
- **Context**: The current Streamlit dashboard uses card layout (Classified Papers) and a searchable list (Knowledge Bank). A graph visualization would render concepts, papers, and their relationships (BUILDS_ON, INTRODUCES, PREREQUISITE_OF) as an interactive node-edge diagram — much better suited to the graph-native data model already in GraphStore
- **PRD Impact**: New section needed for visualization requirements; UX-SPEC would need a graph interaction design
- **Effort Estimate**: High (new visualization library, interaction design, performance considerations for large graphs)
- **Decision**: Backlogged — natural fit for MVP phase when the UI is hardened for daily use

### BL-002: Comprehensive Textbook Seeding (5 Books, Full Coverage)
- **Source**: TASK-029 in TASKS.md — scoped during PoC implementation but deferred due to ~5h Ollama processing time
- **Context**: Current knowledge bank has 492 concepts from 2 textbooks (Murphy PML, Sutton RL) + 26 seed papers + weekly pipeline expansion. Full coverage across 5 books (adding Hastie ESL, Bishop PRML, Zhang D2L) would target 800+ concepts. PDFs already downloaded and TEXTBOOK_CONFIGS already updated with TOC-derived page ranges. Remaining work is running the seeding pipeline across ~86 chapters.
- **PRD Impact**: Strengthens SC-4 (knowledge bank size) and improves classification quality with a broader concept vocabulary
- **Effort Estimate**: Medium (code already exists — mainly Ollama processing time)
- **Decision**: Backlogged — MVP phase, run early to maximize knowledge bank benefit for the 4-week validation

### BL-003: Semantic Concept Deduplication
- **Source**: TASK-030 in TASKS.md — identified after TASK-027 produced 38 near-duplicates at 0.80+ name similarity
- **Context**: Current fuzzy matching (difflib, ratio >= 0.85) catches surface-level duplicates but misses semantic equivalences (e.g., "MDP" vs "Markov Decision Process") and produces false positives on legitimately different concepts (e.g., "prior distribution" vs "posterior distribution"). Needs embedding-based approach using concept descriptions, not just names. Includes dry-run mode and CLI interface.
- **PRD Impact**: New capability — knowledge bank quality/hygiene. Becomes critical after BL-002 significantly expands the concept count
- **Effort Estimate**: Medium (new embedding pipeline + merge logic + CLI)
- **Decision**: Backlogged — MVP phase, depends on BL-002

### BL-004: Paper Decomposition — Problem / Solution / Result
- **Source**: User request during PoC review. SkillClaw (2604.08377) used as motivating example — current summary and key_contributions are too shallow to understand what the paper is actually about without reading it
- **Context**: The project's objective is to build a knowledge bank that lets the user quickly understand papers instead of reading them fully. Current classification produces a flat `summary` (1 sentence) and `key_contributions` (2 bullet points). User wants structured decomposition: (1) **Problem** — what specific problem does the paper address? (2) **Solution** — what approach/method does the paper propose? (3) **Results** — what quantitative/qualitative evidence supports the solution? This maps to how academic papers are actually structured (intro → method → experiments)
- **PRD Impact**: Updates classification prompt in PRD Section 3.2; updates PaperClassification Pydantic model; updates TDD for Ollama prompt templates
- **Effort Estimate**: Medium (prompt redesign + schema change + re-classify existing papers)
- **Decision**: Backlogged — MVP phase. Core to the project's value proposition

### BL-005: External Learning Gateway (NotebookLM Integration)
- **Source**: User request — when the decomposed summary still isn't enough, provide a one-click gateway to deep-dive into the paper via an external tool like NotebookLM
- **Context**: NotebookLM can ingest PDFs and provide interactive Q&A. The idea is to make it trivially easy to go from "I see this paper is interesting" to "I'm learning from it" without manual PDF downloading and uploading. Could be as simple as a link that opens NotebookLM with the paper's PDF URL, or a more sophisticated integration
- **PRD Impact**: New feature — external tool integration section
- **Effort Estimate**: Low to Medium (depends on NotebookLM's API/URL scheme capabilities)
- **Decision**: Backlogged — MVP phase. Investigate NotebookLM's ingestion capabilities first

### BL-006: Split Concept Relationships — Prerequisites vs. Alternative Approaches
- **Source**: User request — current BUILDS_ON edges are too coarse. User wants two distinct relationship types to answer different questions
- **Context**: Currently all concept-to-paper links use a single `BUILDS_ON` edge type. User wants:
  (1) **Prerequisite concepts** — "what do I need to know to understand this?" (e.g., Linear Regression is prerequisite to Ridge Regression). Maps to the existing PREREQUISITE_OF edges in the knowledge bank but not surfaced for classified papers.
  (2) **Alternative approaches** — "what other methods tackle the same problem?" (e.g., Word2Vec vs GloVe both solve word embedding). This is a NEW relationship type — `ALTERNATIVE_TO` — that connects papers/methods addressing the same problem.
  Together these answer: where does this come from, what problem does it solve, how else could you solve it, and how effective is this approach?
- **PRD Impact**: New edge type ALTERNATIVE_TO in graph schema; classification prompt must identify both prerequisites and alternatives; updates GraphStore schema, Pydantic models, and dashboard display
- **Effort Estimate**: High (new graph relationships, prompt redesign, schema migration, UI changes)
- **Decision**: Backlogged — MVP phase. Superseded by BL-007 which provides the comprehensive redesign

### BL-009: Concept Taxonomy — Hierarchical Grouping and Tagging
- **Source**: User request — 492 concepts sit flat with no navigable structure, making it hard to browse by domain area
- **Context**: User wants to group concepts into hierarchical categories. Example: "ML Algorithms" contains { Linear Family (Linear Regression, Ridge, Lasso), Tree-Based (Decision Tree, Random Forest, XGBoost), Neural Networks (MLP, CNN, RNN) }. Or cross-cutting tags like "Classifier", "Optimizer", "Loss Function". This could be:
  (1) **Hierarchical categories** — tree structure (ML Algorithms → Linear Family → Ridge Regression). New node type `Category` with `BELONGS_TO` edges.
  (2) **Tags** — flat labels that allow multi-membership (Ridge Regression tagged as both "ML Algorithm" and "Regularization"). Stored as node properties or a lightweight tag system.
  (3) **Both** — categories for the primary hierarchy, tags for cross-cutting concerns.
  The existing `domain_tags` field on `ExtractedConcept` was intended for this but is underutilized — currently free-form strings from Ollama with no controlled vocabulary. A taxonomy would impose structure.
  With BL-007's richer schema, this becomes a natural fit — Problem nodes already group papers; Category nodes would group concepts. Together they provide two complementary navigation axes: "papers by problem" and "concepts by domain."
- **PRD Impact**: New Category node type in graph schema; taxonomy could be seeded manually or extracted by LLM; affects knowledge bank browsing, search, and graph visualization (BL-001)
- **Effort Estimate**: Medium (taxonomy design + seeding) to High (if auto-generated from existing concepts via LLM clustering)
- **Taxonomy approach**: Auto-generated by LLM (cluster existing concepts into groups), user reviews and adjusts. System proposes, user corrects. As knowledge bank grows, re-clustering can propose new groups or reassignments.
- **Decision**: Backlogged — MVP phase. Pairs well with BL-007 and BL-001 (graph visualization benefits enormously from grouping)

### BL-010: "What Changed in My Graph" Digest Section — Trending Concepts + Content Opportunities
- **Source**: User request — wants the weekly digest to surface how the knowledge graph evolved, not just list new papers. Also exploring content creation as a monetization path and professional brand building.
- **Context**: The current digest is a flat list of new papers ranked by tier. With the concept-first schema (BL-007), the digest can instead show **how the knowledge landscape shifted this week** — which is far more meaningful than "here are 30 new papers."

  **Weekly digest "What Changed" section — concrete examples:**
  - "This week: 2 new alternatives to Flash Attention, 1 new technique addressing long-context inference"
  - "New problem identified: 'skill evolution in multi-agent systems' — 3 papers this week, no prior techniques in your knowledge bank"
  - "Reinforcement Learning cluster growing: +4 techniques, +2 problems in the past 4 weeks"
  - "Technique 'LoRA' now has 6 alternatives — consider a comparison post"

  **Three layers of insight, from immediate to strategic:**
  1. **This week's graph changes** (always shown): new techniques, new problems, new ALTERNATIVE_TO / BASELINE_OF edges. Answers: "what's new in the landscape?"
  2. **Accumulating trends** (rolling 4-week window): concepts/problems gaining the most new connections over recent weeks. Answers: "what topics are heating up?"
  3. **Content opportunities** (optional section): topics with enough depth in the knowledge bank (5+ techniques, clear problem framing, known baselines) that are ready for a "here's what you need to know about X" writeup. Answers: "what's worth writing about now?"

  **Implementation approach:**
  - Query edge `created_at` timestamps grouped by target Problem/Technique/Concept nodes
  - Rank by: (new edges this week) + (new edges past 4 weeks × decay factor)
  - Layer 3 (content opportunities) filters for topics with sufficient graph density (configurable threshold)

- **PRD Impact**: New digest section; requires temporal edge tracking (already available via `created_at` on nodes from BL-007)
- **Effort Estimate**: Low for layer 1 (simple edge timestamp query), Medium for layers 2-3 (rolling window aggregation + density threshold)
- **Decision**: Backlogged — layers 1-2 are high value for daily use in MVP. Layer 3 (content opportunities) is lower priority until the user begins creating content. The underlying data (edge timestamps) will already exist from BL-007.

### BL-011: User Interaction Layer
- **Source**: Design discussion on 2026-04-16 + PKM research finding that the #1 cause of knowledge base abandonment is the system having no memory of user engagement
- **Context**: The current system has no representation of the user's engagement with papers or concepts. It can't distinguish a paper you've deep-dived into from one you've never seen. This prevents personalization (BL-010 "what changed" needs to know what you've read) and makes the knowledge bank feel like a static reference rather than a personal tool.

  **Agreed design — fields on Paper node:**
  | Field | Type | Purpose |
  |-------|------|---------|
  | `user_status` | enum: unseen / skimmed / read / deep-dived | Track engagement depth |
  | `user_notes` | freetext | Single inline text box on paper card — user's own words, personal search index |
  | `last_accessed_at` | timestamp | Auto-updated on view/interact — enables resurface queries and BL-010 trending |
  | `flagged_for_review` | boolean | Star/bookmark toggle for quick save |

  **Design decisions:**
  - Inline notes only, no structured fields — the LLM already handles structured decomposition (BL-007). User notes capture personal perspective the LLM can't produce ("reminds me of our ranking model issue")
  - Notes double as personal search index — user's own words match search queries better than academic language
  - Low friction: status is a dropdown, notes is a text box, flag is a toggle. No mandatory fields.
  - `last_accessed_at` is auto-updated, not manual — zero friction

- **PRD Impact**: New fields on Paper node properties; dashboard UI additions (status dropdown, notes box, flag toggle per card); enables BL-010 personalization
- **Effort Estimate**: Low (4 fields + 3 UI elements on paper card)
- **Decision**: Backlogged — MVP phase. Prerequisite for BL-010 personalization features. High priority due to abandonment risk.

### BL-008: Search — Ranked Field Priority
- **Source**: User feedback — current Knowledge Bank search returns all concepts where any field matches the search term, which surfaces too many irrelevant results
- **Context**: Current implementation is a flat string match across name + description. When searching for e.g. "attention", you get every concept that mentions "attention" anywhere in its description, burying the actual "Attention Mechanism" concept. Search should rank results by field priority: (1) concept/technique/architecture **name** — exact or prefix match first, (2) **innovation/technique name** from papers, (3) description and other fields. With BL-007's richer schema (Problem, Technique nodes), search becomes even more important — user needs to quickly find the right node by its primary identifier. May be superseded by graph visualization (BL-001) with built-in search, but the ranking logic applies regardless of UI
- **PRD Impact**: Updates search behavior in dashboard; with BL-007, extends to searching across Problem and Technique node types
- **Effort Estimate**: Low (ranking logic change) to Medium (if adding fuzzy/prefix matching)
- **Decision**: Backlogged — MVP phase. Applies whether UI stays as Streamlit or moves to graph visualization

### BL-007: Knowledge Graph Redesign — Concept-First Schema
- **Source**: User-driven design discussion on 2026-04-16. Motivated by SkillClaw (2604.08377) as example of insufficient current extraction. Subsumes and refines BL-004 and BL-006. Revised to concept-first principle after further discussion.
- **Context**: Discovery conversation established the user's paper-reading workflow:
  1. "What's new?" — usually a new approach to a known problem (b), then new result (c), then new problem (a)
  2. "Do I know the baselines?" — anchor understanding on familiar ground
  3. "Is the technique clever?" — novel insight (b) or creative recombination (a) triggers deep-dive; engineering tricks (c) needed for work
  4. Papers typically contribute ONE key innovation: architecture/design pattern (most common), then problem framing or loss/training trick, then eval methodology or dataset
  5. User recalls papers as: name → architecture → specific technique

  **Core principle: Concepts are primary citizens, papers are supporting evidence.**
  After 5 years you remember the concepts, not which paper they came from. The knowledge graph should reflect this: Problems, Techniques, and Concepts are the durable nodes. Papers are leaf nodes that provide evidence (results, authorship, date, venue).

  **Agreed design — Node types (4 primary + 1 evidence):**
  | Node | Role | Example |
  |------|------|---------|
  | **Problem** | Primary citizen. The question being addressed | "How to make LLM agent skills improve over time" |
  | **Technique** | Primary citizen. A specific approach/method/architecture | "SkillClaw (collective evolution via agentic evolver)" |
  | **Concept** | Primary citizen. Foundational knowledge unit | "LLM agents", "tool use", "attention mechanism" |
  | **Category** | Grouping. Auto-generated taxonomy (BL-009) | "ML Algorithms", "Optimization", "NLP" |
  | **Paper** | Evidence. Introduces/validates techniques | "SkillClaw: Let Skills Evolve..." (arXiv:2604.08377) |

  **Agreed design — Technique node fields (durable knowledge):**
  | Field | What it answers |
  |-------|----------------|
  | Name | How you recall it ("SkillClaw", "Flash Attention") |
  | Approach / architecture | "What's the core design?" |
  | Innovation type | architecture / problem_framing / loss_trick / eval / dataset |
  | Practical relevance | "Why would I use this at work?" |
  | Limitations / assumed conditions | "What doesn't it do well?" |

  **Agreed design — Paper node fields (evidence only):**
  | Field | What it answers |
  |-------|----------------|
  | Results vs. baselines | "How much better, over what?" — paper-specific evidence |
  | Authors, date, venue, arXiv ID | Provenance metadata |
  | Citation count / venue tier | Quality signals |
  | User status, notes, last accessed | Personal interaction layer |

  **Agreed design — Relationship types (concept-first):**
  | Edge | Connects | What it answers |
  |------|----------|----------------|
  | PREREQUISITE_OF | concept → concept | "What do I need to know first?" |
  | ADDRESSES | technique → problem | "What problem does this technique tackle?" |
  | BASELINE_OF | technique → technique | "What established method does this compare against?" |
  | ALTERNATIVE_TO | technique ↔ technique | "What other approaches tackle the same problem?" |
  | INTRODUCES | paper → technique | "Which paper proposed this technique?" (paper as evidence) |
  | BUILDS_ON | technique → concept | "What existing concepts does this technique use?" |
  | BELONGS_TO | concept/technique → category | "What domain does this belong to?" |

  **Example — SkillClaw in concept-first schema:**
  ```
  Problem: "How to make LLM agent skills improve over time"
    ├── ADDRESSES ← Technique: "SkillClaw"
    │     ├── innovation_type: architecture
    │     ├── practical_relevance: "Use when building multi-user agent systems"
    │     ├── INTRODUCES ← Paper: 2604.08377 (evidence: +88% on WildClawBench)
    │     ├── BUILDS_ON → Concept: "LLM agents", "tool use", "skill libraries"
    │     └── ALTERNATIVE_TO ↔ Technique: "Voyager", "JARVIS"
    └── ADDRESSES ← Technique: "Voyager"
          ├── INTRODUCES ← Paper: 2305.16291
          └── ...
  ```

- **PRD Impact**: Major — rewrites classification schema, prompt templates, Pydantic models, GraphStore schema, and dashboard rendering. Subsumes BL-004 (problem/solution/result) and BL-006 (prerequisite vs. alternative relationships)
- **Effort Estimate**: High (prompt redesign, schema migration, re-classification of existing papers, UI updates)
- **Decision**: Backlogged — MVP phase. This is the foundational redesign that BL-001 (graph visualization), BL-002 (textbook seeding), and BL-005 (NotebookLM gateway) all build on top of

---

### BL-012: Edge-type Distinction in Obsidian Graph View
- **Source**: Milestone 1 user validation (2026-04-19)
- **Description**: Obsidian's graph view renders all edges identically regardless of relationship type (BUILDS_ON, ALTERNATIVE_TO, PREREQUISITE_OF look the same). Users cannot visually distinguish relationship semantics in graph view. Neo4j handles this correctly via edge labels. A workaround for Obsidian would be to prefix wikilinks in the note body with relationship-type icons or section headers (e.g., "⬆ Built on: [[...]]", "↔ Alternatives: [[...]]") so the note body communicates type even if the graph cannot.
- **Priority**: Medium (Neo4j already solves this; Obsidian workaround is nice-to-have)
- **Phase**: MVP
- **PRD Impact**: Updates Obsidian exporter to prefix wikilinks by relationship type; no schema change needed
- **Effort Estimate**: Low (exporter change only)
- **Decision**: Backlogged — MVP phase. Neo4j users already have full edge-type visibility; this improves Obsidian-only users' experience.

### BL-013: Concept Type Distinction in Obsidian Graph View
- **Source**: Milestone 1 user validation (2026-04-19)
- **Description**: Users cannot distinguish Mechanism/Technique/Algorithm/Framework nodes by color in Obsidian graph view. Obsidian supports color-by-tag (not by frontmatter property). Fix: add `tags: [Algorithm]` (or the concept_type value) to each note's YAML frontmatter in the Obsidian exporter. Users can then assign colors per tag in Obsidian Settings → Graph → Groups.
- **Priority**: Medium
- **Phase**: Milestone 2 (cheap to add to the exporter before the full seed run)
- **PRD Impact**: Updates Obsidian exporter to emit `tags` in YAML frontmatter derived from the node's concept_type; no schema change needed
- **Effort Estimate**: Low (one-line change per node type in the exporter)
- **Decision**: Backlogged — Milestone 2. Cheapest to add before the full seed run so all exported notes carry the tag from the start.

---

## Promoted Items Log
<!-- Track items that were moved into TASKS.md -->

| Backlog ID | Promoted To | Date | Notes |
|-----------|-------------|------|-------|
