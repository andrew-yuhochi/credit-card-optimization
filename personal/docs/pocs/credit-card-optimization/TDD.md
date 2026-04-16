# Technical Design Document — Credit Card Optimization

> **Status**: Approved
> **Author**: architect
> **Last Updated**: 2026-04-15
> **Depends on**: PRD.md (approved)

---

## 1. Architecture Overview

The system is a single-server FastAPI application with four logical layers:

1. **Data layer** — a static JSON card database (hand-curated, version-controlled) backed by SQLite for session state and any persisted user data.
2. **Optimization layer** — a MILP solver (PuLP + CBC) that takes a structured spending profile and produces an optimal card assignment.
3. **Web layer** — FastAPI with Jinja2 server-rendered templates for the two-page UI (Input Page, Results Page).
4. **Export layer** — openpyxl generates a four-tab `.xlsx` download on demand.

There is no React frontend, no message queue, no background worker, and no external API calls at runtime. The only runtime I/O is: user HTTP request → FastAPI handler → MILP solve → Jinja2 render → HTTP response. This is intentional — the tool is used semi-annually and correctness matters more than throughput.

```
User Browser
    │  HTTP (form POST)
    ▼
FastAPI Application
    ├── Input validation (Pydantic)
    ├── Card database loader (JSON → CardRecord models)
    ├── Eligibility pre-filter
    ├── MILP Solver (PuLP + CBC)
    ├── Result models (Pydantic)
    ├── Jinja2 template renderer
    └── openpyxl export generator
         │
         ▼
      SQLite (session state + tenant records)
```

**Multi-tenant from day one.** Every database table carries `user_id` and `household_id` columns. The PoC ships with one tenant (the builder). The schema supports N tenants without migration.

---

## 2. Component Design

### 2.1 Data Ingestion Layer

**Card Database (static JSON)**

The canonical source of truth for all card data is `data/cards/cards.json` — a hand-curated, version-controlled file. It is loaded once at application startup and cached in memory. No runtime scraping occurs.

Schema for a single card record:

```json
{
  "id": "cibc_dividend_vi",
  "name": "CIBC Dividend Visa Infinite",
  "issuer": "CIBC",
  "network": "Visa",
  "annual_fee": 120.0,
  "first_year_fee": 0.0,
  "requires_amex": false,
  "approval": {
    "min_credit_score": 725,
    "min_personal_income": 60000,
    "min_household_income": 100000,
    "source": "community",
    "confidence": "medium"
  },
  "category_rates": {
    "grocery": 4.0,
    "gas": 4.0,
    "dining": 2.0,
    "transit": 2.0,
    "recurring": 2.0,
    "other": 1.0
  },
  "category_caps_monthly": {
    "grocery": 80.0,
    "gas": 80.0
  },
  "store_overrides": {
    "shoppers_drug_mart": {"rate": 4.0, "source": "issuer", "note": "SDM coded as grocery on CIBC Dividend"},
    "walmart": {"rate": 1.0, "source": "community", "note": "Walmart coded as general merchandise on Visa networks"},
    "costco": {"rate": 1.0, "source": "issuer", "note": "Costco coded as wholesale; earns base rate"}
  },
  "store_acceptance": {
    "costco_instore": false,
    "costco_online": true
  },
  "point_system": "cashback",
  "cpp_default": 1.0,
  "last_verified_date": "2026-04-15",
  "source_url": "https://www.cibc.com/en/personal-banking/credit-cards/...",
  "override_notes": ""
}
```

**Store MCC Map (static JSON)**

`data/stores/store_mcc_map.json` maps canonical store slugs to MCC and default category:

```json
{
  "costco": {"mcc": "5300", "default_category": "wholesale", "note": "Wholesale Club — NOT grocery on most networks"},
  "walmart": {"mcc": "5310", "default_category": "other", "note": "Discount Store"},
  "shoppers_drug_mart": {"mcc": "5912", "default_category": "pharmacy", "note": "Varies by issuer — see card-level overrides"}
}
```

