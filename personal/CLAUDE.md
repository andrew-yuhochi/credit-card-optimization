# Project Constitution — Claude's Automation Portfolio

## Identity
This workspace contains multiple automation PoC projects being developed by a Data Scientist & ML Engineer based in Canada. The projects share infrastructure patterns, coding standards, and a documentation-first development philosophy.

## Active Projects (in priority order)
1. **Paper Monitoring** — Automated workflow to surface influential ML/DS papers
2. **Bookkeeping App** — Household transaction tracking and financial planning automation
3. **Influence Post Monitoring** — Fund manager social media monitoring for trading signals
4. **Credit Card Optimization** — Expense-behavior-driven card recommendation engine (Canadian market)

## Development Workflow — MANDATORY

### The Documentation-First Rule
**No implementation code may be written for any feature, PoC, or task until the following documents exist in `docs/<project-name>/<current-phase>/`:**

1. `DISCOVERY-NOTES.md` — Captured requirements from conversation with the user
2. `PRD.md` — Product Requirements Document
3. `TDD.md` — Technical Design Document
4. `DATA-SOURCES.md` — Data Source Specification
5. `TASKS.md` — Task Breakdown

If these documents do not exist, **stop and create them first**. Do not proceed with implementation under any circumstance. Templates for all documents are in `docs/templates/`.

### Backlog Capture Rule
During implementation or conversation, new requirements frequently emerge that were not in the original PRD. These must be captured immediately — never built silently and never forgotten.

**When to log**: Any time a discussion introduces a requirement, feature, or behavior that is not described in the project's current PRD.md, log it to `docs/<project-name>/<current-phase>/BACKLOG.md` using the template at `docs/templates/BACKLOG-TEMPLATE.md`.

**Who logs**: The main session (you) is responsible for detecting and logging backlog items during conversation. The architect agent reviews the backlog during phase-gate checks.

**Rules**:
1. **Log first, discuss second.** When a new requirement surfaces, add it to BACKLOG.md before continuing the conversation about whether or how to build it.
2. **Backlog items are NOT approved for implementation.** They stay in BACKLOG.md until the user explicitly promotes them to TASKS.md.
3. **Never implement an untracked requirement.** If you find yourself building something that isn't in TASKS.md or BACKLOG.md, stop and log it.
4. **Create BACKLOG.md on first entry.** If the file doesn't exist yet for a project, create it from the template when the first backlog item is identified.

### Conversation-First Principle
The real value of documentation is the **conversation** that produces it. Before drafting any document, have a genuine back-and-forth conversation with the user to understand what they truly want. Ask questions one at a time, listen to answers, and ask follow-ups. Never assume — always ask. Documents are the *record* of shared understanding, not a substitute for it.

### Three-Phase Development Framework
Every project follows a three-phase lifecycle. Each phase has a distinct goal, and phases do not blend.

| Phase | Definition | User | Goal |
|-------|-----------|------|------|
| **PoC** | Proved prototype | You (testing) | Does the engine work? |
| **MVP** | Validated work for my own interests | You (daily use) | Does it reliably solve my problem? |
| **Beta** | Commercial validation with beta users | External users | Will people pay for this? |

**PoC phase**: Build the core engine. Prove the data flows, processing works, and output is useful. Manual runs are fine. Polish is deferred. The goal is technical validation, not daily usability.

**MVP phase**: Harden the proved prototype into something you depend on daily. Focus on reliability (error recovery, graceful degradation), automation (runs unattended), UX refinement (output is pleasant and scannable), and configuration (adjustable without editing code). New features are allowed when they are critical to daily usability — each triggers research-analyst if it introduces a new external dependency. Feature expansion beyond daily usability is resisted.

**Beta phase**: Validate the commercial thesis with real users. Adds auth, billing, multi-user UI, deployment infrastructure, marketing, and landing pages. Only begins after MVP has shipped value for ~3 months of personal use.

**Phase boundaries are strict:**
- **PoC does NOT include**: polish, automation, deployment, auth, billing
- **MVP does NOT include**: auth, billing, multi-user UI, marketing, landing pages
- **Beta unlocks everything**, but only after MVP proves the tool works

