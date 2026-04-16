# Product Requirements Document — Credit Card Optimization

> **Status**: Approved
> **Author**: architect
> **Last Updated**: 2026-04-15

---

## 1. Problem Statement

Canadian credit card comparison tools fail active optimizers in two structural ways. First, they produce one-size-fits-all recommendations calibrated to a fictional "average" household spending profile that matches no real household. Second, the tools that do allow per-category input still reason about one card at a time — ignoring that a real wallet is a portfolio where reward caps, store-specific merchant category code (MCC) classifications, card acceptance constraints, and annual fees interact across every spending bucket simultaneously.

The result is that a financially literate Canadian who shops at Costco (coded as wholesale, not grocery, on most networks), pays rent via Chexy, and holds a partner with different card eligibility cannot find any tool that gives them a defensible, auditable answer to the question: "What is the best combination of credit cards for my actual household spending?"

A deeper structural problem makes this gap persistent: every Canadian comparison tool (Ratehub, CreditCardGenius, GreedyRates, Milesopedia) earns revenue through affiliate commissions paid by card issuers. This creates a direct financial incentive to recommend whichever card has the highest referral fee, not the one that maximizes the user's reward. No tool that depends on affiliate income can be an honest combination optimizer.

This PoC builds the thing that does not exist: **the smallest useful version of an honest Canadian credit card combination optimizer, used by the builder first**.

---

## 2. Target User

### Primary: The Active Self-Optimizer

A financially literate Canadian professional (data scientist, engineer, accountant, or similar) holding 3–6 credit cards simultaneously. Shops across Costco, grocery chains, gas stations, and restaurants. May or may not use Amex, depending on acceptance at preferred stores. Has a partner and manages joint household expenses. Performs a semi-annual "card audit" by reading forums, card T&Cs, and comparison sites — currently spending 2–4 hours per audit with no durable output and residual uncertainty about whether the result is actually optimal.

This user is technically literate enough to verify the math if given the inputs. They will trust the tool only if it explains every recommendation in plain English and lets them audit the calculation in a spreadsheet. They are the primary user of r/churningcanada (81K subscribers) and an active participant in r/PersonalFinanceCanada (1.83M subscribers).

### PoC User: The Builder Himself

The PoC is validated by the builder using it for his own household's semi-annual card review. If it produces a recommendation he can audit, trust, and act on — and if it surfaces a delta against his current card setup — the engine works.

---

## 3. Success Criteria

- [ ] Given a household spending profile with at least 10 distinct categories/stores, the optimizer returns an optimal card assignment in under 15 seconds.
- [ ] The recommendation accounts for all four real-world constraints: store-level MCC classification, per-card/per-category reward caps, card acceptance limitations (e.g., Costco is Mastercard-only in-store), and annual fee netting.
- [ ] Feature 2 (delta calculator) produces a before/after comparison: "Your current setup earns $X/year; the optimized setup earns $Y/year — a $Z improvement."
- [ ] The spreadsheet export contains all four tabs (Summary, Calculation Detail, Cards Considered, Input Echo) and is self-contained enough to audit every number in the web results.
- [ ] The optimizer handles couple mode: two cardholders with separate credit score and income eligibility profiles, combined household spending, per-person card assignments.
- [ ] The card database covers at least 60 major Canadian credit cards with accurate category rates, monthly caps, store overrides, and approval requirements.

---

## 4. Scope — What's IN

### Feature 1: Optimized Card Combination Recommendation (Must Have — Priority 1)

**Spending Input**
- Manual input of monthly spending in CAD by pre-populated category (groceries, gas, dining, coffee shops, streaming, phone/internet, utilities, rent/mortgage, insurance, transit, Amazon, drugstore/pharmacy, clothing/department stores, home improvement, flights, hotels, car rentals, foreign currency, everything else).
- A dedicated "Stores with Non-Obvious Classifications" sub-section (the keystone UX element) covering: Costco, Walmart, Shoppers Drug Mart, Canadian Tire, Loblaws/PC stores, Amazon Canada, LCBO/Beer Store, Lowe's/Reno-Depot. Each store shows its actual MCC classification and any per-card override notes.
- Custom store entry: user can add any store by name; the system looks up MCC from its database and shows the classification; unknown stores default to "General retail" with an override option.
- Custom (dummy) card entry: user defines a card by name, annual fee, and per-category reward percentages. Dummy cards compete in the optimizer on equal footing with database cards. Intended for foreign cards where the user handles FX math separately.

