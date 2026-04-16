# Data Source Specification — Credit Card Optimization

> **Status**: Approved
> **Author**: architect
> **Last Updated**: 2026-04-15
> **Depends on**: PRD.md (approved)

---

## Overview

The credit card optimizer has no runtime data sources — all card data is loaded from a static, version-controlled JSON file at application startup. This is a deliberate architectural choice: it avoids runtime API dependencies, makes card data changes a code-review process (auditability), and ensures the tool works completely offline.

The data sources documented here are the **one-time seeding sources** used to build and maintain `data/cards/cards.json`, plus the reference datasets bundled into the repository.

---

## Source 1: PrinceOfTravel — Primary Card Database Seed

| Field | Detail |
|-------|--------|
| **Type** | Web scraping (server-rendered HTML + JSON-LD) |
| **URL** | `https://princeoftravel.com/credit-cards/` + individual card pages |
| **Authentication** | None |
| **Rate Limits** | No documented rate limit; scrape politely (1–2 second delay between requests) |
| **Cost** | Free |
| **Data Format** | HTML with embedded JSON-LD (`FinancialProduct` schema) + prose earn rate descriptions |
| **Update Frequency** | Manual quarterly refresh (PoC) |
| **Reliability** | Medium-High — server-rendered Next.js with SSR; JSON-LD confirmed present; content is editorial and stable |
| **Robots.txt** | No explicit prohibition on card pages; content is editorial |

**Sample JSON-LD (Amex Cobalt, from live page):**

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

**Key Fields We Need:**
- `name`: card display name
- `offers.price`: annual fee in CAD
- Earn rates: parsed from prose text (e.g., "5× Eats & Groceries (up to $2,500/month, 1× after), 3× Streaming") using targeted regex
- First-year fee: parsed from prose or JSON-LD `description`
- Welcome bonus: parsed from `description` (for reference; not used in optimizer)

**Coverage:**
- ~100–150 major Canadian credit cards with emphasis on travel and premium cards
- Skews toward Amex, Aeroplan, and travel rewards products; weaker on no-fee and cash-back cards
- Does not cover all 235 cards in the CreditCardGenius sitemap — supplementation from issuer pages is required for cash-back and co-branded cards

**Known Limitations:**
- Monthly reward caps are described in prose and require careful regex parsing — not in structured JSON-LD
- Store-specific classification overrides are not documented on these pages; must be sourced separately from issuer T&Cs and community knowledge
- Annual fee may differ from current issuer page if PrinceOfTravel has not updated recently
- Coverage of no-fee and entry-level cards is incomplete

**Fallback Strategy:**
If PrinceOfTravel changes its HTML structure and the scraper breaks, fall back to issuer pages directly (Source 4) for the affected cards. The static JSON database means a scraper failure has no runtime impact — it only affects the next quarterly manual refresh.

**Scraping Approach (one-time seed, `scripts/seed_cards.py`):**
- `httpx` + `BeautifulSoup4` for server-rendered pages (no browser automation needed for PrinceOfTravel)
- Extract JSON-LD block first
- Parse earn rates from the page body text using regex patterns for "X× Category", "X% on Category", "up to $Y/month"
- Output: one draft JSON record per card, flagged as `"source": "princeoftravel"` with `"last_verified_date"` set to scrape date
- All draft records require human review before merging into `cards.json`

---

## Source 2: Card Issuer Pages — Authoritative Caps and T&C Details

| Field | Detail |
|-------|--------|
| **Type** | Web scraping (static HTML) or manual reading |
| **URLs** | td.com, rbc.com, scotiabank.com, cibc.com, bmo.com, americanexpress.com/ca, pcfinancial.ca, rogersbank.com, canadiantirebank.ca |
| **Authentication** | None (public pages) |
| **Rate Limits** | No documented rate; BMO returns connection refused on automated requests — manual reading only for BMO |
| **Cost** | Free |
| **Data Format** | HTML (server-rendered for TD, Scotiabank, CIBC; partially rendered for RBC, Amex) |
| **Update Frequency** | Manual on-demand (when RFD forum or card issuer announcement signals a change) |
| **Reliability** | Medium — TD, Scotiabank, and CIBC are server-rendered with readable earn rates; BMO and RBC require more effort |

