#!/bin/bash
# Verify "Built with Claude Code" line exists in all project READMEs before push
# Project hook — applies to the personal portfolio only

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')

MISSING=()

# Check all project READMEs that exist
for readme in "$CWD"/projects/*/README.md; do
  if [[ -f "$readme" ]]; then
    if ! grep -q 'Built with \[Claude Code\]' "$readme"; then
      MISSING+=("$readme")
    fi
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "BLOCKED: The following READMEs are missing the 'Built with Claude Code' line:" >&2
  for f in "${MISSING[@]}"; do
    echo "  - $f" >&2
  done
  echo "Add '> Built with [Claude Code](https://claude.ai/code)' below the project description before pushing." >&2
  exit 2
fi

exit 0