**Settings and Constraints**
- Amex toggle: include or exclude Amex cards from the eligible set.
- Eligibility per person: credit score band (< 660 / 660–724 / 725–759 / 760+) and annual income band (< $40K / $40K–$60K / $60K–$80K / $80K–$100K / $100K–$150K / $150K+).
- Couple mode: a toggle that reveals a second eligibility profile (Person 2). Combined household spending is entered once; the optimizer assigns cards per person. Cards requiring a minimum income use the individual applicant's income; household-income-qualifying cards use the combined figure.
- Chexy toggle: monthly rent amount field appears; Chexy's 1.75% processing fee is factored into net reward automatically using the card's "other" earn rate. Net reward = (card_other_rate − 0.0175) × monthly_rent.

**Optimization Engine**
- Mixed-Integer Linear Program (MILP) using PuLP 3.3.0 + CBC solver.
- Pre-filters the card pool by: Amex toggle, credit score/income eligibility per person, store acceptance constraints.
- Objective: maximize total monthly net reward (rewards earned × cents-per-point − annual fees prorated monthly).
- Constraints: full spend coverage, reward caps, store acceptance, eligibility per person.
- Points cards valued at configurable cents-per-point (CPP) defaults: Aeroplan 2.1¢, Amex MR 2.0¢, Scene+ 1.0¢, cashback 1.0¢. CPP values are in config, not hardcoded.

**Results Page**
- Summary banner: estimated monthly reward and annual net reward after all annual fees.
- Baseline comparison: "A 2% flat cash-back card would earn approximately $X/month. Your recommended setup earns $Y/month — $Z/month more." If the recommended set does not beat the 2% baseline, a warning banner replaces the summary.
- Assignment table (columns exactly as specified): Category/Store | Assigned Card | Estimated Monthly Expense | Reward % | Expected Monthly Reward ($). Sorted by Expected Monthly Reward descending by default; sortable by any column.
- "Why this card?" row expansion: one sentence per row in plain English explaining the assignment (e.g., "Scotiabank Gold Amex earns 5% at restaurants; no eligible card beats this rate for your dining spend of $300/month.").
- Card summary panel: one row per selected card showing annual fee, categories assigned, estimated annual reward from spending, and net annual value.
- Couple mode: assignment table includes a "Cardholder" column (Person 1 / Person 2).
- "Export Spreadsheet" button and "Adjust inputs" link back to the input page.

**Session State**
- Input form state is preserved in the server session for the duration of the browser session, enabling the Input → Results → Input round trip without re-entry.
- No login, no persistent storage between sessions. The spreadsheet export is the user's persistence mechanism.

### Feature 2: Delta Calculator — Current vs. Recommended Comparison (Must Have — Priority 2)

- Multi-select field on the input page (or an additional section): "Your current cards" — user selects cards they currently hold from the database.
- The optimizer runs twice: once constrained to the current card set, once unconstrained.
- Both results are shown on a delta results page: "Your current setup earns $X/year. The optimized setup earns $Y/year. Switching saves you $Z/year."
- The delta figure is the commercial-signal instrument: it validates the optimizer's value proposition and is the primary shareability hook for community launch.

**Spreadsheet Export**
- Four-tab .xlsx file: Summary, Calculation Detail, Cards Considered, Input Echo.
- File named `credit-card-optimization-YYYY-MM-DD.xlsx`.
- Export is free (no paywall). It is the trust-building and distribution mechanism.

**Card Database**
- Static JSON file, hand-curated, version-controlled.
- Each card record includes: `last_verified_date`, `source` (issuer / community / estimated), `override_notes`. These fields enable future community-contribution workflows without a migration.
- At least 60 major Canadian cards at launch, covering all major issuers (TD, RBC, Scotiabank, CIBC, BMO, Amex, PC Financial, Rogers, Canadian Tire, Capital One) and card types (cash back, travel points, store-specific).
- Store-override table per card (`store_overrides`): captures issuer-specific classifications (e.g., Shoppers Drug Mart earns grocery rate on CIBC Dividend but pharmacy rate on TD).

---

## 5. Scope — What's OUT

The following are explicitly excluded from the PoC. They are documented here to prevent scope creep.

