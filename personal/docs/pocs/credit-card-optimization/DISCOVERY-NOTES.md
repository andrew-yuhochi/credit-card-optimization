# Discovery Notes — Credit Card Optimization

> **Date**: 2026-04-15
> **Status**: Confirmed by User

## User's Own Words
"I am a very active credit card user, and I always want to optimize my rewards by applying and using the best set of credit cards. However, I found that NONE of the online tools provide an analysis that matches my expense behavior. Either they recommend the 1-for-all 'best' credit card assuming a 'standard' household expense, or they simply compare the reward of a single category to other cards. The first one only benefits the 'lazy' consumers with 'standard' expense behavior. The second one ignores the fact that different credit cards have their own terms and conditions, such as monthly reward limits, retailer classifications, etc."

## Problem & Motivation
Existing Canadian credit card comparison tools fail in two ways:
1. **One-size-fits-all recommendations** — assume "standard" household spending, which doesn't match any real household
2. **Single-category comparisons** — ignore the reality that cards have reward caps, store-specific classifications, acceptance limitations, and annual fees that interact across your full spending profile

The user wants a tool that optimizes across a **combination** of cards against **actual spending behavior**, respecting all real-world constraints.

## Current Solution
Manual research — reading comparison sites, credit card forums, and card T&Cs. Time-consuming and impossible to do holistically across all cards × all categories × all constraints.

## Success Criteria (user-defined)
- The tool covers the **full Canadian credit card market** (not a curated subset)
- Given a user's spending profile, it recommends the **optimal combination of cards** with a clear breakdown of which card to use where and how much reward to expect
- The recommendation accounts for real-world constraints: store classifications, reward caps, card acceptance, annual fees, and approval requirements
- A spreadsheet export shows calculation details for debugging and transparency
- A web page presents the actionable recommendation

## Desired Workflow
- User sits down (roughly semi-annually) when considering their credit card strategy
- Inputs monthly spending by category and specific stores
- Configures personal settings: Amex consideration, credit score/income range, couple mode, Chexy usage for rent
- Optionally adds dummy cards with custom reward percentages (for foreign cards, etc.)
- Receives an optimized card combination recommendation on a web page
- Can export a detailed spreadsheet for verification

## Scope Preferences
### Must Have (PoC)
- **Feature 1: Optimized card combo recommendation**
  - Manual input of monthly spending by category and specific stores
  - Full Canadian credit card market coverage
  - Optimization across any number of cards (annual fees naturally constrain the set)
  - Couple/dual cardholder support with **separate credit score/income eligibility per person**
  - Store-level classification handling (e.g., Costco coded as wholesale/distributor, not grocery) — focus on commonly misunderstood stores
  - Store-specific card acceptance (e.g., Costco only accepts Mastercard)
  - Store-specific credit cards (Canadian Tire, Superstore, Rogers, etc.)
  - Monthly reward caps per card/category
  - Approval requirements filtering (credit score + income range) — real data where available, assumptions where not
  - Annual fees factored into net reward calculation
  - Amex consideration toggle
  - Chexy rent payment consideration
  - **Dummy card feature**: user can add custom cards with manually set reward percentages per category/store (for foreign cards — user handles FX math themselves)
- **Output columns**: Category/Store → Assigned Card → Estimated Expense → Reward % → Expected Reward ($)
- **Web page** for the actionable recommendation
- **Spreadsheet export** with calculation details for every considered combo (debugging/transparency)

### Must Have (PoC) — Second Priority
- **Feature 2: Delta calculator (current vs. recommended comparison)**
  - User inputs their current card holdings (multi-select from card database)
  - Tool runs the optimizer twice: once constrained to current cards, once unconstrained
  - Output shows the delta: "Your current setup earns $X/year; the optimized setup earns $Y/year — a $Z improvement"
  - This is the primary conversion hook for community launch and the key shareability metric
  - Reclassified from "Nice to Have" to "Must Have" based on market research finding: the delta number is the only figure that converts casual visitors and enables the Reddit launch strategy

### Nice to Have (Future Features, Documented)
- **Feature 3**: Welcome bonus strategy — which cards to apply for based on bonus value minus opportunity cost (bonus requirement, normal expense coverage, lost rewards from concentrating spend)
- Configurable card count limits (1, 3, 5, unlimited) — due to hard pull impact on credit score
- Connection to bookkeeping app for actual spending data (replacing manual input)
- Monthly automated data refresh for card terms
- Expansion to banking/broker account and utility offer comparisons

### Explicitly Out of Scope
- Welcome bonus factored into the ongoing optimization (it's a separate strategy)
- Bank feed / Plaid integration
- Multi-user auth, billing, landing page
- FX charge calculations for foreign cards (user handles this via dummy card feature)
- Automated statement parsing (that's the bookkeeping app's job)

## Data Sources & Preferences
- **Credit card data**: No existing data source. Research needed for APIs, databases, or web scraping approaches to cover the full Canadian market (reward structures, T&Cs, caps, classifications, fees, approval requirements).
- **Store classification data**: Research needed for commonly misclassified stores in Canada (e.g., Costco, Walmart, etc.) and how different card networks classify them.
- **Spending input**: Manual entry by the user for PoC.
- **Card data updates**: Manual for PoC; monthly automated refresh as a future goal.

## Output Preferences
- **Primary**: Web page with actionable recommendation table
- **Secondary**: Spreadsheet export (CSV/Excel) with full calculation details for every considered combo
- **Frequency of use**: Semi-annually (roughly)

## Constraints
- PoC is "smallest useful commercial product, used by me first"
- User wants market research on commercial viability before heavy investment
- Credit card data sourcing is a key unknown — may require significant manual research or web scraping
- Multi-tenant architecture from day one (per CLAUDE.md PoC framing)
- The broader vision includes connecting this to the bookkeeping app and expanding to other financial product comparisons

## Open Questions
1. What is the best data source for comprehensive Canadian credit card terms and conditions?
2. How do we obtain store-level merchant category code (MCC) classification data, especially for commonly misunderstood stores?
3. What optimization algorithm is appropriate for the card combination problem (combinatorial optimization with constraints)?
4. How do different card issuers classify the same store differently? How widespread is this problem?
5. What credit score/income thresholds do Canadian card issuers use, and how reliably can we source this data?
6. How does Chexy work mechanically — what reward rates apply when paying rent through it?
7. What store-specific credit cards exist in the Canadian market and how do their rewards compare to general-purpose cards?

## Conversation Summary
The user is an active credit card optimizer frustrated by the lack of tools that analyze card combinations against real spending behavior with real-world constraints. The PoC will cover the full Canadian credit card market, accept manual spending input, and recommend the optimal card combination while respecting store classifications, reward caps, card acceptance limitations, annual fees, and approval requirements. The tool supports couples with separate eligibility profiles and allows dummy cards for foreign credit cards. Output is a web page with an actionable spending guide plus a spreadsheet export for transparency. The commercial vision extends to banking/broker/utility comparisons and integration with the user's bookkeeping app, but PoC scope is tightly focused on Feature 1 (optimized combo recommendation).
