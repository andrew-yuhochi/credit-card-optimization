# Implement Task — $ARGUMENTS

Dispatch a single task to the **data-pipeline** subagent, then the **test-validator** subagent. Do NOT implement in the main session — that violates the Agent Delegation rule and bloats context. The delegation-guard hook will actively block direct edits to `projects/*/src/**` from main.

## Instructions

Parse `$ARGUMENTS` as `<project-name> <task-id>` (e.g., `paper-monitoring TASK-001`). Extract `project` and `task_id`.

### Step 1: Documentation Gate Check (main session)

Verify all five mandatory documents exist in `docs/<project>/<current-phase>/`:
- `DISCOVERY-NOTES.md`
- `PRD.md`
- `TDD.md`
- `DATA-SOURCES.md`
- `TASKS.md`

If any are missing, STOP. Report what is missing and instruct the user to run `/poc-kickoff <project>` first. Do not dispatch.

### Step 2: Lightweight Task Preview (main session)

Use **Grep** to extract only the target task's block from TASKS.md — do NOT Read the whole file into main context.

```
Grep(pattern="^### <task_id>", path="docs/<project>/<phase>/TASKS.md", output_mode="content", -A=20)
```

Confirm:
- The task exists and Status is not already `Done`.
- Its dependencies are `Done` — if not, warn the user and ask before proceeding.
- The task has a `**Demo Artifact**` field. If missing, STOP and ask the user to update TASKS.md first (CLAUDE.md requires it).

### Step 3: Dispatch data-pipeline

Spawn a single `data-pipeline` subagent with a self-contained prompt. The subagent reads project docs inside its own context — main session does NOT pre-load them.

```
Agent(
  subagent_type: "data-pipeline",
  description: "Implement <project> <task_id>",
  prompt: """
Implement <task_id> for the <project> project.

Read inside your own context (do not rely on main-session memory):
- docs/<project>/<phase>/TDD.md (read only if the task's Context field flags architectural relevance)
- docs/<project>/<phase>/DATA-SOURCES.md (read only if the task touches external APIs)
- docs/<project>/<phase>/TASKS.md — find <task_id> and follow Description, Acceptance Criteria, and Demo Artifact requirement

Constraints:
- Follow CLAUDE.md coding standards and Tool Usage Discipline.
- Do NOT modify PRD.md, TDD.md, or DATA-SOURCES.md. If you believe the design is wrong, STOP and flag it.
- Produce the Demo Artifact at the path listed in the task. Confirm it exists before reporting done.
- Update the task's Status to `Done (YYYY-MM-DD)` in TASKS.md when acceptance criteria pass.

Report back (≤200 words):
- Files created or modified (paths only, not content).
- Deviations from the task spec and why (if any).
- Confirmation the Demo Artifact exists at the expected path.
- Any BACKLOG.md items logged while working.
"""
)
```

### Step 4: Dispatch test-validator

After data-pipeline reports done, spawn `test-validator`:

```
Agent(
  subagent_type: "test-validator",
  description: "Validate <project> <task_id>",
  prompt: """
Validate <task_id> for the <project> project.

Read docs/<project>/<phase>/TASKS.md to find <task_id>'s acceptance criteria. Read the code data-pipeline just changed (paths: <files from data-pipeline report>). Write tests if missing. Run the full test suite. Produce a short validation report per docs/templates/VALIDATION-REPORT-TEMPLATE.md with PASS/FAIL verdict per acceptance criterion.

Do NOT fix issues — report them.
"""
)
```

### Step 5: Summarize to user (main session)

Combine the two subagent reports into one short summary (≤150 words):
- Task ID, title, status.
- Demo Artifact path.
- Test verdict (PASS / PASS WITH ISSUES / FAIL) with any blockers.
- Any BACKLOG.md items surfaced.
- Suggested next task from TASKS.md.

Do NOT start the next task. The user decides what comes next.

### Step 6: Commit & push

Per CLAUDE.md's Task Completion Checklist: stage the task's code files + the TASKS.md update (specific paths, not `git add -A`), commit with `feat(<project>): complete <task_id> <short-title>`, verify remote exists, push. Report SHA + GitHub URL on one line.

If the task is the final task in the current milestone, remind the user to run `/milestone-complete <project>` before starting the next milestone.

## Scope boundaries

- **Do not Read TDD.md, DATA-SOURCES.md, or the full TASKS.md in main session.** Only the Grep preview in Step 2. Doc reads happen inside the subagent.
- **Do not Write or Edit any code in main session.** The delegation-guard hook will block attempts on `projects/*/src/**` — that is intentional.
- **Do not trigger the milestone-complete gate from here.** Milestone approval is a separate explicit command.