**MCC Reference (static JSON)**

`data/stores/mcc_codes.json` is sourced from `greggles/mcc-codes` (public domain, 981 entries). Used for: displaying MCC descriptions in the UI, and as a lookup when classifying user-entered custom stores.

**CPP Configuration**

`config/valuation.json` holds cents-per-point defaults. These are user-overridable in a future phase; at PoC they are read-only config:

```json
{
  "cashback": 1.0,
  "amex_mr": 2.0,
  "aeroplan": 2.1,
  "scene_plus": 1.0,
  "td_rewards": 0.5,
  "bmo_rewards": 0.71,
  "rbc_avion": 1.5
}
```

**Data Loading**

A `CardDatabaseLoader` class (registry pattern) loads and validates the JSON at startup. It is the single point of card data access for the rest of the application.

```python
class CardDatabaseLoader:
    def load(self, path: Path) -> list[CardRecord]: ...
    def get_all(self) -> list[CardRecord]: ...
    def get_by_id(self, card_id: str) -> CardRecord | None: ...
    def get_store_mcc_map(self) -> dict[str, StoreMccEntry]: ...
```

All card data flows through Pydantic models — no raw dict access outside the loader.

### 2.2 Processing and Transformation Layer

**Eligibility Pre-Filter**

Before the MILP is constructed, ineligible cards are removed from the candidate pool. This is critical for performance: it reduces the active card count from 100+ to ~40–50, cutting solve time from ~10s to ~2s.

Filter rules (applied in order):
1. If Amex toggle is off: remove all cards where `requires_amex = true`.
2. For each person: remove cards where `approval.min_credit_score > person.credit_score_band_max`.
3. For each person: remove cards where `approval.min_personal_income > person.income_band_max`.
4. If couple mode is active: retain cards where either person qualifies individually, or where combined household income meets `min_household_income`.
5. For each spend bucket that is a specific store: remove cards where `store_acceptance[store] = false`.

This filter is implemented as `EligibilityFilter.filter(cards, profile) -> list[CardRecord]`.

**Spend Bucket Normalization**

The user's input (category rows + store rows) is normalized into a flat list of spend buckets. Each bucket has:
- `bucket_id`: string key (e.g., `"grocery"`, `"costco"`, `"custom_store_1"`)
- `monthly_amount`: float (CAD)
- `resolved_category`: the canonical category key (e.g., `"grocery"`, `"other"`, `"wholesale"`)
- `store_slug`: optional store slug (for store buckets — enables per-card override lookup)
- `acceptance_constraints`: set of card IDs that are excluded at this store

For Chexy rent: the rent amount is added as a special bucket `"chexy_rent"` with `resolved_category = "other"`. The optimizer applies a Chexy adjustment: the effective rate for each card on this bucket = `card_other_rate - 0.0175`. Cards with `card_other_rate <= 0.0175` earn a negative effective rate; the optimizer will route this bucket to cash (effectively $0 reward) or to the card with the least negative rate. A note is surfaced in the results.

**Dummy Card Integration**

Dummy cards defined by the user are converted to `CardRecord` objects by `DummyCardBuilder`. They receive a generated `id` (e.g., `"dummy_0"`), `requires_amex = false`, `approval` thresholds of zero (always eligible), and an empty `store_overrides` table. They are merged into the candidate pool before the eligibility filter runs (eligibility filter always passes them through).

### 2.3 Analytical / Business Logic Layer

**MILP Formulation**

The optimizer is a Mixed-Integer Linear Program (MILP) implemented with PuLP 3.3.0 + CBC solver.

Decision variables:
- `y[c, p]` ∈ {0, 1}: card `c` is selected for person `p`'s wallet
- `x[c, p, k]` ≥ 0: monthly dollars spent on card `c` by person `p` in spend bucket `k`

