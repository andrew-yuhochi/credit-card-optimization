# MVP Goals — Paper Monitoring

> **Phase**: MVP (Validated work for my own interests)
> **Preceding Phase**: PoC completed 2026-04-16
> **Depends on**: PHASE-REVIEW.md from PoC phase (approved 2026-04-16)
> **Last Updated**: 2026-04-17

## What "Works for My Daily Use" Means

The MVP transforms a working PoC (pipeline runs, papers classified) into a personal knowledge tool that the user depends on weekly. The core shift: **concepts are primary citizens, papers are supporting evidence.**

### Daily Usability Criteria
- [ ] When I see a new paper, I understand in 30 seconds what it does, how it's novel, and what I need to know to evaluate it
- [ ] I can find any technique or concept and understand its relation to other concepts in under 30 seconds
- [ ] The weekly digest tells me what shifted in the landscape, not just what's new
- [ ] Pipeline runs unattended every Friday — no manual intervention needed
- [ ] No manual data cleanup needed after each run
- [ ] Configuration changes don't require editing code

### Reliability Criteria
- [ ] Pipeline recovers from network errors without losing data (carried from PoC — already working)
- [ ] Runs for 3 consecutive months without requiring attention beyond weekly digest review
- [ ] Handles the richer extraction schema (problem/technique/baselines) without degraded quality
- [ ] Knowledge bank scales to 800+ concepts without performance issues in search or linking

### UX Criteria
- [ ] Paper cards show structured decomposition: problem, technique, results vs. baselines, practical relevance
- [ ] Concept/technique relationships are visible: prerequisites, alternatives, baselines
- [ ] Knowledge bank is browsable by taxonomy (hierarchical grouping)
- [ ] Search returns concepts/techniques by name first, not buried under description matches
- [ ] I can mark papers as read, add personal notes, and flag papers for review
- [ ] Weekly digest highlights "what changed in my knowledge graph" — not just new papers

### Commercial Signal Instrument
- **Instrument**: Knowledge graph growth rate + concept reuse in classification
- **What it measures**: Does the system get smarter over time? Measured by: (a) weekly concept count growth, (b) percentage of classified papers that link to 2+ existing concepts (indicates the knowledge bank is broad enough to be useful), (c) whether the "what changed" digest section surfaces non-obvious connections
- **Target after 3 months**: (a) Knowledge bank > 800 concepts, (b) > 70% of classified papers link to 2+ concepts, (c) user finds the "what changed" section valuable at least 2 out of 4 weeks

## Features Carried from PoC Backlog

| Backlog ID | Feature | Why it's needed for daily use |
|-----------|---------|-------------------------------|
| BL-007 | Knowledge graph redesign (concept-first schema) | Foundation — without richer extraction, papers remain opaque. Enables the "30-second understanding" goal |
| BL-002 | Comprehensive textbook seeding (5 books) | Broader knowledge bank means more papers link to known concepts. Directly improves the "what do I need to know" experience |
| BL-003 | Semantic concept deduplication | Prevents duplicate concepts from confusing search and taxonomy. Quality gate after BL-002 expansion |
| BL-009 | Concept taxonomy (auto-generated) | Makes 800+ concepts navigable. Without grouping, the knowledge bank is a flat unsearchable list |
| BL-010 | "What changed in my graph" digest | Transforms the digest from "new papers" to "what shifted in the landscape" — the user's third acceptance criterion |
| BL-011 | User interaction layer | Personal notes, read status, flagged papers. Prevents knowledge bank abandonment (PKM research: #1 failure mode) |
| BL-008 | Search ranking | Find concepts by name in under 30 seconds — the user's second acceptance criterion |
| BL-001 | Knowledge graph visualization | Navigate relationships visually. The concept-first schema is a graph — it should look like one |

## Features NOT Included (deferred to Beta or later)

| Feature | Why deferred |
|---------|-------------|
| Auth / user management | Beta concern — personal use only |
| Multi-user UI | Beta concern |
| BL-005: NotebookLM integration | Investigate API first; low urgency until core experience is solid |
| BL-010 layer 3: Content creation opportunities | User hasn't started content creation yet |
| Custom trained classifier | Needs 6+ months of labeled data |
| Full website hosting | Personal tool runs locally |
| Email / push notifications | Opening dashboard weekly is sufficient |

## LLM Model Constraint Update

- **Primary**: Ollama with local models (zero cost). qwen2.5:7b carried from PoC.
- **Fallback**: Cheap cloud API models (e.g., Claude Haiku, GPT-4o-mini) may be considered if local models cannot handle the richer extraction quality required by BL-007. Cost must remain minimal (< $5/month estimated).
- **Decision point**: Test qwen2.5:7b against new BL-007 prompts in Milestone 1. If quality is insufficient, evaluate qwen2.5:14b or phi4:14b locally before considering paid APIs.

## Success Definition

After ~3 months of weekly use, this MVP is successful if:
1. [ ] All daily usability criteria are consistently met
2. [ ] The three core experiences work: 30-second paper understanding, 30-second concept lookup, landscape-shift digest
3. [ ] The knowledge bank has grown beyond 800 concepts with clean taxonomy
4. [ ] The commercial signal instrument shows the system is getting smarter (concept reuse rate increasing)
5. [ ] The user opens the dashboard every week because it's useful, not out of obligation
6. [ ] Technical debt is documented and manageable