**Sample HTML text (TD First Class Travel Visa Infinite — from live TD page):**
```
Earn 8 TD Rewards Points for every $1 on purchases made through Expedia for TD
Earn 6 TD Rewards Points for every $1 on eligible Groceries and Restaurants
Earn 4 TD Rewards Points for every $1 on regularly recurring bill payments set up on your Card
Earn 2 TD Rewards Points for every $1 on all other purchases
```

**Key Fields We Need:**
- Category earn rates and their exact category definitions (what does "groceries" include for this card?)
- Monthly or annual reward caps (dollar or point amounts)
- Store-specific classification notes (e.g., "excludes warehouse clubs such as Costco")
- Income and credit requirements from the application page
- Annual fee confirmation (source of truth)

**Known Limitations:**
- Formats are inconsistent across issuers — no shared schema
- T&C PDFs linked from card pages contain the authoritative cap language but require PDF parsing or manual reading
- BMO blocks automated requests entirely; all BMO card data must be manually entered
- Some issuers bury the "excludes" language in T&C PDFs, not on the product page

**Fallback Strategy:**
Manual entry from the issuer's card application page and T&C PDF. All manually sourced records are flagged with `"source": "issuer"` and the specific URL in `source_url`. If a URL changes, the `override_notes` field records the redirect history.

---

## Source 3: CreditCardGenius Sitemap — Inventory Reference

| Field | Detail |
|-------|--------|
| **Type** | Sitemap XML (static) + individual card pages via Playwright |
| **URL** | `https://creditcardgenius.ca/sitemaps/cards.xml` (sitemap) |
| **Authentication** | None |
| **Rate Limits** | None documented for sitemap; individual pages require Playwright (Angular SPA) |
| **Cost** | Free |
| **Data Format** | XML (sitemap) + JavaScript-rendered HTML (individual pages) |
| **Update Frequency** | Manual, as needed for coverage gap identification |
| **Reliability** | Low for earn rate data (Angular SPA; earn rates loaded dynamically after JS execution); High as a card inventory list |

**How this source is used:**
CreditCardGenius's sitemap lists 235 individual card pages. This list is used as a **coverage gap checklist** — not as a data source for earn rates. After seeding from PrinceOfTravel and issuer pages, the sitemap identifies cards that have not yet been added to `cards.json`. These are then researched from issuer pages directly.

**Key Cards from Sitemap (sample, used to verify coverage):**
- Amex Aeroplan Reserve
- CIBC Costco Mastercard
- PC Financial World Elite
- RBC British Airways Visa Infinite
- Scotiabank Gold Amex
- Canadian Tire Cash Advantage
- Desjardins Odyssey World Elite

**Known Limitations:**
- Individual card pages are Angular SPAs — earn rates are loaded dynamically and not present in the static HTML. Extracting earn rates requires Playwright (headless Chrome), making this fragile to UI updates.
- robots.txt blocks `/api/` but permits individual card pages — scraping is technically permitted but practically fragile.
- Not used for earn rate data in the PoC; issuer pages are the preferred authoritative source for T&C details.

**Fallback Strategy:**
Use sitemap as a checklist only. If earn rate extraction from CCG pages is needed, use Playwright with a retry/backoff pattern and store results in a staging JSON before merging to `cards.json`. Always verify against issuer pages before merging.

---

## Source 4: greggles/mcc-codes — MCC Reference Database

