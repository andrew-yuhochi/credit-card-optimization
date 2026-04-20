# Backlog — Influence Post Monitoring

> **Purpose**: Track requirements discovered during implementation that were NOT in the original PRD.
> **Rule**: Items here are **not approved for implementation** until explicitly promoted to TASKS.md by the user.
> **Last Updated**: 2026-04-20 (BL-007 added)

## Backlog Items

| ID | Requirement | Source | Date | Priority | Status |
|----|------------|--------|------|----------|--------|
| BL-001 | Fixture-driven pipeline runs so deliverables can be tested without real overnight signals | User review of milestone breakdown, 2026-04-18 | 2026-04-18 | High | Promoted → TASK-003, TASK-010, TASK-013 |
| BL-002 | PRD §6.16 and §6.18 still describe old conviction dots and disclaimer footer — §8 overrides 14–16 conflict with §6 governance precedence rule; §6 needs updating to match what was built | Architect review, Milestone 1 close, 2026-04-19 | 2026-04-19 | Medium | Open |
| BL-003 | Disclaimer footer (PRD §11 risk control) must be reinstated in §11 risk table when re-enabled before any non-personal-use distribution (MVP Beta / shared access) | Architect review, Milestone 1 close, 2026-04-19 | 2026-04-19 | High | Open |
| BL-004 | MVP reliability edge cases: account suspended mid-run; twikit rate-limit + retry; Claude API timeout; DB write fail mid-pipeline; partial signal batch; Twilio 429; message over 4,000 chars | BA alignment check, Milestone 2 close, 2026-04-19 | 2026-04-19 | Medium | Open (MVP) |
| BL-005 | `--date YYYY-MM-DD` CLI flag for pipeline morning/evening to override the calendar date — enables reproducible dry-run demos and debugging on non-trading days | test-validator review TASK-013, 2026-04-19 | 2026-04-19 | Low | Open (MVP) |
| BL-006 | Upgrade GitHub Actions to Node.js 24-compatible versions — `actions/checkout@v4` and `actions/setup-python@v5` use deprecated Node.js 20; upgrade to v5/v6 before June 2, 2026 deadline. Affects `morning_alert.yml`, `evening_summary.yml`, `market_hours_poll.yml`. | GitHub Actions deprecation warning, 2026-04-20 | 2026-04-20 | Low | Open |
| BL-007 | Wire engagement velocity (intraday snapshots) into outcome scoring — `market_hours_poll` already collects `engagement_snapshots` every 2h; in MVP connect to amplifier scorer so evening summary weights signals by intraday velocity (e.g. 300% engagement gain by noon → higher confidence). Poll runs in PoC but output is not consumed by the evening pipeline. | User decision, 2026-04-20 | 2026-04-20 | Medium | Open (MVP) |

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

### BL-007: Wire engagement velocity (intraday snapshots) into outcome scoring
- **Source**: User decision — deferred from PoC to MVP (2026-04-20)
- **Context**: The `market_hours_poll` workflow already collects `engagement_snapshots` (likes, reposts, views) every 2h during market hours. In PoC, this data is gathered but not consumed by the evening pipeline. In MVP, connect it to the amplifier scorer so the evening summary can weight signals by intraday engagement velocity — e.g. a post that gained 300% engagement by noon is flagged as higher confidence. Not in scope for PoC validation.
- **PRD Impact**: MVP PRD — new scoring input to amplifier scorer; `engagement_snapshots` table already exists
- **Effort Estimate**: Medium — velocity calculation logic + amplifier scorer integration + evening pipeline wiring
- **Decision**: Open — promote to MVP TASKS.md when MVP phase begins

---

### BL-006: Upgrade GitHub Actions to Node.js 24-compatible versions
- **Source**: GitHub Actions deprecation warning observed during CI run (2026-04-20)
- **Context**: `actions/checkout@v4` and `actions/setup-python@v5` in all three workflow files (`.github/workflows/morning_alert.yml`, `evening_summary.yml`, `market_hours_poll.yml`) use Node.js 20, which is deprecated. GitHub will force Node.js 24 by default starting June 2, 2026. Upgrade to `actions/checkout@v5` and `actions/setup-python@v6` before that deadline.
- **PRD Impact**: None — CI infrastructure only, no user-facing behavior change.
- **Effort Estimate**: Trivial — version bump in three YAML files
- **Deadline**: June 2, 2026
- **Decision**: Open — promote to TASKS.md before June 2, 2026

---

## Promoted Items Log

| Backlog ID | Promoted To | Date | Notes |
|-----------|-------------|------|-------|
| BL-001 | TASK-003 (fixture files), TASK-010 (morning `--use-fixtures`), TASK-013 (evening `--use-fixtures`) | 2026-04-18 | No new task needed — integrated into existing tasks |