**Architecture choices that preserve commercial option value** (applied from PoC onward at ~5-10% upfront effort):
1. **Multi-tenant data model from day one.** `user_id` / `tenant_id` on every table. Single-tenant in PoC and MVP; activated in Beta.
2. **Domain primitives as first-class data.** What makes the product different lives in the database schema, not view-layer logic.
3. **Plugin / registry interfaces at every external boundary.** Parsers, data sources, ML clients — registered through an interface, not selected by `if source == "X"`.
4. **Abstracted ML / LLM clients.** Model imports use the abstract interface only. Provider swaps touch only the client module.
5. **Configuration over hardcoding.** Categories, rules, thresholds, labels, and seed data live in config or database rows.
6. **Forward-compatible schema decisions.** Spend 2-4 hours upfront to avoid later migrations.

**One cheap commercial-signal instrument per project.** Identified during PoC discovery, running during MVP, acted on at Beta decision point. Example: bookkeeping-app's classifier performance panel; paper-monitoring's click-through rate. Protect this in scope cuts.

**Beta decision rule.** After ~3 months of MVP personal use, ask: (a) does the tool solve my problem? (b) does the reliability/UX meet my standard? (c) does the commercial signal instrument show promise? These answers decide whether to begin Beta or enjoy the personal tool. Do not start Beta work until MVP is shipping value monthly.

**Applies to every project in the portfolio.** During `/poc-kickoff` discovery, the user may adjust this framing for a specific project — but the default is this three-phase lifecycle.

### Phase-Specific Workflows

**PoC Workflow** (full kickoff):
```
/poc-kickoff → Discovery Conversation
  → Market Research (market-analyst, commercial viability)
  → User Review & Objective Adjustment
  → Parallel Research (research-analyst + ux-designer)
  → PRD → TDD → Data Source Spec → Task Breakdown (milestones)
  → Implement (milestone by milestone) → Test → Documentation
  → PHASE-REVIEW.md → User decides: proceed to MVP?
```

The **PoC research phase runs in two stages**:
1. **Stage 1 — Market research first:** `market-analyst` runs alone (→ `MARKET-ANALYSIS.md`). User may adjust objectives before further research.
2. **Stage 2 — Technical + UX in parallel:** `research-analyst` (→ `RESEARCH-REPORT.md`) and `ux-designer` (→ `UX-SPEC.md`) run simultaneously, informed by the market analysis.

These three reports are **reference documents** that feed into the architect's PRD/TDD drafting. The 5 mandatory PoC gate documents remain: DISCOVERY-NOTES, PRD, TDD, DATA-SOURCES, TASKS.

**MVP Workflow** (lighter, iterative):
```
/phase-transition mvp
  → Read PoC PHASE-REVIEW.md + BACKLOG.md + completed TASKS.md
  → Define MVP-GOALS.md (daily-use acceptance criteria)
  → Update PRD/TDD for reliability + UX improvements
  → Plan milestones → Implement → Test → Daily use → Iterate
  → PHASE-REVIEW.md → User decides: proceed to Beta?
```

MVP features follow a lighter process: BACKLOG.md item → user promotes to TASKS.md → update relevant PRD/TDD section → implement → test. No full kickoff needed. New features that introduce new external dependencies trigger research-analyst before implementation.

**Beta Workflow** (full commercial cycle):
```
/phase-transition beta
  → Read MVP PHASE-REVIEW.md + BACKLOG.md + completed TASKS.md
  → Re-invoke market-analyst (commercial validation)
  → New documents: DEPLOYMENT.md, API-SPEC.md
  → Update PRD/TDD for multi-user, auth, billing
  → Plan milestones → Implement → Test → Deploy → Recruit users
  → PHASE-REVIEW.md
```

### Phase Transition Rules
At the start of any phase beyond PoC, planning **MUST** begin by reading:
1. Previous phase's `PHASE-REVIEW.md` — learnings and recommendations
2. `BACKLOG.md` — accumulated requirements not yet addressed
3. `TASKS.md` completed log — what was actually built

