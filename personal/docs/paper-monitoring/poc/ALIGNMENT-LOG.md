# Alignment Log — paper-monitoring / poc

---

## 2026-04-19 — Mode A PRD-drafting review: does PRD §3/§6/§7 faithfully capture the MARKET-ANALYSIS commercial verdict?

**Verdict**: ALIGNED
**Mode**: A
**Anchors**:
- PRD §3 Commercial Thesis (Agreed): "data engine first, content creation second, audience third, tool monetization fourth … (1) build the data engine (this PoC); (2) use it as a personal content-production tool … (3) at MVP, add the minimum UI needed for the tool to be demonstrable … (4) at Beta, offer the tool to subscribers/followers who are already asking 'what are you using?'"
- PRD §3 uniqueness/moat: "Concept lineage for content creators — an ML-specific knowledge graph with typed, labeled relationships (not citation graph), structured export designed for LinkedIn carousels / YouTube scripts / newsletters, and a weekly importance + resurrection signal tuned to applied ML."
- PRD §3 500-gate: "500+ newsletter subscribers OR 500+ engagements per LinkedIn/YouTube post"
- MARKET-ANALYSIS Commercial Verdict: "The correct sequence is: (1) build the data engine (PoC goal); (2) use it as a personal content-production tool while publishing consistently on LinkedIn/YouTube; (3) at MVP, add the minimum UI needed for the tool to be demonstrable to an audience; (4) at Beta, offer the tool to subscribers/followers who are already asking 'what are you using?'"
- MARKET-ANALYSIS on UI gate: "The custom interactive graph UI is not commercially justified at PoC stage … if the content channel reaches 500+ newsletter subscribers or the LinkedIn/YouTube content consistently generates 500+ engagements per post, the UI investment is justified."
- MARKET-ANALYSIS Implications: "Content export is non-negotiable … treat structured export … as a first-class feature of the data model, not a view-layer afterthought."
- MARKET-ANALYSIS Implications: "Weekly monitor is the commercial signal instrument. Track whether the user publishes a piece of content after each weekly monitoring run … Log this in the PoC data — it becomes the Beta decision input."
- PRD §6 Scope IN item 6: "Content export formatter: structured JSON and Markdown output containing all 8 content-production fields … CONTENT_ANGLES is non-negotiable."
- PRD §6 Scope IN item 7: "Commercial-signal instrument (§5): concept_queries + content_publications tables, signal CLI, usage-to-publication loop report."
- PRD §7 Scope OUT item 1: "Custom interactive graph UI … deferred to MVP conditional on the commercial-signal threshold (500+ newsletter subscribers or 500+ engagements per post)."

**Analysis**: All three checks pass. PRD §3 reproduces the four-step commercial sequence from MARKET-ANALYSIS Commercial Verdict verbatim and accurately names the niche ("concept lineage for content creators"). The 500-gate in §3 compresses "consistently generates" into a flat number, which is a minor editorial simplification but does not affect scope or decision logic. §6 Scope IN is in direct correspondence with each MARKET-ANALYSIS Implication: content export is first-class (item 6), commercial-signal instrument is present and scope-protected (item 7), multi-tenant user_id is on every table, and external visualization replaces custom UI. §7 Scope OUT explicitly defers the custom graph UI with the correct conditional, and defers auth/billing/deployment to Beta — exactly as the MARKET-ANALYSIS directs. No premature UI, no missing commercial instrument, no commercial thesis drift detected.

**Recommendation**: ALIGNED — proceed. PRD is ready to be locked. No revisions required before milestone planning.

**User outcome**: [Leave blank — to be filled when user decides]

---

## 2026-04-19 — Milestone 1 deliverables review: does what was built serve the north star?

