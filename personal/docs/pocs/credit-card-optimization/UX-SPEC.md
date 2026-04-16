# UX Specification — Credit Card Optimization

> **Date**: 2026-04-15
> **Designer**: ux-designer (subagent)
> **Status**: Draft
> **Related docs**: DISCOVERY-NOTES.md
> **Project UX surface type**: Web App (multi-step form + results page) + Spreadsheet export

---

## Executive Summary

The user sits down roughly twice a year to decide their credit card strategy. They arrive at this tool knowing their approximate spending by category and store, and they leave with a ranked assignment table — "use Card X at Costco, Card Y for groceries, Card Z for everything else" — plus a spreadsheet they can audit if the math feels wrong. The two UX decisions that shape the entire product are: (1) the spending input form must handle a large number of categories and specific stores without feeling like a data-entry chore, which points toward a collapsed-section structure with smart pre-population; and (2) the results page has exactly one job — the assignment table — and everything else on that page must serve it or be absent.

---

## User Workflow Summary

### Current Workflow (without this tool)

1. Sit down with a vague awareness that card terms have changed or spending patterns have shifted.
2. Open 3–5 browser tabs: credit card comparison sites (e.g., Ratehub, Milesopedia), Reddit threads (r/PersonalFinanceCanada), individual card issuer pages.
3. Recall approximate monthly spending by category from memory or bank statements.
4. Manually cross-reference: Does this card have a reward cap? How does it classify Costco? Does it accept Amex at the stores I use?
5. Realize the comparison sites don't account for store-level classifications or caps — they use generic category rates.
6. Dig into card T&Cs PDFs for specific stores.
7. Try to hold the cross-product in working memory: Card A is better for groceries but Card B wins on gas after the cap, and Card C has the annual fee that wipes the advantage...
8. Give up on holistic optimization and either stick with the current setup or make a gut-feel switch.
9. Spend another 30–60 minutes of uncertainty about whether the decision was right.

### Desired Workflow (with this tool)

1. Open the tool. The input form is ready — no login, no prior state needed (semi-annual use).
2. Work through the spending input section: enter monthly amounts for pre-populated categories, add specific stores with amounts, skip categories that don't apply.
3. Configure personal settings: toggle Amex consideration, set credit score and income band, toggle couple mode (adds a second eligibility profile), toggle Chexy for rent.
4. Optionally add one or more dummy cards with custom reward rates per category.
5. Click "Optimize" — wait for results (a few seconds is fine for a PoC).
6. Read the results page: primary table shows the card-to-category/store assignment and expected monthly reward. A summary banner at the top shows total monthly reward and annual net reward after fees.
7. If the numbers look surprising, click "Export Spreadsheet" to audit the calculation detail.
8. Make the credit card decision with confidence.

### Friction Points Resolved

| # | Friction Today | What the Tool Removes |
|---|---|---|
| 1 | Can't see the card-combination problem holistically — must hold it in working memory | The optimizer does the combinatorial math; user sees only the output |
| 2 | Comparison sites ignore store-level MCC classifications | Tool embeds the classification data; user inputs the store name, not the MCC |
| 3 | Reward caps require reading T&Cs for each card | Caps are in the card database; optimizer accounts for them automatically |
| 4 | No way to model couples with different eligibility | Couple mode provides a second eligibility profile inline |
| 5 | Foreign card analysis requires doing FX math separately | Dummy card feature lets user encode net rates directly |
| 6 | Can't verify whether a recommendation is trustworthy | Spreadsheet export exposes full calculation detail for every assignment |
| 7 | Semi-annual research takes 1–2 hours with no durable output | One session produces a saved assignment table and spreadsheet |

---

## Jobs-to-Be-Done

1. **Encode my actual spending** — Input what I really spend at which stores and categories, not a generic profile, so the recommendation reflects my life.
2. **Find the card combination that maximizes my net reward** — Not the "best single card" and not a category-by-category comparison, but the optimal multi-card assignment across my full spending profile.
3. **Trust the recommendation enough to act on it** — The math is hidden from me during optimization; I need a way to verify it after, so I can apply for or keep the right cards with confidence.
4. **Model my household, not just myself** — If I have a partner, I need one recommendation that accounts for two different eligibility profiles and shared spending.
5. **Include cards that don't exist in any comparison database** — Add a custom card (e.g., a US card I hold) with rates I know, and have it compete fairly.