| Field | Detail |
|-------|--------|
| **Type** | Static JSON file (GitHub repository) |
| **URL** | `https://github.com/greggles/mcc-codes` — file: `mcc-codes.json` |
| **Authentication** | None |
| **Rate Limits** | None (static download or git clone) |
| **Cost** | Free / Public Domain |
| **Data Format** | JSON array |
| **Update Frequency** | Downloaded once; bundled into repository as `data/stores/mcc_codes.json` |
| **Reliability** | High — 981 entries covering full ISO 18245 standard; last updated 2024 |

**Sample records:**
```json
[
  {"mcc": "5411", "combined_description": "Grocery Stores, Supermarkets", "id": 312},
  {"mcc": "5300", "combined_description": "Wholesale Clubs", "id": 284},
  {"mcc": "5310", "combined_description": "Discount Stores", "id": 285},
  {"mcc": "5912", "combined_description": "Drug Stores and Pharmacies", "id": 330},
  {"mcc": "5541", "combined_description": "Service Stations ( with or without ancillary services)", "id": 319},
  {"mcc": "5542", "combined_description": "Automated Fuel Dispensers", "id": 320},
  {"mcc": "5812", "combined_description": "Eating Places and Restaurants", "id": 329},
  {"mcc": "5814", "combined_description": "Fast Food Restaurants", "id": 331},
  {"mcc": "4111", "combined_description": "Local and Suburban Commuter Passenger Transportation, Including Ferries", "id": 152},
  {"mcc": "6051", "combined_description": "Non-Financial Institutions – Foreign Currency, Non-Fiat Currency (for example: Cryptocurrency), Money Orders (Not Money Transfer)", "id": 217},
  {"mcc": "6099", "combined_description": "Financial Institutions – Merchandise and Services", "id": 221}
]
```

**Key Fields We Need:**
- `mcc`: the four-digit MCC code
- `combined_description`: human-readable description, used in UI tooltips and "Why this card?" explanations

**How this source is used:**
- Bundled as `data/stores/mcc_codes.json` at repository setup (one-time download)
- Used by `StoreSlugResolver` to look up the MCC description for any store in the store map
- Used in the UI to display a human-readable classification tag next to each store
- Used in the Calculation Detail spreadsheet tab to document the MCC for each spend bucket

**Known Limitations:**
- MCC codes are network-level classifications; issuer-specific overrides (how Shoppers Drug Mart earns grocery rate on CIBC Dividend) are NOT derivable from this dataset — they require per-card research
- MCC 5300 (Wholesale Clubs = Costco) is the authoritative network classification, but some card issuers explicitly define their own category mapping in their T&Cs (e.g., a card that earns grocery rate on "discount store" purchases would override MCC 5310)
- The file may not include newer MCCs added after its last update; for the PoC's purposes, the 981 existing MCCs cover all relevant Canadian retail categories

**Fallback Strategy:**
No fallback needed — file is bundled in the repository. If the upstream repository goes away, the bundled copy remains valid. The file changes rarely (ISO 18245 standard updates are infrequent).

---

## Source 5: Chexy — Rent Payment Fee Mechanics

| Field | Detail |
|-------|--------|
| **Type** | Manual research (live website) |
| **URL** | `https://chexy.co` |
| **Authentication** | None |
| **Rate Limits** | N/A (no API) |
| **Cost** | Free to research; 1.75% fee charged to the user's card per transaction |
| **Data Format** | Human-readable (website copy) |
| **Update Frequency** | Verified 2026-04-15; re-verify before any public release |
| **Reliability** | High — fee is published on the live website; Chexy has 200K+ users and $1.5B+ processed |

**Confirmed Data (from chexy.co, 2026-04-15):**
- Processing fee: **1.75%** of payment amount, charged to the credit card
- Accepted networks: Visa, Mastercard, and American Express
- Bill types covered: rent, property taxes, utilities, insurance, tuition, childcare, income taxes
- MCC classification: likely 6051 or 6099 (financial services / bill payment) — **not confirmed by any issuer**