Objective (maximize monthly net reward in CAD):
```
max  Σ(c,p,k)  x[c,p,k] × effective_rate[c,k] × cpp[c]
     − Σ(c,p)  y[c,p] × annual_fee[c] / 12
```

Where `effective_rate[c,k]` is resolved as:
1. If bucket `k` is a store with an override for card `c`: use `store_overrides[k][c].rate / 100`
2. Else: use `category_rates[c][resolved_category[k]] / 100`
3. For Chexy bucket: use `max(0, category_rates[c]["other"] / 100 - 0.0175)` (clamped to zero; negative rates are not meaningful)

Constraints:
1. **Coverage**: `Σ_c x[c, p, k] = spend[p, k]` for all p, k (all spending must be allocated)
2. **Card selection linking**: `x[c, p, k] ≤ spend[p, k] × y[c, p]` for all c, p, k (can only spend on a card if it's in the wallet)
3. **Monthly cap**: `Σ_k_in_cap_group x[c, p, k] ≤ cap_amount[c, cap_group]` for each (c, cap_group) pair (reward cap enforced on monthly spend, not reward dollars)
4. **Store acceptance**: `x[c, p, k] = 0` if card `c` is excluded at store `k`
5. **Eligibility**: `y[c, p] = 0` if card `c` failed the eligibility pre-filter for person `p`

Note on single vs. couple mode: In single mode, `p` takes a single value `{0}`. Spending buckets are assigned entirely to person 0. In couple mode, `p ∈ {0, 1}` and `spend[p, k] = household_spend[k]` — i.e., each person can potentially earn on the full household spend at each bucket (the optimizer decides who uses which card at which store). This correctly models the case where one person's card is used for household grocery shopping.

**Delta Calculator (Feature 2)**

The optimizer is called twice:
1. **Constrained solve**: `y[c, p] = 0` for all cards `c` not in the user's current card set. This gives `current_annual_reward`.
2. **Unconstrained solve**: Full eligible pool, no forced exclusions. This gives `optimal_annual_reward`.
3. `delta = optimal_annual_reward - current_annual_reward`

Both solve results are returned together in a `DeltaResult` model. The results page renders both side-by-side with the delta figure prominently displayed.

**"Why This Card?" Explanation Generator**

After the MILP solve, for each (bucket, card, person) assignment, an explanation string is generated by `ExplanationGenerator.explain(assignment, card, bucket, cards_considered)`. The generator produces a one-sentence English explanation following a template:

- Store override: "CARD earns RATE% at STORE — it is classified as CATEGORY by ISSUER and this is the highest rate among eligible cards."
- Category rate: "CARD earns RATE% on CATEGORY spending; no eligible card earns more in this category."
- Cap-constrained split: "CARD earns RATE% on CATEGORY up to the monthly cap of $CAP; the remaining $AMOUNT is routed to CARD2 at RATE2%."
- Chexy: "CARD earns RATE% on all purchases (other category); after Chexy's 1.75% fee, the net return on rent is NET_RATE%."

Explanations are part of the `AssignmentRow` model and rendered in the Jinja2 template via the expandable row pattern.

### 2.4 Storage Layer

**SQLite (session state + tenant scaffolding)**

SQLAlchemy with SQLite is used for session state and the multi-tenant scaffold. All tables include `user_id` and `household_id` columns. The PoC operates with a single implicit tenant (the builder). No UI for tenant management is built.

Table: `optimization_sessions`

```sql
CREATE TABLE optimization_sessions (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL DEFAULT 'default',
    household_id TEXT NOT NULL DEFAULT 'default',
    created_at  DATETIME NOT NULL,
    expires_at  DATETIME NOT NULL,
    input_json  TEXT NOT NULL,   -- serialized SpendingProfile (Pydantic model)
    result_json TEXT             -- serialized OptimizationResult (nullable until solve completes)
);
```

Session IDs are UUIDs stored in a browser cookie (HttpOnly, SameSite=Lax). Sessions expire after 24 hours. There is no auth — the session cookie is the only identity mechanism in the PoC.

Table: `households`

```sql
CREATE TABLE households (
    id           TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL DEFAULT 'default',
    household_id TEXT NOT NULL DEFAULT 'default',
    created_at   DATETIME NOT NULL
);
```

Migrations are managed with a simple `migrations/` directory containing numbered SQL files executed at startup if not already applied. No Alembic dependency for PoC.

**JSON Card Database (static, version-controlled)**

`data/cards/cards.json` is the source of truth. It is not stored in SQLite — it lives in the repo and is loaded at startup. This makes card data changes a code review process, which is intentional for a PoC where data accuracy matters.

### 2.5 Presentation Layer

**FastAPI Application Structure**

```
projects/credit-card-optimization/
├── app/
│   ├── main.py                # FastAPI app creation, router registration, startup hooks
│   ├── routers/
│   │   ├── input.py           # GET / (input page), POST /optimize (run optimizer)
│   │   ├── results.py         # GET /results/{session_id}
│   │   └── export.py          # GET /export/{session_id}
│   ├── models/
│   │   ├── card.py            # CardRecord, ApprovalRequirements, StoreOverride, etc.
│   │   ├── spending.py        # SpendingProfile, SpendBucket, PersonProfile, DummyCard
│   │   ├── optimization.py    # OptimizationResult, AssignmentRow, CardSummaryRow, DeltaResult
│   │   └── session.py         # OptimizationSession
│   ├── services/
│   │   ├── card_loader.py     # CardDatabaseLoader (registry pattern)
│   │   ├── eligibility.py     # EligibilityFilter
│   │   ├── spend_normalizer.py # SpendBucketNormalizer, DummyCardBuilder
│   │   ├── optimizer.py       # MILPOptimizer (PuLP + CBC)
│   │   ├── delta.py           # DeltaCalculator (calls optimizer twice)
│   │   ├── explainer.py       # ExplanationGenerator
│   │   └── exporter.py        # SpreadsheetExporter (openpyxl)
│   ├── templates/
│   │   ├── base.html
│   │   ├── input.html
│   │   ├── results.html
│   │   └── error.html
│   └── static/
│       ├── styles.css
│       └── input.js           # Minimal JS: accordion collapse, form validation
├── data/
│   ├── cards/
│   │   └── cards.json
│   └── stores/
│       ├── store_mcc_map.json
│       └── mcc_codes.json
├── config/
│   └── valuation.json
├── migrations/
│   └── 001_initial_schema.sql
├── scripts/
│   └── seed_cards.py          # One-time Playwright scraping helper (not runtime)
├── tests/
│   ├── test_card_loader.py
│   ├── test_eligibility.py
│   ├── test_optimizer.py
│   ├── test_delta.py
│   ├── test_explainer.py
│   ├── test_exporter.py
│   └── test_routes.py
├── requirements.txt
├── .env.example
└── README.md
```

**Request Lifecycle**

1. `GET /` — renders `input.html` with a blank form (or pre-populated from session cookie if returning user).
2. User submits form: `POST /optimize` — validates input (Pydantic), runs eligibility filter, runs MILP solver, runs delta solver (if current cards provided), stores result in SQLite session, redirects to `GET /results/{session_id}`.
3. `GET /results/{session_id}` — loads session from SQLite, renders `results.html` with `OptimizationResult` and `DeltaResult`.
4. `GET /export/{session_id}` — loads session from SQLite, calls `SpreadsheetExporter`, streams `.xlsx` file as download.
5. `GET /?session={session_id}` — loads session input, pre-populates form for the "Adjust inputs" round trip.

**Jinja2 Templates**

Templates receive typed context objects (Pydantic models serialized to dicts). No business logic lives in templates — templates render only. The "Why this card?" expansion uses a `<details>/<summary>` HTML element (no JavaScript required for the basic collapse; progressive enhancement with HTMX or vanilla JS for smoother UX).

**Input Page UX Decisions (resolving open questions from UX-SPEC.md)**

1. **Session persistence**: Server-side session (SQLite + cookie) is used instead of localStorage. Rationale: localStorage is tab-specific and survives browser restart; server-side session is domain-specific and survives tab close/reopen within 24 hours. No privacy concern (no PII stored — only spending amounts). This matches the "adjust inputs" round-trip requirement cleanly without client-side state management complexity.

2. **Couple mode spending split**: Combined household spending is entered once. The optimizer assigns cardholder (Person 1 or Person 2) per spend bucket. The results table shows a "Cardholder" column in couple mode. The user does not split spending per person on input — this is both simpler to enter and correct for the optimization (the optimizer finds the globally optimal person-card-bucket assignment).

3. **Chexy fee handling**: The tool knows the 1.75% Chexy fee and applies it automatically. When the Chexy toggle is enabled, the rent amount is treated as a special spend bucket with effective rate = `(card_other_rate - 0.0175)`. The UI displays the net effective rate in the Assignment table for the rent/Chexy row. No user fee override field is provided — the 1.75% is a published Chexy rate, not user-configurable.

4. **Store-specific loyalty cards**: Canadian Tire Triangle, PC Financial, and similar store-specific cards are regular `CardRecord` entries in the card database. They compete in the optimizer like any other card. There is no stacking model (no "also use your PC Optimum card on top of"). Users who want to model stacking can add a dummy card representing their combined net rate.

5. **Baseline comparison rate**: 2% flat cash-back. Rationale: Rogers Red Mastercard earns 1.5% everywhere; no mainstream no-annual-fee Canadian card reliably exceeds 2% on all purchases. The 2% benchmark represents the Canadian ceiling for a simple no-effort strategy and creates a meaningful, achievable bar for the optimizer to beat.

6. **Export format**: Four-tab `.xlsx`. The multi-tab structure is essential for the Calculation Detail and Input Echo use cases. CSV is not offered — a single-sheet CSV cannot represent the four-tab structure.

---

## 3. Technology Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Language | Python | 3.11+ | Portfolio standard; type hint support |
| Web framework | FastAPI | 0.115.x | Portfolio standard; async-capable, Pydantic-native |
| Template engine | Jinja2 | 3.1.6 | Server-side rendering; no React needed for a two-page form tool |
| Database | SQLite + SQLAlchemy | SQLAlchemy 2.x | PoC simplicity; no Postgres server to manage; schema is multi-tenant-ready |
| Optimization solver | PuLP + CBC | PuLP 3.3.0 | MIT license; benchmarked at full scale (10s worst case, ~2s with pre-filter); algebraic API is maintainable |
| Spreadsheet export | openpyxl | 3.1.5 | Installed; multi-sheet .xlsx; MIT license |
| Data validation | Pydantic | 2.x | Portfolio standard; used for all model definitions |
| Web scraping (one-time) | Playwright | latest | For initial card data seeding from CreditCardGenius + PrinceOfTravel; not a runtime dependency |
| Testing | pytest | 7.x | Portfolio standard; 80% coverage target on core logic |
| Logging | Python logging | stdlib | Portfolio standard; no print() |
| Path handling | pathlib.Path | stdlib | Portfolio standard; no string paths |

**Trade-offs noted:**
- PuLP + CBC vs. scipy.optimize.milp: PuLP's algebraic API is significantly more readable and maintainable for a formulation this complex. scipy.milp requires manual coefficient matrix construction. No performance advantage for this problem type.
- Server-side session vs. localStorage: Server-side is slightly more infrastructure but avoids browser-specific state management quirks and works correctly across tabs.
- Jinja2 vs. React: For a two-page form with no real-time interactivity, React would be over-engineered. Jinja2 renders correctly and is deployable on any WSGI/ASGI host.

---

## 4. Data Flow Diagram

```
[User Browser]
     │
     │  1. GET / (input page)
     ▼
[FastAPI: input.py GET /]
     │
     │  Loads session (if cookie present) → pre-populates form
     ▼
[Jinja2: input.html] → [User fills form] → POST /optimize
     │
     ▼
[FastAPI: input.py POST /optimize]
     │
     ├── Pydantic validation → SpendingProfile
     │
     ├── CardDatabaseLoader.get_all() → list[CardRecord]
     │        └── loads from data/cards/cards.json (cached at startup)
     │
     ├── EligibilityFilter.filter(cards, profile) → eligible_cards
     │
     ├── SpendBucketNormalizer.normalize(profile) → list[SpendBucket]
     │
     ├── MILPOptimizer.solve(eligible_cards, buckets, profile)
     │        └── PuLP + CBC → OptimizationResult
     │
     ├── DeltaCalculator.solve(eligible_cards, buckets, profile)  [if current_cards provided]
     │        ├── Constrained solve → current_result
     │        └── Unconstrained solve (same as above) → optimal_result
     │        └── DeltaResult
     │
     ├── ExplanationGenerator.generate(result, cards) → annotated AssignmentRows
     │
     ├── OptimizationSession.save(db, session_id, input, result)
     │
     └── Redirect → GET /results/{session_id}
     │
     ▼
[FastAPI: results.py GET /results/{session_id}]
     │
     ├── OptimizationSession.load(db, session_id) → result
     ▼
[Jinja2: results.html] → [User reads results]
     │
     │  Optional: GET /export/{session_id}
     ▼
[FastAPI: export.py GET /export/{session_id}]
     │
     ├── SpreadsheetExporter.generate(result) → BytesIO
     └── StreamingResponse (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
```

---

## 5. Security Considerations

- **No API keys or secrets at runtime**: The tool has no external API calls. There are no secrets to leak in `.env`.
- **Session cookie**: HttpOnly, SameSite=Lax, Secure (in production). Session ID is a UUID4 — not guessable.
- **Input validation**: All user inputs are validated by Pydantic before touching the optimizer. Monthly spend amounts are clamped to positive floats. Category names are validated against an allowlist. Custom store names are sanitized (alphanumeric + spaces + common punctuation only).
- **No PII stored**: Session data contains spending amounts and settings — no names, addresses, or financial account numbers. SQLite session table is ephemeral (24-hour expiry, purged at startup for expired rows).
- **MILP resource limits**: The PuLP solver is given a time limit of 30 seconds (`timeLimit=30`). If CBC does not find an optimal solution within 30 seconds, the best feasible solution found is returned with a warning shown in the UI.
- **File download safety**: The `.xlsx` export is generated server-side from trusted internal data only (the session result, which was already validated). No user-supplied content is written into the spreadsheet without sanitization.
- **Dependency pinning**: All dependencies in `requirements.txt` are pinned to exact versions to prevent supply-chain drift.
- **`.env.example`**: Checked into git with placeholder values. `.env` is gitignored.

---

## 6. Error Handling Strategy

| Failure Mode | Detection | Response |
|---|---|---|
| All spending inputs are $0 | Pydantic validator on `SpendingProfile` | HTTP 422; form-level error message rendered in `input.html` |
| MILP solver finds no feasible solution (e.g., no eligible cards at all) | `OptimizationResult.status == "infeasible"` | Results page renders "No eligible cards" state; directs user to check settings |
| MILP solver hits 30-second timeout | `OptimizationResult.status == "timeout"` | Results page renders with best-found solution + a banner: "Optimization did not complete fully — result may not be globally optimal. Tip: reduce card count by tightening eligibility settings." |
| Card JSON fails to parse | `CardDatabaseLoader` raises `ValueError` at startup | Application refuses to start; error is logged with the offending record's `id` field |
| SQLite write failure | SQLAlchemy raises `OperationalError` | HTTP 500; generic error page rendered; full traceback logged |
| Spreadsheet export failure | `openpyxl` raises any exception | Inline error below export button; no page reload; full exception logged |
| Unknown store name submitted | `StoreSlugResolver` returns `None` for slug | Store is treated as "General retail" (`category = "other"`); a yellow classification tag is rendered in the results table |
| Session cookie missing or expired | `OptimizationSession.load` returns `None` | Redirect to `GET /` (input page) with a flash message: "Your session has expired. Please re-enter your spending." |

All exceptions are caught at the router level. The logging module is used throughout — no `print()` statements. Every exception log includes the session ID (if available) and the request path.

---

## 7. Configuration and Environment

**`.env` (gitignored)**

```
SECRET_KEY=<random 32-byte hex>      # Used for session cookie signing
DATABASE_URL=sqlite:///./data/cc_optimizer.db
CARD_DATABASE_PATH=data/cards/cards.json
STORE_MCC_MAP_PATH=data/stores/store_mcc_map.json
MCC_CODES_PATH=data/stores/mcc_codes.json
VALUATION_CONFIG_PATH=config/valuation.json
SESSION_TTL_HOURS=24
MILP_TIME_LIMIT_SECONDS=30
LOG_LEVEL=INFO
```

**`.env.example` (committed)**

```
SECRET_KEY=replace_with_random_hex_string
DATABASE_URL=sqlite:///./data/cc_optimizer.db
CARD_DATABASE_PATH=data/cards/cards.json
STORE_MCC_MAP_PATH=data/stores/store_mcc_map.json
MCC_CODES_PATH=data/stores/mcc_codes.json
VALUATION_CONFIG_PATH=config/valuation.json
SESSION_TTL_HOURS=24
MILP_TIME_LIMIT_SECONDS=30
LOG_LEVEL=INFO
```

**`config/valuation.json` (committed)**

Cents-per-point defaults, editable without a code change:

```json
{
  "cashback": 1.0,
  "amex_mr": 2.0,
  "aeroplan": 2.1,
  "scene_plus": 1.0,
  "td_rewards": 0.5,
  "bmo_rewards": 0.71,
  "rbc_avion": 1.5,
  "pc_optimum": 1.0
}
```

---

## 8. Pydantic Model Reference

All structured data crosses component boundaries as Pydantic models. Key models:

**`CardRecord`** (card.py)

```python
class ApprovalRequirements(BaseModel):
    min_credit_score: int
    min_personal_income: float
    min_household_income: float
    source: Literal["issuer", "community", "estimated"]
    confidence: Literal["high", "medium", "low"]

class StoreOverride(BaseModel):
    rate: float
    source: Literal["issuer", "community", "estimated"]
    note: str = ""

class CardRecord(BaseModel):
    id: str
    name: str
    issuer: str
    network: Literal["Visa", "Mastercard", "Amex", "Other"]
    annual_fee: float
    first_year_fee: float
    requires_amex: bool
    approval: ApprovalRequirements
    category_rates: dict[str, float]
    category_caps_monthly: dict[str, float] = {}
    store_overrides: dict[str, StoreOverride] = {}
    store_acceptance: dict[str, bool] = {}
    point_system: str
    cpp_default: float
    last_verified_date: str
    source_url: str
    override_notes: str = ""
    is_dummy: bool = False
```

**`SpendingProfile`** (spending.py)

```python
class CreditScoreBand(str, Enum):
    FAIR = "fair"         # < 660
    GOOD = "good"         # 660-724
    VERY_GOOD = "very_good"  # 725-759
    EXCELLENT = "excellent"  # 760+

class IncomeBand(str, Enum):
    UNDER_40K = "under_40k"
    B40_60K = "40k_60k"
    B60_80K = "60k_80k"
    B80_100K = "80k_100k"
    B100_150K = "100k_150k"
    OVER_150K = "over_150k"

class PersonProfile(BaseModel):
    credit_score_band: CreditScoreBand
    income_band: IncomeBand

class DummyCard(BaseModel):
    name: str
    annual_fee: float = 0.0
    base_rate: float
    category_rates: dict[str, float] = {}

class SpendingProfile(BaseModel):
    user_id: str = "default"
    household_id: str = "default"
    category_spend: dict[str, float]      # category_key -> monthly CAD
    store_spend: dict[str, float]         # store_slug -> monthly CAD
    custom_store_spend: list[tuple[str, str, float]]  # (name, resolved_category, monthly_cad)
    chexy_rent_amount: float = 0.0
    include_amex: bool = False
    person1: PersonProfile
    couple_mode: bool = False
    person2: PersonProfile | None = None
    current_card_ids: list[str] = []     # for delta calculator
    dummy_cards: list[DummyCard] = []
```

**`OptimizationResult`** (optimization.py)

```python
class AssignmentRow(BaseModel):
    bucket_id: str
    label: str                    # human-readable label for the category/store
    cardholder: Literal["person1", "person2"] | None
    card_id: str
    card_name: str
    monthly_spend: float
    reward_rate_pct: float        # effective rate after overrides
    expected_monthly_reward: float
    is_chexy: bool = False
    chexy_net_rate_pct: float | None = None
    explanation: str              # "Why this card?" one-liner

class CardSummaryRow(BaseModel):
    card_id: str
    card_name: str
    annual_fee: float
    assigned_labels: list[str]
    estimated_annual_reward: float
    net_annual_value: float       # reward - annual_fee

class OptimizationResult(BaseModel):
    status: Literal["optimal", "feasible", "infeasible", "timeout"]
    monthly_net_reward: float
    annual_net_reward: float
    baseline_monthly_reward: float    # 2% flat cash-back reference
    rows: list[AssignmentRow]
    card_summary: list[CardSummaryRow]
    cards_considered: list[CardRecord]  # full eligible pool, for spreadsheet tab 3

class DeltaResult(BaseModel):
    current_annual_reward: float
    optimal_annual_reward: float
    delta_annual: float
    current_result: OptimizationResult
    optimal_result: OptimizationResult
```

---

## 9. Extensibility Notes

**Plugin interfaces at every external boundary**

- `CardDatabaseLoader` is an abstract base class (`abc.ABC`). The JSON implementation is the concrete class for the PoC. A future SQL or API-backed implementation swaps in without touching the optimizer or routes.
- `MILPOptimizer` is defined as an abstract `OptimizerBase` class. The PuLP/CBC implementation is the concrete class. If OR-Tools CP-SAT or a different solver is needed, it implements the same interface.

**Multi-tenant schema**

Every SQLite table has `user_id` and `household_id` columns. The PoC defaults both to `"default"`. Phase 2 adds auth and routes each request to the correct tenant. No migration needed — the columns are already there.

**Card database extensibility**

Every `CardRecord` has `last_verified_date`, `source_url`, and `override_notes`. Future community-contribution workflow: a web form submits a JSON patch; the patch is reviewed and merged via pull request. The data model supports this without schema changes.

**CPP valuation**

`config/valuation.json` is read at startup. Future phase: expose a per-user CPP override in the settings panel, stored in the session profile. The optimizer already reads CPP from `card.cpp_default` crossed with the config file — adding a user override is a single parameter injection.

**Future product categories (banking, broker, utility)**

The `SpendingProfile` model has `user_id` and `household_id` fields. Future product category models will use the same tenant identifiers. The optimization engine's abstract interface is not credit-card-specific at the algorithm level — it solves any assignment problem with caps and binary selection variables.

**Bookkeeping app integration**

The `SpendingProfile` model is designed as a data contract, not a form model. When the bookkeeping app integration is built, it will produce a `SpendingProfile` object directly from transaction data, passing it to the same optimizer pipeline. The web form is one producer; the bookkeeping app will be another.