**Verdict**: ALIGNED
**Mode**: B
**Anchors**:
- PRD §3 Commercial Thesis (Agreed): "data engine first, content creation second … (1) build the data engine (this PoC)"
- PRD §3 uniqueness/moat: "Concept lineage for content creators — an ML-specific knowledge graph with typed, labeled relationships (not citation graph), structured export designed for LinkedIn carousels / YouTube scripts / newsletters"
- PRD §4 SC-1: "Given any seeded concept (e.g., XGBoost), the export contains all 8 structured fields … populated with technically precise content. User can sit down with the export and draft a LinkedIn carousel or YouTube script in under 30 minutes."
- PRD §4 SC-2: "Edges show narrative relationship labels … User validates that browsing XGBoost → Gradient Boosting → AdaBoost → Boosting in Neo4j Browser shows the lineage coherently."
- PRD §4 SC-3: "Manual hand-crafted prototype (~15 tree-based model concepts) validated in Obsidian + Neo4j Browser (Stage 1)"
- PRD §4 SC-5: "Commercial-signal instrument running from day one. Each concept queried via the Concept Explorer is logged … readable via a simple CLI/query at any time."
- PRD §5 Commercial-Signal Instrument: "`concept_queries` (every Concept Explorer invocation … ) and `content_publications` (user-logged content produced … ). Both seeded from day one."
- PRD §6 Scope IN item 1: "Concept Explorer engine: query any concept by name, retrieve the full structured concept export (8 fields including CONTENT_ANGLES) from the redesigned `concepts` + `concept_relationships` tables. CLI-first; no custom UI."
- PRD §6 Scope IN item 2: "concept-first graph schema" with all 8 tables including `concept_queries`, `content_publications`, `user_id` on every table.
- PRD §6 Scope IN item 3: "Stage 1 — Manual hand-crafted prototype: ~15 tree-based model concepts and their relationships, hand-edited in Obsidian + Neo4j Browser"
- PRD §6 Scope IN item 4: "External visualization setup: export scripts + documentation for Obsidian … and Neo4j Browser (graph exploration with labeled edges on edges themselves)."
- PRD §6 Scope IN item 7: "Commercial-signal instrument (§5): `concept_queries` + `content_publications` tables, signal CLI, usage-to-publication loop report."
- PRD §7 Scope OUT item 1: "Custom interactive graph UI … deferred to MVP." (Milestone 1 uses Neo4j Browser + Obsidian — correct.)

**Analysis**: Every Milestone 1 deliverable maps cleanly to a PRD anchor. TASK-M1-001 (schema) directly delivers PRD §6 item 2 — all 8 tables including `user_id` on every table. TASK-M1-002 (AI-generated ground truth, user-validated) is the Stage 1 prototype called for in PRD §6 item 3 and partially advances SC-1 by proving content-draft-ready quality at the hand-crafted level. TASK-M1-003 (seeder) populates the schema so Stage 1 is explorable. TASK-M1-004 (Concept Explorer CLI + SignalLogger) delivers SC-1 (8-field export, BUILDS_ON lineage traversal) and SC-5 in full — the commercial-signal instrument is live and scope-protected exactly as §5 requires. TASK-M1-005 (GraphExporter → Obsidian vault + Neo4j Cypher, user-validated) delivers SC-2 and the external-visualization-only constraint of §7 Scope OUT item 1. No custom UI was built; the 15-concept tree-based domain was used as specified; all 101 relationships with narrative edge labels are in the graph. There is one thing to watch: SC-3 requires user-explicit validation ("does this schema capture what you need for content, and does the exploration in Obsidian/Neo4j match your aspirational UX closely enough to proceed?"). The tasks are marked Done, and the user validated the Obsidian vault and Neo4j Cypher outputs (as stated in the proposal summary), which satisfies the Milestone 1 review checkpoint — no drift here. No pattern of scope creep or scope drift detected across either log entry to date.

**Recommendation**: ALIGNED — proceed to Milestone 2 gate. All five Milestone 1 tasks are delivered and map to their PRD anchors without drift. The commercial-signal instrument is running from day one as §5 requires. The Stage 1 ground truth is validated. Nothing in what was built touches §7 Scope OUT items (no custom UI, no publishing integration, no auth/billing). Milestone 2 (automated seed pipeline on tree-based models, Stage 2 validation) may begin.

**User outcome**: [Leave blank — to be filled when user decides]