---

## Information Architecture

### Surface Inventory

| Surface | Purpose | Primary Question It Answers |
|---|---|---|
| Input Form — Spending Section | Collect monthly spend by category and specific store | "Where does my money actually go each month?" |
| Input Form — Settings Panel | Collect eligibility and personal constraints | "Which cards am I actually eligible for and willing to use?" |
| Input Form — Dummy Cards Panel | Collect custom card definitions | "How do I tell the tool about a card it doesn't know?" |
| Results Page — Summary Banner | Show the headline outcome | "Is this meaningfully better than what I have?" |
| Results Page — Assignment Table | Show the per-category/store card assignment | "Which card do I use where, and what do I earn?" |
| Results Page — Card Summary Panel | Show cards selected and their net annual cost/benefit | "Which cards make the cut, and do the fees justify them?" |
| Spreadsheet Export | Show full calculation detail | "Why did the optimizer assign this card here?" |

The tool has **two pages**: an Input Page and a Results Page. There is no navigation between them during a session — the user moves forward (Input → Results) and can go back (Results → Input to adjust). There is no persistent state between sessions — the tool is stateless from the user's perspective, which matches the semi-annual usage pattern.

### Navigation Model

```
[Input Page] ──── "Optimize" button ──── [Results Page]
                                              │
                                         "Back / Adjust"
                                              │
                                         [Input Page]
                                         (form re-populated
                                          from last run)
                                              │
                                    "Export Spreadsheet" ──── [.xlsx download]
```

The "Back / Adjust" path must re-populate the input form with the values from the last run. The user should not have to re-enter all their spending data because they want to test a setting change. Form state must survive the round trip.

### Reading Order / Visual Hierarchy

