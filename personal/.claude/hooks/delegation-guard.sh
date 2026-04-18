#!/bin/bash
# Block direct Write/Edit of agent-owned files from the main session.
# Allow calls from sidechains (subagents) since they are the correct owners.
#
# Project hook — applies to the personal portfolio only.
#
# Main-session-legit paths (NOT guarded): TASKS.md, BACKLOG.md,
# DISCOVERY-NOTES.md, demos/*, and anything outside of the guarded patterns.

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // empty')

# Only guard Write and Edit.
if [[ "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Edit" ]]; then
  exit 0
fi

OWNER=""
REASON=""

# --- Code & tests ---
if [[ "$FILE_PATH" =~ /projects/[^/]+/src/ ]]; then
  OWNER="data-pipeline"
  REASON="Implementation code under projects/*/src/**"
elif [[ "$FILE_PATH" =~ /projects/[^/]+/tests/ ]]; then
  OWNER="test-validator"
  REASON="Test code under projects/*/tests/**"

# --- Project README ---
elif [[ "$FILE_PATH" =~ /projects/[^/]+/README\.md$ ]]; then
  OWNER="content-writer"
  REASON="Project README.md is content-writer-owned"

# --- Gate docs — architect-owned ---
elif [[ "$FILE_PATH" =~ /docs/[^/]+/(poc|mvp|beta)/(PRD|TDD|DATA-SOURCES|MVP-GOALS|DEPLOYMENT|API-SPEC|PHASE-REVIEW)\.md$ ]]; then
  OWNER="architect"
  REASON="${BASH_REMATCH[2]}.md is architect-owned"

# --- Research outputs — agent-specific ---
elif [[ "$FILE_PATH" =~ /docs/[^/]+/(poc|mvp|beta)/MARKET-ANALYSIS\.md$ ]]; then
  OWNER="market-analyst"
  REASON="MARKET-ANALYSIS.md is market-analyst-owned"
elif [[ "$FILE_PATH" =~ /docs/[^/]+/(poc|mvp|beta)/RESEARCH-REPORT\.md$ ]]; then
  OWNER="research-analyst"
  REASON="RESEARCH-REPORT.md is research-analyst-owned"
elif [[ "$FILE_PATH" =~ /docs/[^/]+/(poc|mvp|beta)/UX-SPEC\.md$ ]]; then
  OWNER="ux-designer"
  REASON="UX-SPEC.md is ux-designer-owned"

# --- Strategic alignment log — business-analyst ---
elif [[ "$FILE_PATH" =~ /docs/[^/]+/(poc|mvp|beta)/ALIGNMENT-LOG\.md$ ]]; then
  OWNER="business-analyst"
  REASON="ALIGNMENT-LOG.md is business-analyst-owned"

# --- Claude Design briefs — ux-designer (.md only; prototype exports stay unguarded) ---
elif [[ "$FILE_PATH" =~ /docs/[^/]+/(poc|mvp|beta)/designs/.*\.md$ ]]; then
  OWNER="ux-designer"
  REASON="Claude Design briefs under designs/ are ux-designer-owned"

else
  # Path is not guarded — allow.
  exit 0
fi

# Allow if the most recent transcript entry is from a sidechain (subagent).
if [[ -n "$TRANSCRIPT" && -f "$TRANSCRIPT" ]]; then
  IS_SIDECHAIN=$(tail -n 1 "$TRANSCRIPT" 2>/dev/null | jq -r '.isSidechain // false' 2>/dev/null)
  if [[ "$IS_SIDECHAIN" == "true" ]]; then
    exit 0
  fi
fi

# Block with a helpful message.
cat >&2 <<EOF
BLOCKED: Direct $TOOL_NAME on $FILE_PATH from the main session is not allowed.

$REASON. Delegate to the $OWNER subagent:

  Agent(
    subagent_type: "$OWNER",
    description: "<short task description>",
    prompt: "<full task brief>"
  )

This enforces the Agent Delegation rule in CLAUDE.md. Main-session-legit exceptions (TASKS.md, BACKLOG.md, DISCOVERY-NOTES.md, demos/*) are not guarded.

If you genuinely need to bypass (e.g., repairing the hook itself), ask the user to temporarily disable the hook in .claude/settings.local.json.
EOF
exit 2
