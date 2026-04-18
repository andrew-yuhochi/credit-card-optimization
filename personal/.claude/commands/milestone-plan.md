# Milestone Plan — $ARGUMENTS

Analyze current progress on a project and plan the next milestone of work.

## Instructions

The user will provide a project name as the argument (e.g., `paper-monitoring`).

### Step 1: Assess Current State
- Read `docs/$ARGUMENTS/<current-phase>/TASKS.md`
- Count tasks by status: Done, In Progress, To Do, Blocked
- Identify any blocked tasks and their blockers
- Check which milestone we're currently in

### Step 2: Review Completed Work
- List tasks completed since the last milestone plan
- Note any tasks that took longer than expected or deviated from the plan
- Check if any completed tasks revealed new requirements or risks

### Step 3: Review Outstanding Work
- List all remaining To Do tasks
- Check dependency chains — which tasks are unblocked and ready?
- Identify any tasks that should be re-estimated based on what we've learned

### Step 4: Propose Next Milestone
Present a proposed milestone plan:

```
## Milestone [N]: [Deliverable Name] — $ARGUMENTS
**Goal**: [What the user can test when this milestone is complete]
**Acceptance Criteria**: [How the user validates the deliverable]
**Review Checkpoint**: User reviews and approves before next milestone begins

### Tasks for This Milestone
1. **TASK-XXX**: [Title] — Complexity: [X] — Agent: [agent(s)] — Ready: Yes/No
2. **TASK-XXX**: [Title] — Complexity: [X] — Agent: [agent(s)] — Ready: Yes/No
3. **TASK-XXX**: [Title] — Complexity: [X] — Agent: [agent(s)] — Ready: Yes/No

### Dependencies to Resolve First
- [Any blockers that need attention]

### Risks
- [Anything that might slow this milestone down]
```

Ask the user: **"Does this milestone plan work for you? Want to adjust the scope or priorities?"**

### Step 5: Update TASKS.md
After user approval, update `docs/$ARGUMENTS/<current-phase>/TASKS.md` with the new milestone section and any re-prioritized tasks.

Every task entry **must** include an `- **Agent**:` field immediately after `- **Status**:`. Use the agent delegation guidelines from CLAUDE.md to assign:
- `data-pipeline (impl)` — for any ingestion, transformation, or processing code
- `devops-engineer (infra)` — for scheduling, deployment, automation, monitoring (MVP onward)
- `test-validator (QA)` — always paired with implementation tasks; also primary for pure test tasks
- `architect (phase-transition review)` — add for the first task of a new milestone when it represents a phase boundary
- `content-writer (docs)` — for README files, documentation updates, or user-facing written content
- `none — manual user process` — for process/validation tasks with no code delegation

Every task entry **must** also include a `- **Demo Artifact**:` field describing what a non-developer can look at to judge the task (screenshot, CLI recording, sample output file, URL). If you cannot name a Demo Artifact for a task, the task is pure infrastructure and violates CLAUDE.md's milestone rule — bundle it into a neighboring user-visible task instead. See `docs/templates/TASKS-TEMPLATE.md` for the format.

The milestone block itself **must** include:
- `**Demo Gallery**: docs/<project>/<phase>/demos/milestone-N/`
- `**Review Checkpoint**: User reviews and approves before Milestone N+1 begins (run /milestone-complete <project> to trigger the approval gate)`