These inputs inform the new phase's goals, priorities, and task planning. Never plan from a blank slate. The architect produces the PHASE-REVIEW.md at the end of each phase; the user reviews it before the next phase begins.

### Milestone Rules
Tasks are organized into **milestones**, not sprints. Each milestone produces a **testable deliverable** that the user can validate.

- Every milestone has: a goal, acceptance criteria, and a user review checkpoint
- **Every milestone must have a user-observable deliverable.** No pure infrastructure milestones. If a milestone requires backend work (schema changes, refactors, migration scripts), bundle it with the first feature that makes the work visible in the UI or CLI. "Schema redesign" alone is never a milestone — "schema redesign + richer paper cards in the dashboard" is.
- The next milestone **cannot begin** until the user reviews and approves the current milestone's deliverable
- Milestones are scoped to be completable and testable independently
- See `docs/templates/TASKS-TEMPLATE.md` for the milestone structure

This ensures the user validates incrementally throughout development, not only at the end.

### Prototype Validation Rule
When a phase introduces a **significant schema, data model, or extraction logic change**, milestones must follow a three-stage prototype approach to validate the design before committing to full-scale implementation:

1. **Stage 1 — Manual prototype**: Hand-craft a small dataset (~15 items) in a domain the user knows well. Build the visualization/UI. Let the user interact, edit, and validate the design. This validates: are the data structures right? Are the relationships useful? Is the UX adequate?
2. **Stage 2 — Small-scale validation**: Run the actual pipeline on a **representative sample** covering all source types (e.g., papers, surveys, textbooks, landmark papers) in the **same domain** as Stage 1. Compare output against the hand-crafted ground truth. This validates: does the pipeline produce useful output? Are the extraction, processing, and storage steps working correctly? Any quality issues to fix before scaling?
3. **Stage 3 — Full extension**: Only after Stages 1 and 2 pass, extend to the full dataset. This is now a scale exercise, not a design exercise.

**Why this matters**: Building the full pipeline and seeding hundreds of items before visualizing the result risks discovering fundamental design flaws after hours of processing. Stages 1 and 2 are cheap validation gates (~1 day each) that prevent expensive rework.

**When to apply**: Any time a milestone involves (a) a new data model or schema, (b) new LLM extraction prompts, or (c) a new visualization that hasn't been validated with real data. If the change is incremental (adding a field, tweaking a prompt), the full three-stage approach is not needed — use judgment.

**Domain selection**: The prototype domain should be one the user has full mastery over, so they can judge quality without external reference. Ask the user to choose during milestone planning.

### How to Start Work
- New PoC: Run `/poc-kickoff <project-name>` (starts with a discovery conversation)
- Phase transition: Run `/phase-transition <mvp|beta>` (reads previous phase docs, plans next phase)
- New feature in current phase: Discuss with the user first, update docs, then run `/implement <task-id>`
- Bug fix: Can proceed directly but must update TASKS.md afterward

## Coding Standards

### Language & Frameworks
- **Primary language**: Python 3.11+
- **API framework**: FastAPI
- **Frontend**: React (when needed, deferred for PoC phase)
- **Database**: PostgreSQL (production), SQLite (PoC prototyping)
- **Data processing**: pandas, polars (prefer polars for new work)
- **ML/AI**: scikit-learn, transformers, Anthropic API
- **Testing**: pytest with minimum 80% coverage target for core logic

### Python Conventions
- Use type hints on all function signatures
- Use dataclasses or Pydantic models for structured data
- Use `pathlib.Path` instead of string paths
- Use `logging` module, not `print()` for operational output
- Use virtual environments (`venv`) per project
- Pin dependencies in `requirements.txt` with exact versions

### Project Structure (per PoC)
See `docs/STRUCTURE.md` for the per-project directory layout.

### Git Conventions
- Branch naming: `<type>/<project>/<short-description>` (e.g., `feat/paper-monitoring/arxiv-integration`)
- Commit messages: Conventional Commits format — `type(scope): description` (types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `data`)
- Always commit docs before implementation code

### GitHub Rules — MANDATORY
These rules apply to every project in this workspace without exception:

1. **GitHub account**: All repositories must be pushed to GitHub account **`andrew-yuhochi`**. Before any `git remote add` or `gh repo create`, verify the target account is `andrew-yuhochi`. Never push to a different account.

2. **Create the GitHub repo at first task completion**: The very first task completed in a new PoC **must** include creating the GitHub remote before the push. Specifically, when marking the first task Done:
   - Check whether the project directory has a `git remote` configured (`git remote -v`).
   - If no remote exists, create a new **public** repo under `andrew-yuhochi` named after the project directory (e.g., `paper-monitoring`), set it as `origin`, and push.
   - The description field should be the first sentence of the project README.
   - After creating the remote, scrub any embedded token from the URL in `.git/config` — use `https://github.com/andrew-yuhochi/<repo>.git` as the stored remote, and rely on `GIT_TOKEN`/`gh auth` for authentication at push time.
   - Never create the repo before the first task is actually complete — no empty-repo placeholders.

3. **Push after every completed task**: After marking a task as Done in TASKS.md, push the commit to GitHub. No task is considered complete until its code is on the remote. The push is part of the task-completion checklist below, not optional.

4. **"Built with Claude Code" in every README**: Every project README.md must include the line:
   ```
   > Built with [Claude Code](https://claude.ai/code)
   ```
   placed directly below the project description at the top of the file. Add this when creating or first updating any README. Never omit it. **Before every task-completion push, verify the line is still present** — if it is missing, restore it in the same commit that closes the task.

5. **Portfolio-infrastructure files are never pushed to GitHub**: The following are local-only — they may be committed locally for versioning, but they must NOT be included in any `git push` or pull request:
   - `CLAUDE.md` (root Project Constitution)
   - `.claude/**` (agents, commands, hooks, skills, settings, agent-memory)
   - `docs/templates/**`
   - `docs/STRUCTURE.md`

   These are personal workflow configuration, not project deliverables. Rules 2–3 above (repo creation, push-after-task) apply only to files under `projects/<project>/**` and `docs/<project>/<phase>/**`. **Never mix infra and project files in the same commit.** If you discover a commit that mixes them, split it locally before pushing — or do not push that commit. When in doubt, ask the user.

### Task Completion Checklist — MANDATORY
Every time a task is marked Done, execute these steps in order. Do not skip, reorder, or defer any step.

1. **Update `docs/<project>/<current-phase>/TASKS.md`**: change the task's `**Status**` to `Done (YYYY-MM-DD)` using today's date.
2. **Verify README compliance**: confirm `projects/<project>/README.md` contains the `> Built with [Claude Code](https://claude.ai/code)` line directly below the top-level description. If missing, delegate to content-writer to restore it — main session edits to README.md are blocked by the delegation-guard hook.
3. **Stage the task's code + the TASKS.md update** (specific files, not `git add -A`).
4. **Commit** with a Conventional Commits message scoped to the task id, e.g. `feat(paper-monitoring): complete TASK-011 weekly pipeline ingestion`.
5. **Ensure remote exists**: run `git remote -v`. If empty, this is the first task — create the GitHub repo per GitHub Rule #2 before continuing.
6. **Push** to `origin main` (or the task branch, if one exists). A task is not Done until the push succeeds. Per GitHub Rule #5, only project files (`projects/<project>/**`, `docs/<project>/<phase>/**`) get pushed; portfolio-infra files (CLAUDE.md, `.claude/**`, `docs/templates/**`, `docs/STRUCTURE.md`) stay local — never include them in a task-completion push.
7. **Report back to the user**: one line confirming the commit SHA and the GitHub URL.

If any step fails (hook failure, push rejected, README line missing), stop and fix the root cause before retrying. Never use `--no-verify` or force-push to bypass a failure.

### Security Rules
- Never commit API keys, tokens, or secrets
- Use `.env` files for local secrets (gitignored)
- Use `.env.example` with placeholder values checked into git
- Validate and sanitize all external API responses
- Log warnings for unexpected data formats, don't silently fail

## Tool Usage Discipline — MANDATORY

