# Credit Card Optimization

The honest Canadian credit card combination optimizer — find the optimal set of credit cards for your actual spending behavior, with no affiliate bias.

> Built with [Claude Code](https://claude.ai/code)

## What This Does

Unlike comparison sites that recommend a single "best" card based on generic spending profiles (and are paid by card issuers to do so), this tool:

- **Optimizes across combinations** of cards, not just one card at a time
- **Uses your actual spending** by category and specific stores
- **Respects real-world constraints**: store-level merchant classifications (Costco is wholesale, not grocery), reward caps, card acceptance limitations, annual fees, and approval requirements
- **Supports couples** with separate eligibility profiles per person
- **Explains every recommendation** with a "Why this card?" breakdown and a full calculation spreadsheet export

## Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set SECRET_KEY to a random hex string

# Run the application
uvicorn app.main:app --reload
```

The app will be available at `http://localhost:8000`.

## Card Database

The card database is a hand-curated JSON file at `data/cards/cards.json`. To update card data:

1. Edit `data/cards/cards.json` directly
2. Verify the record validates: `python -c "from app.services.card_loader import JsonCardDatabaseLoader; JsonCardDatabaseLoader().load()"`
3. Commit the change with a conventional commit: `data(credit-card-optimization): update CARD_NAME rates`

### Seeding Script

To generate draft card records from PrinceOfTravel:

```bash
python scripts/seed_cards.py --urls https://princeoftravel.com/credit-cards/CARD-SLUG/ --delay 2
```

Draft records are printed to stdout for human review — they are NOT automatically merged into `cards.json`.

## Methodology

This tool uses Mixed-Integer Linear Programming (PuLP + CBC solver) to find the mathematically optimal card combination. The optimization:

- Maximizes total net reward (rewards earned minus annual fees)
- Enforces monthly reward caps per card/category
- Applies store-level merchant category code (MCC) classifications per card issuer
- Filters by card acceptance (e.g., Costco only accepts Mastercard in-store)
- Filters by credit score and income eligibility per person

No affiliate relationships. No issuer compensation. The recommendation is purely mathematical.

## License

All rights reserved.
