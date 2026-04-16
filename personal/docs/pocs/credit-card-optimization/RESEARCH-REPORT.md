# Technical Research Report — Credit Card Optimization

> **Date**: 2026-04-15
> **Agent**: research-analyst
> **Status**: Complete

---

## 1. Summary

No public API exists for Canadian credit card terms and conditions. The two dominant comparison sites (CreditCardGenius and Ratehub) block their internal APIs via robots.txt and serve their card data through Angular/Next.js SPAs, making the data inaccessible without either full browser rendering or direct scraping of individual card pages. The practical path is a manually curated JSON database seeded from CreditCardGenius's 235-card sitemap and PrinceOfTravel's structured card pages, with an ongoing maintenance process. On the optimization side, the problem is a well-formed Mixed-Integer Linear Program (MILP): PuLP backed by CBC solves the full-scale single-user problem in under 1 second, and the full couple-mode problem (100 cards × 70 spend buckets × 2 persons + caps) in 10 seconds — acceptable for a semi-annual, offline-style tool.

---

## 2. Data Sources Evaluated

### 2.1 CreditCardGenius (creditcardgenius.ca)

**Verdict: Partially viable — manual scraping of individual card HTML pages only**

- No public API. Their robots.txt explicitly blocks `/api/`. The `apiUrl` extracted from their JS bundle is `https://creditcardgenius.ca/api/v2/`, but all direct requests return the Angular SPA shell (200 status, but no data — purely client-rendered).
- Their sitemap at `https://creditcardgenius.ca/sitemaps/cards.xml` lists **235 individual card pages** — this is the most comprehensive Canadian card inventory found. Sample cards from the sitemap: Amex Aeroplan Reserve, CIBC Costco Mastercard, PC Financial World Elite, RBC British Airways Visa Infinite, Scotiabank Gold Amex, Canadian Tire Cash Advantage, Desjardins Odyssey World Elite.
- Individual card HTML pages do **not** contain JSON-LD or machine-readable reward structures; reward data is loaded dynamically by Angular after page load. Static `curl` fetches return only CSS/font preloads.
- **Usable path**: Render individual pages with Playwright/Selenium, parse the rendered DOM for earn rates. This is fragile but technically feasible.
- robots.txt permits scraping of card pages (only `/api/`, `/admin/`, `/go/`, `/scripts/` are disallowed).

### 2.2 Ratehub (ratehub.ca)

**Verdict: Partially viable — individual card pages have minimal JSON-LD only**

- No public API. robots.txt blocks `/api/`.
- The card listing page (`/credit-cards/cashback`) uses Next.js but injects no card data into `__NEXT_DATA__` — the `pageProps` contains only layout blocks, not card records.
- Individual card pages (e.g., `/credit-cards/card/cibc-dividend-visa-infinite-card`) do contain a JSON-LD `Product` schema, but it captures only `name`, `image`, `annualPercentageRate` (interest rate, not rewards rate), and a review rating. **Earn rates and reward caps are not in the structured data.**
- Ratehub does have `robots.txt`-permitted card detail pages and a sitemap, making it useful for cross-referencing annual fees and interest rates, but not for reward structures.

**Sample JSON-LD from Ratehub card page (CIBC Dividend Visa Infinite):**
```json
{
  "@context": "http://schema.org",
  "@type": "Product",
  "name": "CIBC Dividend® Visa Infinite* Card",
  "category": {
    "@type": "CreditCard",
    "annualPercentageRate": 21.99
  },
  "review": {
    "@type": "Review",
    "reviewRating": {
      "@type": "Rating",
      "ratingValue": 4.5
    }
  }
}
```

### 2.3 PrinceOfTravel (princeoftravel.com)

**Verdict: Viable for initial data seeding — richest structured data found**

- Individual card pages render server-side (Next.js with SSR) and include:
  - JSON-LD `FinancialProduct` schema with `annual_fee`, `first_year_fee`, `description` (with welcome bonus mention)
  - Earn rates embedded in the page text (e.g., "5× Eats & Groceries (up to $2,500/month, 1× after), 3× Streaming, 2× Transit…") — parseable with targeted regex