**Net Reward Formula (hardcoded in `config/`):**
```
chexy_fee_rate = 0.0175
net_reward_rate = card_other_rate - chexy_fee_rate
break_even_card_rate = 0.0175  (1.75%)
```

Cards that earn net positive on Chexy (earning > 1.75% on "other"):
- Amex Cobalt: 1× MR ≈ 2.0¢/pt → ~2.0% → net +0.25%
- Any card with ≥2% flat cash-back on all purchases

Cards that earn net negative on Chexy:
- Rogers World Elite: 1.5% on all → net -0.25%
- WestJet RBC World Elite: 1.5% WestJet dollars → net -0.25%
- 1% base-rate cards → net -0.75%

**Key Data Encoded in the Application:**
- `CHEXY_FEE_RATE = 0.0175` in `config/valuation.json`
- Chexy bucket is treated as earning `card_other_rate - CHEXY_FEE_RATE` effective rate
- Chexy MCC assumption is documented in the UI and in the Input Echo spreadsheet tab
- Users can read the assumption and override by adding a dummy card with a manually set rate if they have evidence their card earns differently on Chexy transactions

**Known Limitations:**
- Chexy's MCC classification is inferred, not confirmed by any Canadian card issuer. If a card issuer classifies Chexy as a specific category (e.g., utilities) and earns a higher rate, the tool's calculation would understate that card's Chexy value.
- Chexy's fee structure could change. The `chexy_fee_rate` is in `config/valuation.json` (not hardcoded) so it can be updated without a code change.
- Chexy has recently added Mastercard acceptance; the network acceptance list may evolve. The tool's Chexy toggle does not restrict by card network — it applies to all accepted networks (Visa, Mastercard, Amex).

**Fallback Strategy:**
If Chexy changes its fee, update `config/valuation.json`. If Chexy's MCC classification is officially confirmed by an issuer (via a statement example posted on RFD forum, for example), update the `override_notes` field in the affected card records.

---

## Source 6: Community Knowledge — Store Classification Overrides

| Field | Detail |
|-------|--------|
| **Type** | Manual research (RFD forum, card T&Cs, community testing) |
| **URLs** | `redflagdeals.com/forums/`, individual card T&C PDFs from issuer pages |
| **Authentication** | None |
| **Rate Limits** | N/A |
| **Cost** | Free |
| **Data Format** | Forum posts, PDF T&Cs, human-readable |
| **Update Frequency** | Reviewed quarterly; updated on-demand when community reports a change |
| **Reliability** | Medium — community-sourced; reflects real card behavior but may lag behind issuer changes |

**What this source provides:**
The per-card `store_overrides` table in `cards.json` — specifically, the issuer-specific exceptions where a store earns a rate different from its MCC category default. These overrides cannot be derived from any structured data source; they require reading each card's T&C and cross-referencing with community experience reports.

**Key known store classification quirks (pre-seeded):**

| Store | MCC | Default Category | Card-Specific Override |
|-------|-----|------------------|------------------------|
| Costco | 5300 | wholesale | Most cards: 1% "other"; CIBC Costco Mastercard: earns base + Costco cash-back |
| Walmart | 5310 | other | Most cards: 1% "other"; some issuers code Walmart Supercenter as grocery (5411) |
| Walmart Supercenter | 5411 or 5310 | mixed | Terminal-dependent; flag as "may vary" in UI |
| Shoppers Drug Mart | 5912 | pharmacy | CIBC Dividend: earns grocery rate (4%); TD: earns pharmacy rate; Amex: earns grocery on some cards |
| Canadian Tire | 5251 or 5945 | other | Usually "other" on most cards; Canadian Tire Triangle earns 4% |
| Amazon Canada | 5999 or 5045 | other | Coded as general merchandise on most networks; some cards have explicit "online shopping" category |
| Uber Eats | 5812 | dining | Restaurant rate on some cards; "other" on others |
| DoorDash | 5812 | dining | Restaurant rate on Scotia Gold Amex |
| LCBO | 5921 | other | Usually "other" |

