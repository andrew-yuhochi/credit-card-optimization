# Per-Project Directory Layout

## Code Structure
Each project lives under `projects/<project-name>/` with this structure:

```
projects/<project-name>/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration and env vars (Pydantic BaseSettings)
│   ├── models/            # Pydantic data models / data contracts
│   ├── services/          # Business logic
│   ├── integrations/      # External API clients
│   └── utils/             # Shared utilities
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── data/                  # Local data (gitignored)
├── notebooks/             # Exploration notebooks
├── requirements.txt       # Exact pinned versions
├── .env.example           # Template for environment variables (committed)
└── README.md
```

## Documentation Structure
Documentation lives in `docs/<project-name>/` with phase subfolders:

```
docs/<project-name>/
├── poc/                   # PoC phase — frozen after phase completion
│   ├── DISCOVERY-NOTES.md
│   ├── PRD.md
│   ├── TDD.md
│   ├── DATA-SOURCES.md
│   ├── TASKS.md
│   ├── BACKLOG.md
│   ├── ALIGNMENT-LOG.md   # business-analyst verdicts log
│   ├── MARKET-ANALYSIS.md
│   ├── RESEARCH-REPORT.md
│   ├── UX-SPEC.md
│   ├── designs/           # Claude Design briefs + exported prototypes (PoC: one surface only)
│   │   ├── <surface>-brief.md
│   │   └── <surface>-prototype.{url,pdf,png}
│   ├── demos/             # Demo artifacts per task (screenshots, CLI recordings, sample outputs)
│   └── PHASE-REVIEW.md
├── mvp/                   # MVP phase — evolved from PoC docs
│   ├── MVP-GOALS.md
│   ├── PRD.md             # Evolved from poc/PRD.md
│   ├── TDD.md             # Evolved from poc/TDD.md
│   ├── DATA-SOURCES.md    # Evolved from poc/DATA-SOURCES.md
│   ├── TASKS.md           # New milestones for MVP
│   ├── BACKLOG.md         # Carried forward from poc/
│   └── PHASE-REVIEW.md
└── beta/                  # Beta phase — evolved from MVP docs
    ├── PRD.md
    ├── TDD.md
    ├── DATA-SOURCES.md
    ├── TASKS.md
    ├── BACKLOG.md
    ├── MARKET-ANALYSIS.md  # Re-done for commercial validation
    ├── DEPLOYMENT.md
    ├── API-SPEC.md
    └── PHASE-REVIEW.md
```

### Phase Document Rules
- **PoC phase**: All documents created fresh during kickoff
- **MVP/Beta phases**: PRD, TDD, DATA-SOURCES, and BACKLOG are copied from the previous phase folder, then evolved. The originals stay frozen as historical record.
- **TASKS.md**: Created fresh each phase with new milestones (previous phase's tasks are already frozen)
- **PHASE-REVIEW.md**: Created at the end of each phase by the architect