The main session's token footprint is dominated by file reads and command output that stay baked into the cached prefix for the rest of the conversation. Follow these rules to keep context lean.

### File reads and searches
- **Read files with the Read tool**, not `cat`/`head`/`tail`/`less` via Bash. Read paginates and truncates; Bash returns the full buffer into permanent context.
- **Search file contents with the Grep tool**, not `grep`/`rg` via Bash. Grep is tuned for truncation and structured output.
- **Find files with the Glob tool**, not `find`/`ls` via Bash.
- **Bash is for shell-only operations** — git, package managers, running scripts, and anything the dedicated tools cannot do.

### When you must use Bash
- Prefer `head -N` / `tail -N` over full-file dumps.
- Run `wc -l` first if you are unsure how large the output will be.
- For verbose commands, redirect to a temp file (`cmd >/tmp/log.txt 2>&1`) and then Read a slice — do not stream 20K+ lines into context.

### Re-reading the same file
Before reading a file a second time in the same session, pause: do you already have what you need in context, or should you delegate to a subagent that reads it in isolation? Repeated re-reads of the same file are one of the largest sources of context bloat in this workspace.

### Delegation for heavy reads
If a task requires reading several large files to produce a small answer, spawn a subagent with the Agent tool. The subagent's tool results stay in its own context; only its summary returns to the main session. This is the single biggest lever for keeping token usage bounded.

## Agent Coordination Rules

### Agent Inheritance Rule
Agents inherit all rules from this file (coding standards, security rules, workflow conventions, git conventions). Agent-specific instructions in `.claude/agents/` supplement, not replace, these standards. Do not duplicate CLAUDE.md content in agent definitions — reference it.

### Agent Delegation Guidelines

**Agents by phase:**

| Agent | PoC | MVP | Beta |
|-------|-----|-----|------|
| research-analyst | Full research | On-demand (new dependencies) | On-demand |
| market-analyst | Full analysis | — | Re-invoked |
| ux-designer | Full UX spec | On-demand (UX refinement) | Full UX generalization |
| architect | Full design + gate reviews | Update docs + gate reviews | Deployment arch + security |
| data-pipeline | Build engine | Harden + new features | Backend API endpoints |
| test-validator | Unit + integration | + regression, reliability | + E2E, load, accessibility |
| content-writer | README, code docs | Usage guide, changelog | User docs, marketing, API docs |
| devops-engineer | — | Scheduling, automation, basic deployment | CI/CD, Docker, cloud, monitoring |
| security-reviewer | — | — | OWASP, auth audit, penetration testing |

**PoC research phase runs in two stages:**
1. **Stage 1 — Market research first:** `market-analyst` runs alone (→ `MARKET-ANALYSIS.md`). User adjusts objectives before further research.
2. **Stage 2 — Technical + UX in parallel:** `research-analyst` (→ `RESEARCH-REPORT.md`) and `ux-designer` (→ `UX-SPEC.md`) run simultaneously.

**Design phase:**
- **architect**: Reads research reports + DISCOVERY-NOTES, produces gate documents (PRD, TDD, DATA-SOURCES, TASKS). Performs phase-transition gate reviews, security reviews, and PHASE-REVIEW.md at end of each phase.

**Implementation phase:**
- **data-pipeline**: Ingestion, transformation, and analytical processing code
- **devops-engineer**: Scheduling, deployment, automation, monitoring (MVP onward)
- **test-validator**: Testing and code review; does not modify implementation code
- **content-writer**: README, documentation, and user-facing content

### Team Composition Check
At the start of every PoC kickoff, briefly review `.claude/agents/` and ask whether the current team covers every angle this project needs. If a genuinely new angle is missing (regulatory review, a specialist domain, a new kind of data work), flag it to the user and ask whether to create a new agent before proceeding. Do NOT invent agents silently. Most of the time the standard team is sufficient — this is a 30-second sanity check, not a bureaucratic gate.

### Context Preservation
- When switching between PoCs, always re-read the relevant docs in `docs/<project-name>/<current-phase>/`
- Reference TASKS.md to understand current progress before starting work
- Update TASKS.md status after completing each task