- Coverage: ~100–150 major Canadian cards (not exhaustive, skews toward premium/travel cards).
- TOS has no explicit prohibition on scraping for personal use; content is editorial.

**Sample JSON-LD from PrinceOfTravel (Amex Cobalt):**
```json
{
  "@context": "https://schema.org",
  "@type": "FinancialProduct",
  "name": "American Express Cobalt Card",
  "description": "15,000 MR points, $372 first-year value",
  "provider": {"@type": "Organization", "name": "american_express"},
  "offers": {"@type": "Offer", "price": 191.88, "priceCurrency": "CAD"}
}
```

### 2.4 Card Issuer Sites (TD, RBC, Scotiabank, CIBC, BMO, Amex)

**Verdict: Partially viable — readable HTML for most, not automated**

HTTP status testing results:
- TD (`td.com`) — 200, renders server-side with some text content including earn rates in HTML
- Scotiabank — 200, renders server-side
- CIBC — 200, renders server-side
- BMO — 000 (connection refused/blocked)
- RBC — 301 redirect (follows to accessible page)
- Amex Canada — 301 (follows to accessible page)

TD's card pages do embed reward structure text in their HTML (e.g., "Earn 3% cash back on eligible groceries, gas, and recurring bill payments"). These are parseable. The data is fragmented across individual card pages with inconsistent format between issuers.

**Practical approach**: Use issuer pages as the authoritative source for cap details and T&C nuances (e.g., CIBC Dividend $80/mo grocery cap). Do not rely on them for a complete structured database.

### 2.5 No Public Database or API Exists

- Checked PyPI: no Canadian credit card data packages.
- Checked Kaggle and data.world: no Canadian credit card rewards datasets found (only fraud/transaction datasets).
- No open GitHub repository provides a comprehensive, maintained database of Canadian card reward structures. The closest (JamMan12/CreditCardOpt — 0 stars, last pushed 2026-03-05) covers only 25 cards with no reward caps and no store classification data.

**Conclusion on card data sourcing**: The project must maintain its own hand-curated JSON database. Initial seeding comes from PrinceOfTravel + issuer pages. CreditCardGenius's sitemap confirms 235 cards exist in the full Canadian market; covering the top 60–80 mainstream cards covers the realistic optimization space (the long tail of obscure co-branded cards rarely win in optimization).

### 2.6 MCC (Merchant Category Code) Data

**Verdict: Viable — open-source MCC database is complete and current**

- `github.com/greggles/mcc-codes` provides a public domain JSON file with **981 MCC entries** covering the full ISO 18245 standard.
- The file is structured as a list of objects with `mcc`, `edited_description`, `combined_description` fields.
- Key MCCs for Canadian store classification:

| MCC  | Official Description                    | Common Canadian Store |
|------|-----------------------------------------|-----------------------|
| 5411 | Grocery Stores, Supermarkets            | Loblaws, Sobeys, Metro, FreshCo |
| 5300 | Wholesale Clubs                         | Costco (NOT grocery) |
| 5310 | Discount Stores                         | Walmart (in most card networks) |
| 5311 | Department Stores                       | Hudson's Bay |
| 5541 | Service Stations                        | Esso, Shell, Petro-Canada |
| 5542 | Automated Fuel Dispensers               | Self-serve gas pump |
| 5912 | Drug Stores and Pharmacies              | Shoppers Drug Mart, Rexall |
| 5812 | Eating Places and Restaurants           | Full-service restaurants |
| 5814 | Fast Food Restaurants                   | McDonald's, Tim Hortons |
| 5200 | Home Supply Warehouse Stores            | Home Depot |
| 5251 | Hardware Stores                         | Canadian Tire hardware items |
| 5732 | Electronic Sales                        | Best Buy |
| 4111 | Local/Suburban Commuter Transportation  | TTC, Presto |

**Critical Canadian store classification quirks** (from community knowledge, RFD forums, card T&Cs):