- **Auth, billing, user accounts, landing page**: This is a personal-use PoC. No login screen, no subscription flow, no marketing copy.
- **Welcome bonus strategy (Feature 3)**: Optimizing across one-time signup bonuses is a separate problem from ongoing reward optimization. It introduces different constraints (spending requirements, time horizons, opportunity cost) and would muddy the primary output. Backlogged.
- **Configurable max card count**: The optimizer lets annual fees do natural pruning. A "recommend at most N cards" constraint is deferred; it requires a settings field, optimizer constraint, and explanation.
- **Bank feed / Plaid / open banking integration**: Spending input is manual for the PoC. Integration with the bookkeeping app is a future phase once both are independently working.
- **FX charge calculations for foreign cards**: The dummy card feature lets the user input net rates after FX. The tool does not compute FX math.
- **Automated card data refresh**: Card database is maintained manually for the PoC. Quarterly re-scraping is a process, not a product feature.
- **Affiliate links, "Apply Now" buttons, issuer links on results page**: Phase 2 commercial features. Excluded to preserve the honest-optimizer positioning.
- **Mobile optimization**: The input form is table-like and targets deliberate desktop sessions. The layout must not break catastrophically on a tablet, but no special mobile optimization is required.
- **Card count limit toggle, annual churn reminders, benefit tracking**: All deferred to Phase 2.
- **Expansion to banking, broker, utility comparisons**: The schema is forward-compatible but no features are built.
- **Side-by-side card comparison (per-card mode)**: This is what incumbents already do. The PoC does not build it.

---

## 6. User Workflow

1. **Open the tool.** Input page loads. No login. Form is either blank (first use) or pre-populated from session state if returning from the results page.
2. **Enter spending.** Work through the category groups. The "Stores with Non-Obvious Classifications" sub-section is prominently placed above the regular stores section. Enter monthly CAD amounts; leave unwanted categories at $0.
3. **Add custom stores (optional).** Click "+ Add a store." The system looks up the store's MCC classification. Unknown stores default to "General retail" with an override option.
4. **Configure settings (optional, collapsed by default).** Toggle Amex inclusion. Set credit score band and income band (Person 1). Toggle couple mode to add Person 2's eligibility. Toggle Chexy and enter monthly rent if applicable.
5. **Add dummy cards (optional, collapsed by default).** Define any card not in the database: name, annual fee, per-category reward rates.
6. **Enter current card holdings (Feature 2).** Multi-select from the card database. The optimizer will run a constrained solve against this set to produce the delta comparison.
7. **Click "Optimize".** A progress message appears: "Analyzing [N] cards against your spending profile…" Solver runs; if it takes over 10 seconds, a "still working…" message appears.
8. **Read the results page.** Summary banner first: monthly and annual net reward. Delta section (Feature 2): current vs. recommended comparison. Assignment table: one row per category/store. "Why this card?" expansion available on every row. Card summary panel below.
9. **Export spreadsheet (optional).** Click "Export calculation spreadsheet (.xlsx)." File downloads immediately.
10. **Adjust and re-optimize (optional).** Click "Adjust inputs." Input page re-populates with previous values. Change any input and re-run.

---

## 7. Assumptions

- The user is comfortable entering approximate monthly spending amounts. Precision to the nearest $50 is sufficient for meaningful optimization.
- Couple mode uses combined household spending. Both people shop the same stores in roughly the same proportion; the optimizer assigns which person's card to use at each store, not which fraction of spending goes where per person.
- Chexy payments code as MCC 6051 or 6099 (financial services / bill payment) and earn the card's base "other" rate. This is unconfirmed from issuer statements; the assumption is documented in the UI and the Calculation Detail tab.
- Store-specific loyalty cards (PC Optimum card, Canadian Tire Triangle) are treated as regular credit cards in the optimizer. Stacking a loyalty card on top of a credit card is not modelled; users who do this can account for it via a dummy card.
- Points card valuation is subjective. Default CPP values (Aeroplan 2.1¢, Amex MR 2.0¢) are documented defaults, not guarantees. Users with different redemption habits should override CPP values in config.
- The card database at launch covers 60+ major Canadian cards. The long tail of obscure co-branded cards rarely wins in optimization; covering the top cards covers the realistic decision space.
- Credit score and income thresholds in the database are community-sourced (CreditCardGenius editorial, RedFlagDeals forum data), not issuer-official. The `source` field on each card record documents this.
- The 2% flat cash-back baseline is the appropriate benchmark for a Canadian audience (reflects premium no-annual-fee cash-back cards like Rogers Red Mastercard, which earns 1.5% everywhere, and Rogers World Elite, which earns 1.5% on all and 3% on Rogers purchases; 2% represents the achievable no-fee ceiling in the Canadian market).