**Input Page:**
1. Page heading and one-sentence purpose statement (what the tool does, for a user who hasn't used it in 6 months)
2. Spending Section (largest section, at the top — it's the primary input)
3. Settings Panel (below spending, collapsed by default — expands on click)
4. Dummy Cards Panel (below settings, collapsed by default — clearly optional)
5. "Optimize" CTA button (sticky footer or prominent fixed position)

**Results Page:**
1. Summary banner (total monthly reward, annual net reward after all fees) — the headline number
2. "What NOT to do" callout — only if a commonly used card has been displaced (e.g., "Your current card at Costco earns less than the recommended one")
3. Assignment table (the core output) — full width
4. Card summary panel (which cards are in the recommended set, fee vs. reward per card)
5. "Export Spreadsheet" button
6. "Adjust inputs" link back to the input form

---

## Interaction Specification

### Touchpoint 1: Spending Input — Category Rows

- **Trigger**: User lands on the Input Page for the first time, or returns after a Results page "Adjust" action.
- **Input**: Monthly spend amount (in CAD) per spending category.
- **System response**: A pre-populated list of spending categories is shown as rows with a text/number input field next to each. Categories with no amount entered are treated as $0 (zero, not missing — the optimizer can still route $0 categories, it just won't matter). The list is organized into logical groups (see IA note below).
- **Affordances**:
  - Each row has a label (category name), a dollar input field, and a small help icon. Hovering the help icon shows a tooltip clarifying what counts as this category (e.g., "Groceries — includes most Canadian supermarkets; excludes Costco and Walmart, which are classified differently by most card networks").
  - Dollar fields accept numeric input only; formatted as currency on blur.
  - "Skip all" link per group collapses/zeroes the group if the user doesn't have that spend type.
  - The category list is not editable — these are the fixed optimization inputs. (Store-level entries are handled in the next touchpoint.)
- **Edge cases**:
  - User enters a non-numeric value: field turns red with inline message "Enter a dollar amount (e.g., 200)".
  - User enters a very large number (e.g., $50,000/month groceries): no error, but the optimizer will use it. The system trusts the user's input.
- **Exit state**: Every relevant category has an amount or is implicitly $0.

**Pre-populated category list (organized by group):**

```
EVERYDAY SPENDING
  Groceries (supermarkets)
  Gas & EV charging
  Dining & restaurants
  Coffee shops

RECURRING BILLS
  Streaming services
  Phone & internet / wireless
  Utilities (hydro, gas, water)
  Rent / mortgage (Chexy-eligible if toggled)
  Insurance premiums
  Transit / commute

SHOPPING
  Amazon (online shopping — classified as general retail by most cards)
  Drugstore / pharmacy
  Clothing & department stores
  Home improvement (Home Depot, Canadian Tire goods)

TRAVEL
  Flights
  Hotels
  Car rentals
  Foreign currency spend

OTHER
  Everything else (catch-all)
```

**Commonly misunderstood stores section** (within or adjacent to the above): a separate sub-section or call-out within Everyday Spending, labeled "Stores with non-obvious classifications." This surfaces the stores the user is most likely to get wrong:

```
STORES WITH NON-OBVIOUS CLASSIFICATIONS
  Costco (classified as Wholesale/Warehouse, not Grocery — Mastercard only)
  Walmart (classified as General Merchandise, not Grocery — by most cards)
  Canadian Tire (can be classified as Auto, Home, or General — varies by card)
  Loblaws / PC stores (may qualify for PC Optimum card bonus)
  Shoppers Drug Mart (pharmacy classification varies)
  Amazon Canada (online retail, not physical retail category)
  LCBO / Beer Store (liquor — often a separate category)
  Lowe's / Reno-Depot (home improvement, not grocery)
```

The user enters their monthly spend at each of these stores. The system applies the correct MCC classification per card network. This is the key insight the tool provides that no comparison site does.

### Touchpoint 2: Spending Input — Custom Store Entry

- **Trigger**: User wants to enter a store not in the pre-populated list.
- **Input**: Store name (text) and monthly spend amount.
- **System response**: An "+ Add a store" button at the bottom of the spending section opens an inline row with a free-text store name field and a dollar amount field. The system looks up the store's MCC classification from its database; if found, a small tag appears next to the store name ("Classified as: Grocery"); if not found, a warning tag appears ("Classification unknown — will use 'General retail'") with a note that the user can override.
- **Affordances**:
  - Store name field has autocomplete from the card database. Selecting a match populates the classification automatically.
  - If no match: user can still submit; the store is treated as "General retail" category.
  - Override link: "Change classification" opens a small dropdown with category options (Grocery, Gas, Dining, etc.) — this is the expert affordance for power users.
  - Multiple custom stores can be added; each becomes its own row.
  - Any custom row can be deleted with an "x" button on the row.
- **Edge cases**:
  - User enters a store name that the system has a known misclassification for (e.g., types "Costco" in the custom field): "This store is already in the Stores with Non-Obvious Classifications section — we've handled its classification for you."
  - User adds 20+ custom stores: the list scrolls; there is no hard cap.
- **Exit state**: All relevant stores are in the spending input with amounts and resolved classifications.

### Touchpoint 3: Settings Panel

- **Trigger**: User clicks "Settings" or the collapsed Settings section header.
- **Input**: Personal eligibility and preference configuration.
- **System response**: Panel expands to reveal settings. Settings are organized in logical sub-groups.
- **Affordances and fields**:

```
CARD ACCEPTANCE
  [ ] Include Amex cards in recommendations
      (unchecked by default — many stores don't accept Amex)

ELIGIBILITY — PERSON 1
  Credit score band: [dropdown]
      < 660 (Fair) | 660–724 (Good) | 725–759 (Very Good) | 760+ (Excellent)
  Annual income: [dropdown]
      < $40K | $40K–$60K | $60K–$80K | $80K–$100K | $100K–$150K | $150K+ 

COUPLE MODE
  [ ] We are a couple — optimize for two cardholders
      When checked, reveals:
  ELIGIBILITY — PERSON 2
    Credit score band: [same dropdown]
    Annual income: [same dropdown]
    Note: "Cards requiring both applicants' income will use combined household income."

RENT
  [ ] I pay rent and want to factor in Chexy
      When checked, reveals:
    Monthly rent: [number field, CAD]
    Note: "Chexy enables credit card payments for rent. The Chexy fee applies and 
    is factored into net reward calculations."
```

- **Edge cases**:
  - User sets very low credit score (< 660) + low income: results page should note that most premium cards are not available, and the recommendation set will be limited. This is not an error — it's correct behavior.
  - Couple mode with two very different eligibility profiles: the optimizer uses the more restrictive profile for cards that require both cardholders to qualify, and the individual profile for cards where one person holds the card.
- **Exit state**: Eligibility constraints and preference toggles are set.

### Touchpoint 4: Dummy Cards Panel

- **Trigger**: User clicks "Dummy Cards" or the collapsed Dummy Cards section header. Default: collapsed, labeled "Add a custom or foreign card."
- **Input**: Card name, and reward percentages per category.
- **System response**: Panel expands with an explanation: "Use this to add a card not in our database — for example, a US card you hold. Enter the reward rate you'll earn at each category after any FX fees you've already calculated."
- **Affordances**:
  - "+ Add dummy card" button opens a card definition form:
    - Card name (text, required — e.g., "Chase Sapphire Preferred (USD)")
    - Annual fee in CAD (number, optional — defaults to $0)
    - Per-category reward %: a condensed version of the category list, each with a % input field. Categories not filled in default to the card's base rate.
    - Base rate % field (applied to all categories where no specific rate is set)
  - Multiple dummy cards can be added.
  - Each dummy card has a delete button.
  - Dummy cards appear in the optimizer as peers of real cards — no special treatment in output.
- **Edge cases**:
  - User doesn't fill in any specific category rates, only a base rate: the card is treated as a flat-rate card at that base rate everywhere.
  - User sets a category rate of 0%: that card won't be assigned to that category unless it's still the best option (which would only happen if all other cards are also 0% — unlikely).
  - User adds a dummy card with the same name as a real card in the database: a warning appears — "A card named 'Visa Infinite' already exists in our database. Did you mean to add a custom variant? Consider a more specific name."
- **Exit state**: All custom cards are defined with rates. The user understands they are competing in the optimization on equal footing.

### Touchpoint 5: Optimization Run

- **Trigger**: User clicks the "Optimize" button.
- **Input**: (none — all inputs collected already)
- **System response**:
  1. Basic validation: are any spending amounts entered? If all amounts are $0, show an inline error at the top of the spending section: "Enter at least one spending amount to get a recommendation."
  2. If valid: a loading state replaces the button. A simple progress message appears: "Analyzing [N] cards against your spending profile..." No spinner needed — a brief text update is sufficient for a tool used semi-annually.
  3. On completion: the page navigates to the Results Page. The Input Page state is preserved in session memory for "Back / Adjust."
- **Edge cases**:
  - Optimization takes longer than 10 seconds: show a message "This is taking a little longer than usual — still working..." Do not time out within 60 seconds.
  - Error during optimization (backend failure): show a full-page error state (see Error States section).
- **Exit state**: User is on the Results Page.

### Touchpoint 6: Results Page — Assignment Table

- **Trigger**: Arriving on the Results Page after a successful optimization run.
- **Input**: (none — read-only results page)
- **System response**: The results page loads with:

  1. **Summary banner** (top): "Your optimized setup earns an estimated **$X/month** in rewards — **$Y/year** net of all annual fees." Where X and Y are the optimizer's output figures.
  2. **Assignment table** (main content): One row per category/store that had a non-zero spend amount. Columns exactly as specified by the user:

  | Category / Store | Assigned Card | Estimated Monthly Expense | Reward % | Expected Monthly Reward ($) |
  |---|---|---|---|---|
  | Groceries | TD First Class Travel | $400 | 3.0% | $12.00 |
  | Costco | Scotiabank Gold Amex | $300 | 4.0% | $12.00 |
  | Gas | Scotiabank Gold Amex | $150 | 4.0% | $6.00 |
  | ... | ... | ... | ... | ... |
  | **TOTAL** | | **$2,400** | | **$96.00** |

  Rows sorted by Expected Monthly Reward descending — largest dollar impact at top.

  3. **Card summary panel** (below table): One row per card in the recommended set.

  | Card | Annual Fee | Categories Assigned | Est. Annual Reward from My Spending | Net Annual Value |
  |---|---|---|---|---|
  | Scotiabank Gold Amex | $120 | Gas, Costco, Dining | $432 | +$312 |
  | TD First Class Travel | $139 | Groceries, Streaming | $288 | +$149 |
  | Chase Sapphire Preferred (custom) | $0 (CAD) | Travel | $96 | +$96 |

  Cards with negative net annual value do not appear in the recommended set (the optimizer has already excluded them).

  4. **Export button**: "Export calculation spreadsheet (.xlsx)" — prominent, below the card summary panel.
  5. **Adjust inputs link**: "Change my spending or settings" — below the export button.

- **Affordances**:
  - The assignment table is sortable by any column header (secondary sort). Default sort is by Expected Monthly Reward descending.
  - Each row in the assignment table has a small expand control: clicking it reveals a one-line explanation — "Why this card?" — e.g., "Scotiabank Gold Amex earns 4% at grocery-coded merchants; Costco is classified as grocery by Scotiabank." This is the transparency affordance that builds trust.
  - Each card name in the table is a static label (no link to issuer site in PoC — that's a Phase 2 feature).
  - Couple mode: if active, each row in the assignment table includes a "Cardholder" column — Person 1 or Person 2 — indicating whose card in the couple should be used.
- **Edge cases**: Addressed in Error States section.
- **Exit state**: User knows which card to use where, and has optionally exported the spreadsheet.

### Touchpoint 7: Spreadsheet Export

- **Trigger**: User clicks "Export calculation spreadsheet (.xlsx)".
- **Input**: (none)
- **System response**: Browser downloads an .xlsx file named `credit-card-optimization-[YYYY-MM-DD].xlsx`. File opens directly in Excel / Google Sheets.
- **Spreadsheet structure** (tabs):
  - Tab 1 — **Summary**: The same assignment table from the web page. This is the "what to do" sheet.
  - Tab 2 — **Calculation Detail**: One row per category/store × card considered combination. Columns: Category/Store | Card | Monthly Spend | Base Rate % | Category Rate % | Cap Applied? | Cap Amount | Effective Rate % | Monthly Reward | Annual Reward | Annual Fee Portion | Net Annual Contribution. This is the debugging sheet — the user can sort and filter to understand why Card A beat Card B for a given category.
  - Tab 3 — **Cards Considered**: Full list of cards the optimizer evaluated, with their key attributes (annual fee, base rate, key category rates, cap amounts, eligibility requirements). This is the reference sheet — "what did the tool know about each card?"
  - Tab 4 — **Input Echo**: The exact spending amounts and settings the user entered for this run. This makes the spreadsheet a self-contained record — the user can pick it up in 6 months and understand what they entered without reopening the tool.
- **Edge cases**:
  - Export fails (backend error): inline error message below the button — "Export failed. Try again or refresh the page."
- **Exit state**: User has a local file with full calculation detail. The web page remains open.

---

## Human-in-the-Loop Patterns

This tool involves optimization with embedded card classification data. The user cannot modify the classification logic directly, but they can override at two points:

### Confidence Surfacing — Store Classifications

When the system assigns a MCC classification to a store (either pre-populated or custom-entered), it should surface its confidence:

- **High confidence** (store is in the database with confirmed classification): no visual indicator — just the classification tag.
- **Inferred classification** (store matched by name but classification may vary by issuer): tag reads "Classified as: Grocery (may vary)" with a help icon explaining that different card networks may classify this store differently.
- **Unknown** (store not in database, defaulting to General retail): yellow warning tag "Classification unknown — using General retail" with an override option.

The "Why this card?" row expansion on the results page is the primary trust-building mechanism. The user should be able to read one sentence that explains every assignment in plain English. If that sentence would be confusing, the UX is broken.

### Correction Flow

The user can override store classifications in the input form (see Touchpoint 2, Override link). There is no correction flow on the results page — if the user disagrees with a classification, they go back to the input form, change the classification, and re-optimize. This is intentional: the results page is read-only. Mixing correction affordances into the results page would make it ambiguous whether the table reflects the current inputs.

### Trust-Building Over Time

This is a semi-annual tool — there is no "over time" trust-building loop within a single session. Trust is built through:

1. **Transparency by default**: The "Why this card?" expansion on every result row.
2. **The spreadsheet**: The detailed calculation tab. A user who audits one recommendation and finds it correct will trust the system for future runs.
3. **Known-store validation**: The pre-populated "Stores with Non-Obvious Classifications" section names the exact stores that comparison sites get wrong. A knowledgeable user recognizes this immediately as evidence the tool understands the domain.

---

## Error & Empty States

### Error States

| Situation | What the user sees | What they can do |
|---|---|---|
| All spending inputs are $0 | Inline error at top of spending section: "Enter at least one spending amount to see a recommendation." | Fill in spending amounts. |
| Backend optimization fails | Full-page error: "Something went wrong during optimization. Your inputs have been saved — click Retry to try again, or go back and adjust your inputs." Retry button + Back link. | Retry or adjust. |
| Spreadsheet export fails | Inline error below the export button: "Export failed. Try again or refresh the page." | Retry export. |
| No cards are eligible given credit score / income constraints | Results page loads but assignment table shows a single note row: "No cards in our database match your eligibility profile. Consider checking your credit score band or income range in Settings, or use a dummy card to model a card you know you qualify for." Summary banner shows $0. | Adjust settings or add dummy card. |
| All eligible cards are beaten by a simple cash-back baseline | Results page loads normally. The summary banner includes a secondary line in muted text: "Note: A 2% flat cash-back card would earn approximately $X/month from your spending. The recommended set earns $Y/month — a difference of $Z/month." The user sees the margin explicitly. If Z is negative (no card beats 2% flat), a warning banner replaces the summary: "The cards available to you don't beat a 2% flat cash-back card given your spending profile. See the card summary panel for details." | Review card summary, adjust settings, or add dummy cards. |
| Couple mode: Person 2's eligibility disqualifies a card Person 1 could hold individually | No error — the optimizer silently assigns cards correctly per person. The "Cardholder" column in the assignment table makes this visible. | No action needed; result is already correct. |

### Empty States

**First load (no prior session):** The spending input section is pre-populated with all categories showing $0 in input fields. There is a one-line instruction above the first group: "Enter your typical monthly spending in each category. Leave categories at $0 if they don't apply to you." This eliminates ambiguity about whether blank = skip or blank = error.

The Settings and Dummy Cards panels are collapsed with a short label explaining what's inside — the user who doesn't need them never opens them.

### Success / Completion States

The results page IS the success state. There is no separate "done" confirmation. The user knows they're done when:

1. The summary banner shows a non-zero annual net reward figure.
2. The assignment table has one row per spending category/store with a non-zero amount.
3. The "Export" button is available.

There is no "save" action. The results exist for the duration of the browser session. If the user closes the tab, results are gone. This is acceptable for a semi-annual tool — the spreadsheet export is the persistence mechanism.

---

## What NOT to Build

The following features are tempting adjacencies that must stay out of the PoC:

1. **Saved profiles / user accounts**: The user identified this tool as semi-annual and explicitly out-of-scope for auth. Adding a "save my spending profile" feature introduces auth, data storage, and password-reset flows that dwarf the PoC effort. The "Input Echo" tab in the spreadsheet is the persistence mechanism — the user can paste their old inputs back in.

2. **Welcome bonus calculator**: This is explicitly Feature 3 in the backlog. Showing welcome bonuses on the results page or in the card summary panel introduces a different optimization problem (one-time vs. ongoing value) that muddies the primary output. Keep the results page about ongoing reward rates only.

3. **Side-by-side "current setup vs. recommended" comparison**: This is explicitly Feature 2 in the backlog. It requires the user to enter their current card setup, which doubles the input surface. Exclude entirely from PoC. The summary banner's "you earn $X/month" is the implicit comparison — the user knows what they currently earn.

4. **Card count limit toggle**: This is in the Nice-to-Have backlog. The PoC optimizer lets annual fees do the pruning naturally. Adding a "recommend at most 3 cards" constraint is a UI control that requires a settings field, optimizer constraint logic, and an explanation. Defer to Phase 2.

5. **External links to card application pages**: One-click "Apply Now" links on the results page feel useful but introduce maintenance overhead (URLs change), affiliate tracking questions, and distract from the core job. The user's job is to make the decision; the application is trivially easy once decided.

---

## Accessibility & Ergonomics

This is a single-user PoC. The handful of accessibility considerations that matter:

1. **Keyboard navigation**: The spending input form has many fields. Tab order should follow reading order (top to bottom, left to right within groups). Users who are fast typists should be able to complete the form without touching a mouse.

2. **Colour-blind-safe palette**: The results page uses colors only in the card summary panel (for quick scanning). Do not use red/green alone to distinguish positive/negative net value — use red/green + icon (+ / -) + text label. This covers the most common colour blindness (red-green).

3. **Number formatting**: All currency fields should display with two decimal places and a dollar sign on blur (e.g., "400" becomes "$400.00"). Percentage fields should display with one decimal place and a % sign (e.g., "3" becomes "3.0%"). This reduces misreading.

4. **Mobile**: This is a semi-annual, deliberate-session tool. Mobile is not the primary context. The input form is table-like and does not translate well to narrow screens. No special mobile optimization required for PoC — but the layout should not break catastrophically on a tablet (responsive enough to be functional, not beautiful).

5. **Form length management**: The full spending input list is long. Use accordion-style group headers that can collapse. A user who has no travel spend should be able to collapse the Travel group and reduce visual noise. This is the primary ergonomic concern with the input form.

---

## Wireframes / Structural Sketches

### Input Page

```
+------------------------------------------------------------------+
| Credit Card Optimizer                          [Settings] [?]    |
+------------------------------------------------------------------+
| Enter your monthly spending to find your optimal card setup.     |
| All amounts in CAD. Leave categories at $0 if they don't apply.  |
+------------------------------------------------------------------+

  EVERYDAY SPENDING                                    [collapse v]
  +--------------------------+-------------------+
  | Groceries (supermarkets) |  $  [______400__] |
  | Gas & EV charging        |  $  [______150__] |
  | Dining & restaurants     |  $  [______300__] |
  | Coffee shops             |  $  [_______50__] |
  +--------------------------+-------------------+

  STORES WITH NON-OBVIOUS CLASSIFICATIONS     [? why this section]
  +--------------------------+-------------------+
  | Costco                   |  $  [______300__] |   [i] Mastercard only • Wholesale rate
  | Walmart                  |  $  [_______80__] |   [i] General merchandise rate
  | Shoppers Drug Mart        |  $  [_______40__] |   [i] Pharmacy rate (varies by card)
  | Amazon Canada            |  $  [______100__] |   [i] Online retail rate
  | Canadian Tire            |  $  [_______60__] |   [i] Rate varies by card
  | LCBO / Beer Store        |  $  [________0__] |
  +--------------------------+-------------------+
  [+ Add another store]

  RECURRING BILLS                                      [collapse v]
  ...

  SHOPPING                                             [collapse v]
  ...

  TRAVEL                                               [collapse v]
  ...

  OTHER                                                [collapse v]
  +--------------------------+-------------------+
  | Everything else          |  $  [______200__] |
  +--------------------------+-------------------+

+------------------------------------------------------------------+
|  [v] SETTINGS                                                    |
|     [ ] Include Amex cards                                       |
|     Credit score:   [Excellent (760+)          v]               |
|     Annual income:  [$100K–$150K               v]               |
|     [ ] Couple mode                                              |
|     [ ] I pay rent via Chexy                                     |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  [v] ADD A CUSTOM CARD  (optional)                              |
|     For cards not in our database (e.g., US or foreign cards)   |
|     [+ Add dummy card]                                           |
+------------------------------------------------------------------+

                              [ OPTIMIZE MY CARD SETUP  >> ]
```

### Results Page

```
+------------------------------------------------------------------+
| < Adjust my inputs                                               |
+------------------------------------------------------------------+
|                                                                  |
|  Your optimized setup earns $96/month — $852/year net of fees.  |
|                                                                  |
|  Note: a 2% flat cash-back card would earn ~$48/month.          |
|  Your recommended setup earns $48/month more.                   |
+------------------------------------------------------------------+

  YOUR SPENDING ASSIGNMENT                    [sort by: Reward $ v]
  +------------------+------------------+----------+--------+--------+
  | Category / Store | Card             | Expense  | Rate   | Reward |
  +------------------+------------------+----------+--------+--------+
  | Dining           | Scotiabank Gold  | $300     | 5.0%   | $15.00 |  [>]
  | Costco           | Cibc Dividend    | $300     | 4.0%   | $12.00 |  [>]
  | Groceries        | TD First Class   | $400     | 3.0%   | $12.00 |  [>]
  | Gas              | Scotiabank Gold  | $150     | 4.0%   | $6.00  |  [>]
  | ...              | ...              | ...      | ...    | ...    |
  +------------------+------------------+----------+--------+--------+
  | TOTAL            |                  | $2,400   |        | $96.00 |
  +------------------+------------------+----------+--------+--------+

  [>] expanded row:
  +------------------------------------------------------------------+
  | Why Scotiabank Gold Amex for Dining?                             |
  | Scotiabank Gold Amex earns 5% at restaurants. Your dining spend  |
  | of $300/month earns $15/month before the monthly cap of $200 in  |
  | rewards is reached. No other eligible card beats this rate for   |
  | this category.                                                   |
  +------------------------------------------------------------------+

  CARDS IN YOUR RECOMMENDED SET
  +------------------------+--------+-------------------+--------+----------+
  | Card                   | Fee    | Assigned to       | Reward | Net/Year |
  +------------------------+--------+-------------------+--------+----------+
  | Scotiabank Gold Amex   | $120   | Dining, Gas, ...  | $372   | +$252    |
  | TD First Class Travel  | $139   | Groceries, ...    | $288   | +$149    |
  | CIBC Dividend Visa Inf | $120   | Costco, ...       | $240   | +$120    |
  +------------------------+--------+-------------------+--------+----------+

        [ EXPORT CALCULATION SPREADSHEET (.xlsx) ]

        [ < Change my spending or settings ]
```

### Spreadsheet — Tab Structure

```
[Summary] [Calculation Detail] [Cards Considered] [Input Echo]
   ^              ^                    ^                ^
 "What         "Why did          "What did the      "What did
 to use"      it pick X?"       tool know?"       I enter?"
```

---

## Open UX Questions

The following questions were not resolved in the discovery notes and should be answered before implementation begins:

1. **Session persistence**: Should the input form remember values from the previous run (e.g., via localStorage) so the user doesn't re-enter everything on the next semi-annual session? The discovery notes imply stateless ("no auth, no accounts"), but lightweight localStorage persistence would dramatically improve the semi-annual re-use experience. This is a UX-significant question, not purely a technical one.

2. **Couple mode — shared vs. per-person spending**: In couple mode, does the spending input represent combined household spending, or does the user need to split spending per person? The recommendation engine needs to know, because card eligibility is per person. The simplest UX is: enter combined household spending, and the optimizer assigns the cardholder per assignment row. But if Person 1 and Person 2 go to different stores, that model breaks. Needs a decision.

3. **Chexy mechanics — what the tool needs to know**: The discovery notes ask how Chexy works mechanically. The UX impact: does the user need to enter the Chexy fee separately, or does the tool know it and factor it in? This determines whether the Chexy toggle reveals a fee override field or is purely a classification toggle.

4. **Store-specific cards (Canadian Tire, PC Optimum, etc.)**: These are mentioned in scope. In the input form, are these cards in the "Assigned Card" column of the results table like any other card? Or do they get a separate treatment (e.g., "also use your PC Optimum card at Loblaws in addition to your main card")? The UX implication: stacking rewards from a loyalty card on top of a credit card reward is a different model than card-vs-card assignment. Needs a decision before the results table structure is finalized.

5. **What is the baseline for the "you could earn more" comparison?**: The summary banner compares against "a 2% flat cash-back card." Is 2% the right baseline for a Canadian audience? (Some argue 1.5% is more representative of no-fee cards.) This is a UX-significant choice because it frames the entire value proposition.

6. **Export format preference**: The discovery notes say "CSV/Excel." The UX spec proposes .xlsx with multiple tabs (Summary, Calculation Detail, Cards Considered, Input Echo). Confirm this is the preferred format — multi-tab .xlsx is more useful for debugging but requires Excel or Google Sheets; a single CSV is simpler but loses the tab structure.

---

## Implications for the PRD

- **The "Stores with Non-Obvious Classifications" section is the keystone UX element.** Do not simplify it away. This is the exact problem the user identified with existing tools, stated in their own words. If scope cuts are needed, cut from the Other spending group or the Custom Store Entry autocomplete — not from this section.
- **The "Why this card?" row expansion on the results table is non-negotiable.** Without it, the results page is a black box that the user cannot verify. The spreadsheet is the fallback, but in-line explanation is the primary trust mechanism. It must be part of the v1 results page.
- **The results page is read-only.** Do not add inline editing or "swap card" affordances to the results page. If the user wants to change something, they go back to the input form and re-optimize. This keeps the results page unambiguous and the optimization path clean.
- **Session state must survive the Input → Results → Input round trip.** If the "Adjust inputs" link loses the user's spending data, the tool is broken for practical use. This is a UX requirement, not a nice-to-have.
- **Couple mode is a progressive disclosure pattern, not a separate flow.** Do not create a separate "couple mode" page or wizard. It is a toggle in the Settings panel that reveals a second eligibility form in-place. Keeping it in-place preserves the single-flow structure.
- **The spreadsheet's Input Echo tab is part of the core spec**, not a bonus feature. It is the persistence mechanism that replaces saved profiles and makes the spreadsheet useful 6 months from now. Do not defer it.
- **Do not add card application links, affiliate links, or "see current offer" buttons in the PoC.** These are Phase 2 commercial features and introduce maintenance and trust concerns disproportionate to their PoC value.
