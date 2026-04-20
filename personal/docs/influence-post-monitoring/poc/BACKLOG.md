# Backlog — Influence Post Monitoring

> **Purpose**: Track requirements discovered during implementation that were NOT in the original PRD.
> **Rule**: Items here are **not approved for implementation** until explicitly promoted to TASKS.md by the user.
> **Last Updated**: 2026-04-19

## Backlog Items

| ID | Requirement | Source | Date | Priority | Status |
|----|------------|--------|------|----------|--------|
| BL-001 | Fixture-driven pipeline runs so deliverables can be tested without real overnight signals | User review of milestone breakdown, 2026-04-18 | 2026-04-18 | High | Promoted → TASK-003, TASK-010, TASK-013 |
| BL-002 | PRD §6.16 and §6.18 still describe old conviction dots and disclaimer footer — §8 overrides 14–16 conflict with §6 governance precedence rule; §6 needs updating to match what was built | Architect review, Milestone 1 close, 2026-04-19 | 2026-04-19 | Medium | Open |
| BL-003 | Disclaimer footer (PRD §11 risk control) must be reinstated in §11 risk table when re-enabled before any non-personal-use distribution (MVP Beta / shared access) | Architect review, Milestone 1 close, 2026-04-19 | 2026-04-19 | High | Open |
| BL-004 | MVP reliability edge cases: account suspended mid-run; twikit rate-limit + retry; Claude API timeout; DB write fail mid-pipeline; partial signal batch; Twilio 429; message over 4,000 chars | BA alignment check, Milestone 2 close, 2026-04-19 | 2026-04-19 | Medium | Open (MVP) |

## Item Detail

### BL-001: Fixture-driven pipeline mode (`--use-fixtures`)
- **Source**: User review of milestone deliverables pre-implementation (2026-04-18)
- **Context**: Real signals may not appear overnight for days at a time. Without a way to inject synthetic signals, milestone deliverables (real WhatsApp messages with signal blocks) cannot be validated until organic signals happen. Each orchestrator needs a `--use-fixtures` flag that bypasses ingestion/scoring and seeds the DB with pre-built fixture signals, then runs from classification/rendering onward — producing a real WhatsApp on the user's phone with realistic content.
- **PRD Impact**: None — this is a developer/testing affordance, not a user-facing feature. No PRD change needed.
- **Effort Estimate**: Low — fixture JSON files + a `--use-fixtures` branch in the orchestrator CLI
- **Decision**: Promoted immediately per explicit user instruction ("please ensure that we are able to do it"). Changes made to TASK-003, TASK-010, TASK-013.

---

### BL-004: MVP reliability edge cases (deferred from PoC Milestone 2 review)
- **Source**: User note on Milestone 2 approval + BA alignment check (2026-04-19)
- **Context**: Seven operational failure modes identified during Milestone 2 review that test retry loops, partial-batch recovery, and delivery resilience. BA confirmed these belong in MVP hardening, not PoC. The PoC mitigation for these risks is architectural (SocialMediaSource swap interface, CallMeBot delivery fallback, zero-score sentinel) — not exhaustive test coverage.
- **Cases**:
  1. Account suspended mid-run → graceful skip, log warning, continue with remaining accounts
  2. twikit rate-limit hit → exponential back-off + retry (3 attempts)
  3. Claude API timeout → zero-score sentinel, log warning, continue
  4. DB write fails mid-pipeline → transaction rollback, log error, operational WhatsApp sent
  5. Partial signal batch (some accounts succeed, some fail) → ship available signals, note failures in `daily_summaries.error_message`
  6. Twilio 429 rate-limit → retry with back-off before falling back to operational message
  7. Rendered message exceeds 4,000 chars → split into multiple messages per existing renderer logic
- **PRD Impact**: MVP PRD §11 risk mitigations section; adds reliability acceptance criteria
- **Effort Estimate**: Medium — 7 test scenarios + retry/fallback logic in orchestrator and delivery layer
- **Decision**: Open — promote to MVP TASKS.md when MVP phase begins

---

## Promoted Items Log

| Backlog ID | Promoted To | Date | Notes |
|-----------|-------------|------|-------|
| BL-001 | TASK-003 (fixture files), TASK-010 (morning `--use-fixtures`), TASK-013 (evening `--use-fixtures`) | 2026-04-18 | No new task needed — integrated into existing tasks |