---

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Card data sourcing is entirely manual — no API exists; accurate reward structures require hand-curation from issuer pages | High | High | Seed from PrinceOfTravel (server-rendered, ~100 cards, JSON-LD) + issuer pages for caps; accept 60-card coverage at launch; schedule quarterly manual refresh; document `last_verified_date` on every record |
| Store classification is issuer-specific, not derivable from MCC codes alone — getting it wrong silently corrupts the optimization | High | High | Build per-card `store_overrides` table; source from RFD forum knowledge + individual T&Cs; flag all overrides with `source` and `confidence` fields; surface classification in UI with "may vary" tags |
| CreditCardGenius card pages require JavaScript rendering — 235-card inventory requires Playwright scraping, fragile to UI updates | Medium | Medium | Use Playwright for one-time bulk seeding; store results in the static JSON database; do not build runtime re-scraping; quarterly manual review is the maintenance model |
| Point valuation subjectivity causes recommendation instability between users with different travel habits | Medium | Medium | Expose CPP as configurable values in `config/valuation.json`; show CPP assumptions in the Calculation Detail spreadsheet tab; consider a sensitivity note ("this recommendation changes if Aeroplan CPP drops below 1.8¢") in Phase 2 |
| Chexy MCC classification unconfirmed — if some issuers earn a higher rate on Chexy, the net reward calculation would be wrong | Low-Medium | Medium | Default to "other" rate; document assumption explicitly in the UI and in the Input Echo spreadsheet tab; invite user to override if they have personal statement evidence |
| Card database accuracy degrades over time as issuers change terms | High | Medium | Every record has `last_verified_date`; build a simple JSON patch workflow for updates; design for future community-contribution model without requiring it at launch |
| Affiliate incumbents copy the combination optimizer feature | Low (24-month horizon) | High | Differentiation rests on transparent methodology and no issuer relationships — lean into this aggressively in community launch messaging; the spreadsheet export and "Why this card?" explanations are the artefacts that prove no affiliate bias |

---

## 9. Positioning

This tool is positioned as **"The Honest Combination Optimizer."** The word "honest" is load-bearing: every Canadian comparison site has an affiliate conflict of interest. They recommend individual cards proportional to referral fee revenue, not mathematical optimality. This tool charges the user and earns nothing from issuers, which is the only model that permits an honest recommendation.

The methodology is published transparently. The card database is version-controlled and documented. The spreadsheet export is free because it is both the trust-building mechanism and the distribution vehicle — a user who shares their spreadsheet in a Reddit post with the tool's URL in cell A1 is marketing the tool at zero cost.

Community launch targets r/churningcanada first (81K subscribers, highly engaged optimizers who already do this manually in spreadsheets), then r/PersonalFinanceCanada (1.83M subscribers). The launch post is not a pitch — it is a worked example: "I ran my own household spending through it. My previous combination earned $X/year. The optimizer found a better combination earning $Y/year — a $Z improvement I had missed because Costco codes as wholesale, not grocery." The delta figure (Feature 2) makes this post possible.

---

## 10. Future Considerations

The following are Phase 2 and Phase 3 considerations. They are referenced here for schema and architecture awareness only — no features are built toward them in the PoC.

- **Welcome bonus strategy (Feature 3)**: Which cards to apply for based on one-time bonus value, minus opportunity cost of concentrating spend during the qualification window and the hard-pull credit impact. Separate optimization problem.
- **Bookkeeping app integration**: Replace manual spending input with actuals from the bookkeeping app's transaction categorizer. This is the most durable moat once both tools are independently working.
- **Saved profiles**: Semi-annual re-use would benefit from a persisted spending profile that the user updates rather than re-enters. Requires minimal auth (email + magic link would suffice). Deferred because auth introduces flows that dwarf the PoC.
- **Community-contributed card data**: The card database schema is designed with `last_verified_date`, `source`, and `override_notes` fields from day one, enabling a future contribution workflow where users can submit corrections and flag stale data.
- **SEO content strategy**: 5–10 pages answering specific Canadian combination questions ("best credit card combo for Costco + groceries + gas in Canada") that no affiliate site will write honestly. Each page embeds the optimizer. Phase 2.
- **Affiliate revenue (additive, not structural)**: If the tool achieves community credibility, a non-ranking "apply here" link could generate referral revenue without changing the optimization output. This requires issuer relationships and is strictly Phase 2.
- **B2B2C / white-label**: The optimization engine licensed to a financial advisor, robo-advisor, or bank as an embedded feature. Phase 3.
- **Expansion to banking/broker/utility comparisons**: The data model and plugin architecture support future product categories without migration. No features are built.
- **Configurable max card count**: "Recommend at most N cards" for users who want to limit hard-pull credit impact from applications. Deferred; annual fees do natural pruning in the PoC.
- **Open banking integration**: If Consumer-Driven Banking (Royal Assent 2024, implementation phased) delivers API access to transaction data, the spending input form can be replaced by a bank feed. Build toward this by keeping the spending profile as a data model, not a form model.
