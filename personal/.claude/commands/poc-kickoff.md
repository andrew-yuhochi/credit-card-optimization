# PoC Kickoff — $ARGUMENTS

Launch the full documentation-first workflow for a PoC project. The real value of this process is the **conversation** — understanding what the user truly wants through back-and-forth dialogue before committing anything to paper.

Mandatory sequence: Discovery Conversation → Parallel Research (Technical + Market + UX) → PRD → TDD → Data Source Spec → Task Breakdown.

## Instructions

The user will provide a project name as the argument (e.g., `paper-monitoring`, `bookkeeping-app`, `influence-post-monitoring`, `credit-card-optimization`).

### Step 0: Team Composition Check

Before delegating to any subagent, briefly review the available agents in `.claude/agents/` and ask yourself: **does the current team cover every angle this project needs?** If an angle is missing (e.g., regulatory review, a specialist domain like medical/legal, a new kind of data work), flag it to the user and ask whether to create a new agent before proceeding. Do NOT invent agents silently. Most of the time the answer is "the existing team is sufficient" — this step is a 30-second sanity check, not a bureaucratic gate.

Current standard research-phase team: **research-analyst** (technical feasibility), **market-analyst** (commercial viability), **ux-designer** (user experience). Standard implementation team: **architect**, **data-pipeline**, **test-validator**, **content-writer**.

### Step 1: Validate Project
- Confirm the project name matches one of the known projects in `CLAUDE.md`
- Check if `docs/$ARGUMENTS/poc/` directory exists
- Check if any documents already exist there — if so, report their status and ask whether to start fresh or continue from where we left off

### Step 2: Discovery Conversation

**This is the most important step. Do NOT skip it. Do NOT start drafting documents yet.**

Have a genuine conversation with the user to understand their vision. Ask questions one at a time (not a wall of questions). Listen to their answers and ask follow-up questions based on what they share. The goal is to uncover what they truly want before writing anything down.

Start by asking the user to describe the project in their own words — what problem they're trying to solve and what success looks like to them. Then explore these areas through natural conversation, not as a checklist:

**Understanding the problem:**
- What triggered this idea? What pain point are they experiencing today?
- How are they currently solving this problem (manual process, existing tool, not solving it)?
- Who else might benefit from this besides themselves?

**Defining the PoC scope:**
- What is the minimum they need to see working to feel the PoC is a success?
- What would make them excited vs. what would be "nice to have"?
- Are there any hard constraints (specific data sources, budget, timeline)?
- What should explicitly be left out of the PoC?

**Understanding the data:**
- What data sources do they have in mind? Any preferences or existing relationships?
- Do they already have access to any APIs or data feeds?
- What format do they want the output in (dashboard, alerts, reports, CLI)?

**Clarifying the user experience:**
- Walk me through how you'd use this tool on a typical day
- What would trigger you to open it? What would you do after seeing the output?
- How often would you use it (daily, weekly, on-demand)?

**Important conversation rules:**
- Ask ONE question at a time, not multiple
- Build on the user's answers — reference what they just told you
- If something is unclear, ask a follow-up before moving on
- Don't assume — if you're not sure what they mean, ask
- It's okay for this step to take multiple back-and-forth exchanges
- When you feel you have a clear picture, summarize your understanding back to the user and ask: **"Did I capture this correctly? Anything I'm missing or got wrong?"**

Only proceed to Step 3 after the user confirms your understanding is correct.

Save the conversation summary to `docs/$ARGUMENTS/poc/DISCOVERY-NOTES.md` before proceeding.

### Step 3: Parallel Research Phase

Spawn **three agents in parallel** in a single message — do NOT run them sequentially:

**3a. research-analyst** (technical feasibility)
> Investigate technical feasibility for **$ARGUMENTS**: data sources, APIs, libraries, OSS prior art, performance, technical risks. Use `docs/$ARGUMENTS/poc/DISCOVERY-NOTES.md` as the authoritative source. Produce `docs/$ARGUMENTS/poc/RESEARCH-REPORT.md`. Do NOT cover market, competitive positioning, or UX — those are other agents' scope. Reference any specific technologies, data sources, or constraints the user mentioned in the discovery conversation.