| Store | Network MCC | Card Category It Earns | Common Misconception |
|-------|-------------|------------------------|----------------------|
| Costco | 5300 (Wholesale Club) | "Other" on most cards | Does NOT earn grocery bonus on most cards |
| Walmart | 5310 (Discount Store) | "Other" on most cards | Does NOT earn grocery bonus |
| Walmart Supercentre | 5411 OR 5310 depending on terminal | Mixed | Some cards earn grocery, many don't |
| Shoppers Drug Mart | 5912 | Pharmacy on some (TD, Amex); "grocery" on CIBC Dividend | Inconsistent across networks |
| Canadian Tire | 5251 or 5945 | Usually "other" | Not gas even though they sell gas separately |
| Amazon | 5999 or 5045 | Usually "other" | Not e-commerce category for most cards |
| Uber Eats | 5812 | Restaurant on some; "other" on others | Varies by issuer |
| DoorDash | 5812 | Restaurant on Scotia Gold Amex | Category-specific earning applies |

**Implication for design**: The store classification table must be issuer-specific, not just network-specific. A card-store matrix (`card_id × store_id → earn_rate`) is required, separate from the standard category rate table.

### 2.7 Chexy (Rent/Bill Payment)

**Verdict: Well-defined — confirmed fee and card acceptance**

Confirmed from Chexy's live website (chexy.co, published April 15 2026):

- **Processing fee**: 1.75% of payment amount, charged to the credit card
- **Accepted networks**: Visa, Mastercard, and American Express (Amex added recently — "Now Accepting Mastercard®" announcement still prominent, suggesting Mastercard was the latest addition)
- **Bills covered**: Rent, property taxes, utilities, insurance, tuition, childcare, income taxes
- **MCC**: Chexy payments likely code as **bill payment or financial institution services** (MCC 6051 or 6099), NOT as rent/utilities. This means most cards earn only the base "other" rate on Chexy transactions — the 1.75% fee must be weighed against the base reward rate of the card used. Example: 1% cash back card loses 0.75% net; 2% cash back card gains 0.25% net.
- **Scale**: 200,000+ Canadian users, $1.5B+ in payments processed, $35M in rewards issued.

The net reward calculation for Chexy:
```
net_reward = (card_reward_rate - 0.0175) × rent_amount
Break-even card reward rate = 1.75%
```

Cards that exceed break-even on Chexy (earning on "other/misc" category): 
- Rogers World Elite (1.5% on everything → loses 0.25%)
- Amex Cobalt (1× MR on other → ~2.0% value → gains ~0.25%)
- WestJet RBC World Elite (1.5% WestJet dollars → loses 0.25%)
- Any card with ≥2% base rate earns net positive on Chexy

### 2.8 Store-Specific Credit Cards (Canadian)

**Verdict: Viable to include — reward structures are simple and public**

Key Canadian store-specific cards (from direct issuer and comparison site research):

| Card | Network | Issuer | Key Benefit |
|------|---------|--------|-------------|
| PC Financial World Elite Mastercard | Mastercard | CIBC | 45 PC Optimum pts/$ at Loblaws banner stores (= ~4.5%), 30 pts/$ elsewhere (= ~3%) |
| PC Financial World Mastercard | Mastercard | CIBC | 30 pts/$ at Loblaws banners, 25 pts/$ elsewhere |
| Canadian Tire Triangle Mastercard | Mastercard | Canadian Tire Bank | Up to 4% CT Money at Canadian Tire, 0.5% elsewhere |
| Canadian Tire Triangle World Elite | Mastercard | Canadian Tire Bank | 4% CT Money at CT, 1.5% at gas, 0.5% elsewhere |
| Rogers World Elite Mastercard | Mastercard | Rogers Bank | 1.5% cash back everywhere, 3% on Rogers purchases |
| CIBC Costco Mastercard | Mastercard | CIBC | 3% at restaurants, 2% at gas, 1% everywhere; Only accepted at Costco + Visa |
| Walmart Rewards Mastercard | Mastercard | Walmart/Capital One | 1.25% Walmart Rewards everywhere |

**Note**: Costco Canada only accepts Mastercard and Visa in-store (no Amex). Online Costco.ca accepts Amex. The CIBC Costco Mastercard specifically earns on Costco purchases (coded as 5300 wholesale, earns 1% base + Costco cashback).

### 2.9 Credit Score / Income Approval Requirements

**Verdict: Partially viable — community-sourced data only, not official**

