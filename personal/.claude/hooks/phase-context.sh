#!/bin/bash
# Re-inject phase context after context compaction
# Project hook — reminds Claude of key workflow conventions

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')

# Build context reminder
cat <<'EOF'
Post-compaction reminder:
- Projects follow a three-phase lifecycle (PoC → MVP → Beta). Check PRD.md for current phase.
- Tasks use milestones with user review checkpoints. Check TASKS.md for current progress.
- New requirements must be logged to BACKLOG.md before implementation (Backlog Capture Rule).
- Follow CLAUDE.md for all coding standards, security rules, and workflow conventions.
EOF

exit 0