**3b. market-analyst** (commercial viability)
> Assess commercial viability and market positioning for **$ARGUMENTS**: market size, segments, competitive landscape, pricing benchmarks, uniqueness/moat, commercial risks. Use `docs/$ARGUMENTS/poc/DISCOVERY-NOTES.md` as the authoritative source. Produce `docs/$ARGUMENTS/poc/MARKET-ANALYSIS.md` following the template at `docs/templates/MARKET-ANALYSIS-TEMPLATE.md`. Be honest about commercial viability — if the story is weak, say so.

**3c. ux-designer** (user experience)
> Translate the user's needs into UX requirements for **$ARGUMENTS**: user workflow mapping, interaction specification, information architecture, human-in-the-loop patterns, error/empty states. Use `docs/$ARGUMENTS/poc/DISCOVERY-NOTES.md` as the authoritative source — especially any direct user quotes about how they want to use the tool. Produce `docs/$ARGUMENTS/poc/UX-SPEC.md` following the template at `docs/templates/UX-SPEC-TEMPLATE.md`. Applies to every project — even CLI tools, emails, and alerts have UX decisions to make. **Also produce ONE Claude Design Brief for the single highest-risk UX surface** at `docs/$ARGUMENTS/poc/designs/<surface-slug>-brief.md` per your agent definition. After Step 3 completes, the main session will prompt the user to run Claude Design with that brief and save the prototype to `designs/<surface-slug>-prototype.{url,pdf}`.

Wait for all three reports. Then share the key findings with the user and ask: **"Any of these findings change your thinking? Anything you'd like to explore further before we draft the requirements?"**

Wait for user input before proceeding. The user may ask for follow-up research from any of the three agents before moving on.

### Step 4: Document Creation

Delegate to the **architect** agent:
> Draft the four gate documents (PRD.md, TDD.md, DATA-SOURCES.md, TASKS.md) for **$ARGUMENTS/poc**. Read DISCOVERY-NOTES.md, RESEARCH-REPORT.md, MARKET-ANALYSIS.md, and UX-SPEC.md as inputs. Follow your agent definition for responsibilities and the templates in `docs/templates/`. The PRD must weave in market positioning and UX decisions; PRD §3 Commercial Thesis (Agreed) must capture the adopted commercial verdict, uniqueness/moat, and monetization angle from the MARKET-ANALYSIS conversation — quote the user's actual decision, not just the analyst's recommendation. The TDD must surface non-functional requirements from those reports (multi-tenancy hooks, latency needs, etc.); DATA-SOURCES.md must include real sample responses; TASKS.md tasks must each have a one-sentence Context field, acceptance criteria, and Demo Artifact per the template. Self-review for internal consistency before reporting back.

After architect reports back, dispatch **business-analyst** (Mode A — PRD-drafting alignment):
> Run Mode A: review `docs/$ARGUMENTS/poc/PRD.md` against `docs/$ARGUMENTS/poc/MARKET-ANALYSIS.md`. Verify §3 Commercial Thesis (Agreed) faithfully captures the adopted verdict, uniqueness/moat, and monetization angle from the MARKET-ANALYSIS conversation. Verify §6 Scope IN and §7 Scope OUT align with the agreed thesis. Output ALIGNED / DRIFTING / VIOLATES per your output format and append to `docs/$ARGUMENTS/poc/ALIGNMENT-LOG.md`.

If BA returns DRIFTING or VIOLATES, surface the verdict to architect and ask architect to revise the flagged PRD sections BEFORE showing the user. Loop architect ↔ BA until verdict is ALIGNED.

Once BA reports ALIGNED, present a summary of key decisions to the user. Ask: **"Does this design capture your vision? Any changes before we start implementation?"**

Wait for user input. If changes are requested, update the affected documents and re-summarize only the changed sections.

### Step 5: Gate Review
Delegate to the **architect** agent with this task:
> Perform a Design → Implementation gate review for **$ARGUMENTS**. Verify that DISCOVERY-NOTES.md, PRD.md, TDD.md, DATA-SOURCES.md, and TASKS.md all exist in `docs/$ARGUMENTS/poc/`, are internally consistent, and are complete. Verify that the PRD reflects the user's stated priorities from the discovery notes. Report your verdict: PASS / PASS WITH NOTES / FAIL.

### Step 6: Summary
Present a summary to the user:
- List all documents created with their file paths
- Highlight how key decisions from the discovery conversation are reflected in the documents
- Show the first 3 tasks from TASKS.md as suggested starting points
- Remind the user to run `/implement TASK-001` to begin implementation