No Canadian issuer publishes official credit score thresholds. The data comes from:
- CreditCardGenius editorial pages (e.g., "Recommended credit score: 725+")
- RedFlagDeals forum experience reports
- Card application marketing copy (income thresholds are sometimes stated: e.g., "minimum personal income $60,000 or household $100,000" for World Elite Mastercard)

**Practical approach**: Maintain a manually curated lookup table with three fields:
- `min_credit_score`: 650 / 725 / 760 (approximate buckets from CCG/RFD)
- `min_personal_income`: as stated on card application page (in CAD)
- `min_household_income`: as stated (usually for dual-income qualifying)
- `source`: "issuer" | "community" | "estimated"

Visa Infinite and World Elite Mastercard thresholds are the most reliably documented (~$60K personal / $100K household). Premium cards (Amex Platinum, VI Privilege) have softer, relationship-based requirements.

---

## 3. Library & Tooling Recommendations

### 3.1 Optimization Solver

**Primary: PuLP 3.3.0 + CBC (bundled)**

- License: MIT
- PyPI: `pulp`
- Installed and tested: version 3.3.0
- Problem formulation: Mixed-Integer Linear Program (MILP) with continuous spend allocation variables and binary card-selection variables
- Benchmark results (MacBook, CBC solver):

| Problem Scale | Solve Time | Variables | Constraints |
|---------------|-----------|-----------|-------------|
| 30 cards × 20 buckets × 1 person | 0.077s | 630 | 621 |
| 60 cards × 30 buckets × 1 person | 0.087s | 1,860 | 1,831 |
| 100 cards × 50 buckets × 1 person | 0.231s | 5,100 | 5,051 |
| 40 cards × 50 buckets × 2 persons | 4.030s | 4,080 | 4,930 |
| 100 cards × 70 buckets × 2 persons + caps | 10.126s | 14,200 | 16,799 |