**How this data is encoded:**

Each card's `store_overrides` dict maps store slugs to a `StoreOverride` object with `rate`, `source`, and `note` fields. Example:

```json
"store_overrides": {
  "shoppers_drug_mart": {
    "rate": 4.0,
    "source": "community",
    "note": "SDM classified as grocery for CIBC Dividend per card T&C; confirmed on RFD forum 2024-11"
  }
}
```

**Known Limitations:**
- Community data can be wrong. Card issuers do not publish machine-readable store classification tables.
- A single T&C change by an issuer can invalidate multiple override entries without public announcement. RFD forum users typically catch these within 1–4 weeks of a change.
- Some issuers distinguish between "Shoppers Drug Mart" as a grocery (5411) vs. pharmacy (5912) based on what the customer bought — but the MCC is assigned by the merchant's terminal, not the purchase content. This creates ambiguity that cannot be fully resolved in the model.

**Fallback Strategy:**
When classification is uncertain, mark the entry with `"confidence": "low"` and surface the "may vary" tag in the UI. The user can override the classification for a specific store via the input form's override dropdown. All overrides are documented in the Calculation Detail spreadsheet tab.

---

## Data Quality Considerations

**Completeness**

The initial card database targets 60+ major Canadian credit cards covering all major issuers. The CreditCardGenius sitemap confirms 235 cards exist in the full Canadian market. The long tail (obscure co-branded hotel cards, regional credit union products) rarely wins in optimization against mainstream cash-back and travel cards. 60 cards is sufficient for meaningful optimization; 100+ cards would be exhaustive coverage.

**Freshness**

Card terms change 2–4 times per year per issuer. Quarterly refresh is the maintenance model for the PoC. The `last_verified_date` field on every card record makes staleness visible. Cards not verified in more than 180 days should be flagged in the UI with a "may be outdated" warning.

**Accuracy of Community-Sourced Fields**

Credit score and income thresholds in `approval` are community-sourced (CreditCardGenius editorial, RFD forum reports). They are approximate and issuer-dependent. They are used only for eligibility filtering, not for the optimization math. The `source` field ("issuer" | "community" | "estimated") and `confidence` field ("high" | "medium" | "low") document the reliability of each threshold.

**Store Classification Confidence**

Three confidence tiers are used in the UI:
- **Confirmed**: store classification is explicitly stated in the card's T&C PDF (source: issuer)
- **Community-verified**: classification reported by multiple independent users in RFD or r/churningcanada threads and consistent with the MCC code (source: community)
- **Inferred**: classification derived from MCC code alone, with no card-specific confirmation (source: estimated)

Only "confirmed" and "community-verified" overrides are pre-seeded in `store_overrides`. "Inferred" classifications use the MCC default and display the "may vary" tag.

---

## Data Privacy and Compliance

**No PII in card data.** The card database contains only publicly available card terms (annual fees, earn rates, approval thresholds). No user data is stored in the card database.

**Session data is ephemeral.** The `optimization_sessions` SQLite table stores spending amounts and settings (no names, account numbers, or contact information). Rows expire after 24 hours and are purged at startup. No session data is transmitted to third parties.

**Scraping compliance.** PrinceOfTravel's robots.txt does not prohibit scraping of card pages. CreditCardGenius robots.txt permits individual card pages. The scraping script (`scripts/seed_cards.py`) is a one-time offline tool, not a runtime component. It respects a 1–2 second delay between requests and does not scrape any page marked disallowed in robots.txt.

**Terms of service.** The card data collected from issuer pages is public information, freely available on the issuers' websites. The tool does not copy or republish copyrighted marketing text — it extracts structured facts (earn rates, annual fees) and stores them in a proprietary data schema.

**No affiliate tracking.** The tool does not include referral links, tracking pixels, or affiliate codes. Card names and issuers are referenced factually, not commercially.
