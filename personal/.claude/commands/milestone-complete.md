# Milestone Complete — $ARGUMENTS

Enforce the user-approval gate at the end of a milestone. CLAUDE.md mandates that the next milestone cannot begin until the user has reviewed and approved the current milestone's deliverable. This command is the structural enforcement of that rule.

Run this when you believe every task in the current milestone is Done.

## Instructions

The user provides a project name as the argument (e.g., `paper-monitoring`). If no argument is given, infer from the most recently touched project under `docs/`.

### Step 1: Identify the Milestone

- Read `docs/$ARGUMENTS/<current-phase>/TASKS.md`.
- Locate the current milestone — the lowest-numbered milestone whose Status is not `Done`.
- If that milestone has any task whose Status is not `Done`, list the non-Done tasks and **STOP**. The milestone is not complete yet; do not proceed to Step 2.

### Step 2: Verify Demo Artifacts

For every task in the milestone:
- Confirm the task has a `- **Demo Artifact**:` line.
- Confirm the referenced artifact file exists (Read it) or the URL is reachable.
- If any artifact is missing or unreachable, list the gaps and **STOP**. Do not proceed to Step 3. Direct the user to either collect the missing artifacts, or explicitly annotate the task with `Demo Artifact: none — <reason>` if the task genuinely has no user-visible effect (rare; should have been caught at milestone-plan time).

### Step 3: Produce the Milestone Review

Draft the review in this form:

```
## Milestone N Review — <project>

**Milestone**: <name>
**Goal**: <from TASKS.md>
**Tasks completed**: <count>
**Demo Gallery**: docs/<project>/<phase>/demos/milestone-N/

### What shipped
- TASK-00X: <title> — <one-sentence outcome>
- ...

### Demo artifacts
- TASK-00X: [artifact path or URL]
- ...

### Acceptance criteria check
- [x] <criterion 1> — <evidence>
- [x] <criterion 2> — <evidence>

### Deviations from plan
- <anything built differently from the original plan, scope changes, discovered issues>
- <if nothing notable, write "None">

### Backlog items surfaced during this milestone
- <links to BACKLOG.md entries added during the milestone, or "None">
```

### Step 4: Pause for User Approval — MANDATORY

Present the milestone review to the user and **STOP**. Do not proceed to Step 5, do not start the next milestone, do not edit any other files until the user replies.

Ask the user exactly this:

> Milestone **N** is complete. Review the summary and demo artifacts above. Please reply with one of:
> - **approve** — I will record approval in TASKS.md and unlock Milestone N+1.
> - **approve with notes** — I will capture your notes in the Completed Milestones Log before proceeding.
> - **revise** — tell me what is incomplete or unsatisfactory; I will reopen the relevant tasks and we will iterate before re-running this command.

### Step 5: Record the Outcome

After the user replies:

**If approved or approved-with-notes:**
- Move the milestone block under `## Completed Milestones Log` in TASKS.md with today's date and the review outcome.
- If "approve with notes," record the user's notes verbatim in the log entry.
- Update the Progress Summary table counts.
- Leave the next milestone's Status as `To Do` — do not auto-start it.

**If revise:**
- Reopen the flagged tasks and reset their Status to `In Progress` or `To Do`.
- Do NOT move the milestone to the Completed Milestones Log.
- Summarize what will be addressed, then stop. Wait for the user to drive the next step (implementation or re-planning).

### Step 6: Commit

Commit the TASKS.md update with a Conventional Commits message scoped to the project and milestone, e.g.:

```
docs(<project>): close Milestone <N> — <approved | approved with notes | revise>
```

Push per the Task Completion Checklist in CLAUDE.md. Report the commit SHA and GitHub URL back to the user in one line.

## Scope boundaries

- **Do not start the next milestone.** Starting the next milestone requires the user to run `/milestone-plan` (to confirm scope) and then `/implement` as a separate step. This command only closes the current milestone.
- **Do not ask an agent to "approve" on the user's behalf.** Only the user can approve milestones. The architect reviews design quality; it does not substitute for user sign-off.
- **Do not edit code.** This command only reads TASKS.md, verifies artifacts, produces the review, and updates TASKS.md after user approval.
- **Do not skip Step 4.** If you find yourself drafting the review and moving straight to Step 5 without waiting for a user reply, stop — that defeats the entire purpose of this command.