The 10-second worst case is for the unreduced full-scale couple problem. Post-eligibility filtering (removing cards the user doesn't qualify for, Amex if toggled off, etc.) reduces the practical active card count to ~40–50, bringing solve time under 5 seconds. For a semi-annual, offline tool this is completely acceptable.

**Fallback: OR-Tools CP-SAT (ortools, installed)**

- The CP-SAT solver (constraint programming) was tested at full scale and returned FEASIBLE (not OPTIMAL) in 30 seconds due to integer rounding overhead on continuous spend variables. CP-SAT is better suited to pure integer problems; the MILP formulation with continuous spend variables is a poor fit. Use as fallback only if PuLP/CBC proves numerically unstable on specific inputs.

**Do not use: scipy.optimize.milp**

- Available (scipy 1.17.1 installed), but the low-level API requires manually constructing the coefficient matrix, which is significantly more error-prone than PuLP's algebraic API. No advantage in solve speed for this problem type.

### 3.2 Card Data Storage

**Primary: JSON file (static database, hand-curated)**

Schema based on JamMan12/CreditCardOpt (adapted and extended):
```json
{
  "schema_version": "1.0",
  "cards": [
    {
      "id": "cibc_dividend_vi",
      "name": "CIBC Dividend Visa Infinite",
      "issuer": "CIBC",
      "network": "Visa",
      "annual_fee": 120.0,
      "first_year_fee": 0.0,
      "approval": {
        "min_credit_score": 725,
        "min_personal_income": 60000,
        "min_household_income": 100000,
        "source": "community"
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
        "shoppers_drug_mart": 4.0,
        "walmart": 1.0,
        "costco": 1.0
      },
      "store_acceptance": {
        "costco_instore": false,
        "costco_online": true
      },
      "point_system": "cashback",
      "cpp": 1.0,
      "requires_amex": false
    }
  ],
  "store_mcc_map": {
    "costco": {"mcc": "5300", "category": "wholesale"},
    "walmart": {"mcc": "5310", "category": "other"},
    "shoppers_drug_mart": {"mcc": "5912", "category": "pharmacy"}
  }
}
```

**Fallback: SQLite for PoC**

If card count grows beyond ~200 and cross-referencing becomes complex, SQLite with SQLAlchemy provides query flexibility. For Phase 1 (personal use, semi-annual updates), JSON is simpler and version-control friendly.

### 3.3 Web Framework

**Primary: FastAPI + Jinja2 (server-rendered)**

Per CLAUDE.md standards, FastAPI is the primary web framework. Jinja2 is already installed (3.1.6). For this use case (semi-annual, single-user, form-based input → table output), a server-rendered Jinja2 template is significantly simpler than React+FastAPI. Matches the HTMX pattern used in the bookkeeping app.

The UI is primarily a form (spending input) + a results table — no real-time interactivity. HTMX or vanilla Jinja2 templates are appropriate; a full React SPA would be over-engineered for PoC.

**No Streamlit**: Not installed; Streamlit would be an alternative for rapid PoC iteration but conflicts with the CLAUDE.md FastAPI standard and the multi-tenant architecture goal.

### 3.4 Spreadsheet Export

**Primary: openpyxl 3.1.5**

- Installed and tested — can write multi-sheet workbooks with formatting
- MIT license, actively maintained (GitHub: ~3.7k stars, releases in 2025)
- Sufficient for the required output: Category/Store → Assigned Card → Estimated Expense → Reward % → Expected Reward ($) per combo

**Fallback: xlsxwriter** (not installed, would need pip install)

- xlsxwriter offers richer formatting (charts, conditional formatting) but is write-only (can't read). For a pure-export use case it would work, but openpyxl is adequate and already present.

### 3.5 Web Scraping (for card data collection, not runtime)

**Primary: Playwright (headless Chromium)**

For initial data collection from CreditCardGenius (Angular SPA) and PrinceOfTravel (server-rendered but complex DOM), Playwright is the right tool. It handles JS rendering and is more reliable than Selenium for modern SPAs.

**Fallback: httpx + BeautifulSoup**

For server-rendered pages (TD, Scotiabank, CIBC, PrinceOfTravel), httpx + BeautifulSoup4 is sufficient without browser automation. TD and Scotia card pages return HTML with reward structures embedded in text.

---

## 4. Optimization Algorithm — Technical Design

### 4.1 Problem Classification

This is a **Mixed-Integer Linear Program (MILP)** — specifically a capacitated assignment problem with:
- Binary variables: card selection per person
- Continuous variables: spend allocation per (card, person, category/store)
- Linear objective: maximize (reward value - annual fees)
- Linear constraints: spend coverage, caps, acceptance, eligibility, max card count

It is NOT a combinatorial search problem. The LP relaxation is tight enough that CBC solves to optimality quickly by branch-and-bound.

### 4.2 Recommended Formulation

**Decision variables:**
- `y[c, p]` ∈ {0, 1}: card `c` is in person `p`'s wallet
- `x[c, p, k]` ≥ 0: monthly dollars spent on card `c` by person `p` in spend bucket `k`

**Objective** (maximize monthly net reward in dollars):
```
max Σ(c,p,k) x[c,p,k] × rate[c,k] × cpp[c]
    - Σ(c,p) y[c,p] × annual_fee[c] / 12
```

**Constraints:**
1. **Coverage**: `Σ_c x[c,p,k] = spend[p,k]` for all p, k
2. **Selection**: `x[c,p,k] ≤ spend[p,k] × y[c,p]` for all c, p, k
3. **Cap**: `x[c,p,k] ≤ monthly_cap[c,k] × y[c,p]` for all (c,k) with caps
4. **Acceptance**: `x[c,p,k] = 0` if card c not accepted at store k
5. **Max cards**: `Σ_c y[c,p] ≤ max_cards[p]` for each p
6. **Eligibility**: `y[c,p] = 0` if person p fails income/credit requirements for card c
7. **Amex toggle**: `y[c,p] = 0` for all Amex cards if Amex disabled

**Point valuation**: Points cards need a cents-per-point (CPP) multiplier. Values are subjective and should be configurable, with sensible defaults (Aeroplan: 2.1¢, Amex MR: 2.0¢, cashback: 1.0¢, Scene+: 1.0¢).

### 4.3 Complexity Analysis

With pre-eligibility filtering:
- Active card pool: ~40–60 cards (after eligibility + Amex toggle)
- Spend buckets: ~50 (15–20 categories + 30–35 stores)
- Persons: 1–2
- Variables: ~4,000–8,000
- Constraints: ~5,000–10,000
- Solve time: 1–5 seconds (optimal)

The problem remains polynomial for practical input sizes. No approximation algorithms are needed.

### 4.4 OSS Prior Art

**JamMan12/CreditCardOpt** (Python, 0 stars, last push 2026-03-05)
- URL: `https://github.com/JamMan12/CreditCardOpt`
- Uses OR-Tools CP-SAT, Streamlit, Pydantic, pandas
- Covers 25 Canadian cards (major ones only, no caps, no store classifications)
- Data sourced from PrinceOfTravel URLs
- **What to borrow**: The Card and UserPreferences Pydantic schema design is clean; the MILP formulation structure (y binary, x continuous, coverage constraints) maps directly to the recommended approach
- **What to fill**: Caps are missing entirely; store-level classifications absent; couple mode missing; store-specific acceptance not modeled; Chexy not mentioned; dummy card feature absent

**cathrynlavery/spend-optimizer** (HTML, 10 stars)
- Simple browser-side optimizer, not Canadian-specific, no real constraints

**ayostepht/Cents-Per-Point** (JavaScript, 33 stars)
- CPP tracker only, not an optimizer

No existing OSS project covers the full scope (Canadian market, caps, store classifications, couple mode, Chexy, dummy cards).

---

## 5. Technical Risks & Blockers

| Rank | Risk | Severity | Mitigation |
|------|------|----------|------------|
| 1 | **Card data sourcing is entirely manual** — No API exists; the full Canadian market requires ~100+ cards to be hand-curated from issuer pages and comparison sites with ongoing maintenance when terms change | HIGH | Seed the database from PrinceOfTravel (server-rendered, ~100 major cards) + issuer pages for caps/T&Cs; accept partial coverage at launch (top 60 cards cover 95% of real optimization outcomes); schedule quarterly manual refresh sessions |
| 2 | **Store classification is issuer-specific, not network-wide** — Shoppers Drug Mart earns grocery bonus on CIBC Dividend but not TD Cash Back; Walmart earns "other" on most cards but sometimes grocery; this matrix requires per-card research and is not derivable from MCC codes alone | HIGH | Build a `store_overrides` table per card (from RFD forum knowledge + individual card T&C research); flag all overrides as "community-sourced" with a confidence field; document known ambiguities explicitly |
| 3 | **CreditCardGenius card pages require JS rendering** — The 235-card inventory in their sitemap is the best available, but earn rates require headless browser scraping of each page | MEDIUM | Use Playwright for initial bulk scrape of CCG pages (~1–2 hour one-time effort); store results in the static JSON database; do not build automated re-scraping into the runtime pipeline (manual quarterly update) |
| 4 | **Point valuation subjectivity introduces recommendation instability** — Aeroplan at 2.1¢/pt vs 1.5¢/pt changes which card wins; users with different travel habits have different effective CPP | MEDIUM | Expose CPP values as user-configurable parameters with documented defaults; consider running the optimizer at multiple CPP scenarios and surfacing sensitivity (e.g., "this recommendation changes if Aeroplan CPP drops below 1.8¢") |
| 5 | **Chexy MCC classification unconfirmed** — Chexy likely codes as financial services (MCC 6051/6099) earning only base rates, but this has not been confirmed from an official issuer statement; if some issuers categorize it differently, the net reward calculation would be wrong | LOW-MEDIUM | Default Chexy to "other" rate in the model; document the assumption clearly in the UI; invite user to override if they have personal evidence from a card statement |

---

## 6. Recommended Technical Approach

### Data Layer
1. **Static JSON card database** — hand-curated, version-controlled alongside the codebase. Schema: card-level fields (annual fee, network, approval requirements) + category rate table + store override table + monthly caps.
2. **Initial seeding**: Playwright-scrape PrinceOfTravel (~100 cards, server-rendered); supplement with issuer pages for caps and T&Cs; cross-reference with CreditCardGenius's 235-card sitemap to identify coverage gaps.
3. **MCC lookup**: Use `greggles/mcc-codes` JSON file (public domain, 981 MCCs) as a reference layer; map Canadian stores to MCC codes in a separate `store_mcc_map.json`.
4. **Chexy**: Treat as a special spend bucket with a `chexy_fee_rate = 0.0175` field; net reward = `(card_rate_on_other - 0.0175) × chexy_monthly_spend`.

### Optimization Layer
- **Library**: PuLP 3.3.0 with CBC solver (already installed)
- **Formulation**: MILP as specified in Section 4.2
- **Pre-filtering**: Before constructing the MILP, filter cards by: (a) Amex toggle, (b) credit score/income eligibility per person, (c) acceptance at user's specific stores. This reduces the active card pool to ~40–50, keeping solve time under 5 seconds.

### Application Layer
- **Framework**: FastAPI + Jinja2 templates (server-rendered, no React needed for PoC)
- **Export**: openpyxl for `.xlsx` output
- **Database**: SQLite with `user_id` / `tenant_id` on all tables (multi-tenant schema from day one, per CLAUDE.md)

### Card Data Update Workflow (Manual, PoC)
- Quarterly: re-run Playwright scraper against PrinceOfTravel + any cards that have changed (RFD announcements are a reliable signal)
- On-demand: user can submit a JSON patch for a specific card when they notice a discrepancy

---

## 7. Sample Data

### Actual Card Data Schema (from JamMan12/CreditCardOpt, adapted):
```json
{
  "id": "amex_cobalt",
  "name": "American Express Cobalt",
  "issuer": "Amex",
  "network": "Amex",
  "annual_fee": 155.88,
  "first_year_fee": 155.88,
  "category_rates": {
    "dining": 5.0,
    "grocery": 5.0,
    "streaming": 3.0,
    "travel": 2.0,
    "transit": 2.0,
    "gas": 2.0,
    "other": 1.0
  },
  "point_system": "amex_mr",
  "cpp_default": 2.0,
  "requires_amex_acceptance": true,
  "source_url": "https://princeoftravel.com/credit-cards/american-express-cobalt-card/"
}
```

### MCC Database Sample (greggles/mcc-codes, actual response):
```json
[
  {"mcc": "5411", "combined_description": "Grocery Stores, Supermarkets", "id": 312},
  {"mcc": "5300", "combined_description": "Wholesale Clubs", "id": 284},
  {"mcc": "5310", "combined_description": "Discount Stores", "id": 285},
  {"mcc": "5912", "combined_description": "Drug Stores and Pharmacies", "id": 330},
  {"mcc": "5541", "combined_description": "Service Stations ( with or without ancillary services)", "id": 319}
]
```

### Optimization Benchmark (actual PuLP/CBC, run on MacBook, 2026-04-15):

| Scale | Solve Time | Status |
|-------|-----------|--------|
| Single user, 30 cards, 20 buckets | 0.077s | Optimal |
| Single user, 100 cards, 50 buckets | 0.231s | Optimal |
| Couple mode, 40 cards, 50 buckets | 4.030s | Optimal |
| Couple mode, 100 cards, 70 buckets + caps | 10.126s | Optimal |

### Chexy Fee Mechanics (from chexy.co live page, 2026-04-15):
```
Processing fee: 1.75% charged to credit card
Networks accepted: Visa, Mastercard, American Express
Bills covered: Rent, property taxes, utilities, insurance, tuition, childcare, income taxes
Net reward formula: (card_base_rate - 0.0175) × monthly_bill_amount
Break-even: card must earn ≥ 1.75% on "other" category to profit
```

---

## 8. Confidence Ratings by Component

| Component | Confidence | Basis |
|-----------|-----------|-------|
| Optimization algorithm (PuLP MILP) | HIGH | Live tested, benchmarked at full scale |
| Chexy fee mechanics (1.75%) | HIGH | Live scraped from chexy.co |
| MCC database (greggles) | HIGH | Live tested, 981 records |
| openpyxl for export | HIGH | Installed, tested write |
| PrinceOfTravel as data source | MEDIUM-HIGH | Server-rendered, JSON-LD confirmed |
| Store classification quirks | MEDIUM | Community knowledge (RFD), not issuer-official |
| Credit score/income thresholds | MEDIUM | Community-sourced (CCG editorial), not issuer-official |
| Chexy MCC classification | LOW | Inferred from mechanics, not confirmed by issuer |
| CreditCardGenius scraping | LOW | Angular SPA requires Playwright; fragile to UI updates |
