"""Tests for app.services.explainer — ExplanationGenerator.

Covers all 4 acceptance criteria from TASKS.md TASK-008:
1. Grocery → CIBC Dividend produces category-rate explanation with 4.0%.
2. Shoppers Drug Mart → CIBC Dividend (store override) produces store explanation.
3. Chexy row produces Chexy-fee explanation with net rate.
4. All rows non-empty across a realistic set (grocery, chexy, shoppers, split).
"""

from app.models.card import ApprovalRequirements, CardRecord, StoreOverride
from app.models.optimization import AssignmentRow
from app.models.spending import SpendBucket
from app.services.explainer import ExplanationGenerator

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_APPROVAL = ApprovalRequirements(
    min_credit_score=725,
    min_personal_income=60_000,
    min_household_income=100_000,
    source="community",
    confidence="medium",
)

CIBC_DIVIDEND = CardRecord(
    id="cibc_dividend_vi",
    name="CIBC Dividend Visa Infinite",
    issuer="CIBC",
    network="Visa",
    annual_fee=120.0,
    first_year_fee=0.0,
    requires_amex=False,
    approval=_APPROVAL,
    category_rates={
        "grocery": 4.0,
        "gas": 4.0,
        "dining": 2.0,
        "transit": 2.0,
        "recurring": 2.0,
        "other": 1.0,
    },
    category_caps_monthly={"grocery": 80.0, "gas": 80.0},
    store_overrides={
        "shoppers_drug_mart": StoreOverride(
            rate=4.0,
            source="issuer",
            note="SDM coded as grocery on CIBC Dividend",
        ),
        "costco": StoreOverride(
            rate=1.0,
            source="issuer",
            note="Costco coded as wholesale; earns base rate",
        ),
    },
    store_acceptance={"costco_instore": False, "costco_online": True},
    point_system="cashback",
    cpp_default=1.0,
    last_verified_date="2026-04-15",
    source_url="https://www.cibc.com",
)

ROGERS = CardRecord(
    id="rogers_world_elite",
    name="Rogers World Elite Mastercard",
    issuer="Rogers Bank",
    network="Mastercard",
    annual_fee=0.0,
    first_year_fee=0.0,
    requires_amex=False,
    approval=_APPROVAL,
    category_rates={"other": 1.5, "grocery": 1.5},
    category_caps_monthly={},
    store_overrides={},
    store_acceptance={},
    point_system="cashback",
    cpp_default=1.0,
    last_verified_date="2026-04-15",
    source_url="https://www.rogers.com",
)

AMEX_COBALT = CardRecord(
    id="amex_cobalt",
    name="American Express Cobalt Card",
    issuer="American Express",
    network="Amex",
    annual_fee=155.88,
    first_year_fee=155.88,
    requires_amex=True,
    approval=_APPROVAL,
    category_rates={
        "dining": 5.0,
        "grocery": 5.0,
        "streaming": 3.0,
        "travel": 2.0,
        "other": 1.0,
    },
    category_caps_monthly={},
    store_overrides={},
    store_acceptance={},
    point_system="amex_mr",
    cpp_default=2.0,
    last_verified_date="2026-04-15",
    source_url="https://www.americanexpress.com",
)


def _make_assignment_row(**kwargs) -> AssignmentRow:
    """Helper to build an AssignmentRow with sensible defaults."""
    defaults = dict(
        bucket_id="grocery",
        label="Grocery",
        cardholder=None,
        card_id="cibc_dividend_vi",
        card_name="CIBC Dividend Visa Infinite",
        monthly_spend=400.0,
        reward_rate_pct=4.0,
        expected_monthly_reward=16.0,
        is_chexy=False,
        chexy_net_rate_pct=None,
        explanation="",
    )
    defaults.update(kwargs)
    return AssignmentRow(**defaults)


# ---------------------------------------------------------------------------
# AC-1: Grocery → CIBC Dividend (category rate explanation)
# ---------------------------------------------------------------------------

def test_grocery_cibc_dividend_category_explanation() -> None:
    """AC-1: grocery bucket with CIBC Dividend → category-rate explanation."""
    generator = ExplanationGenerator()

    row = _make_assignment_row(
        bucket_id="grocery",
        card_id="cibc_dividend_vi",
        card_name="CIBC Dividend Visa Infinite",
        reward_rate_pct=4.0,
    )
    bucket = SpendBucket(
        bucket_id="grocery",
        monthly_amount=400.0,
        resolved_category="grocery",
        store_slug=None,
        is_chexy=False,
    )

    result = generator.annotate(
        rows=[row],
        cards_by_id={"cibc_dividend_vi": CIBC_DIVIDEND},
        buckets_by_id={"grocery": bucket},
    )

    assert len(result) == 1
    explanation = result[0].explanation
    assert "earns 4.0% on Grocery spending; no eligible card earns more in this category." in explanation
    assert "CIBC Dividend Visa Infinite" in explanation


# ---------------------------------------------------------------------------
# AC-2: Shoppers Drug Mart → CIBC Dividend (store override explanation)
# ---------------------------------------------------------------------------

def test_shoppers_cibc_store_override_explanation() -> None:
    """AC-2: SDM bucket with CIBC Dividend store override → store explanation."""
    generator = ExplanationGenerator()

    row = _make_assignment_row(
        bucket_id="shoppers_drug_mart",
        label="Shoppers Drug Mart",
        card_id="cibc_dividend_vi",
        card_name="CIBC Dividend Visa Infinite",
        monthly_spend=200.0,
        reward_rate_pct=4.0,
        expected_monthly_reward=8.0,
    )
    bucket = SpendBucket(
        bucket_id="shoppers_drug_mart",
        monthly_amount=200.0,
        resolved_category="grocery",
        store_slug="shoppers_drug_mart",
        is_chexy=False,
    )

    result = generator.annotate(
        rows=[row],
        cards_by_id={"cibc_dividend_vi": CIBC_DIVIDEND},
        buckets_by_id={"shoppers_drug_mart": bucket},
    )

    assert len(result) == 1
    explanation = result[0].explanation
    assert "earns 4.0% at Shoppers Drug Mart" in explanation
    assert "classified as" in explanation
    assert "CIBC" in explanation


# ---------------------------------------------------------------------------
# AC-3: Chexy rent row
# ---------------------------------------------------------------------------

def test_chexy_rent_explanation() -> None:
    """AC-3: Chexy bucket → Chexy-fee explanation with net rate."""
    generator = ExplanationGenerator()

    # CIBC Dividend other_rate = 1.0%, net = max(0, 1.0 - 1.75) = 0%
    # Use a card with other_rate=3.0% so net = 3.0 - 1.75 = 1.25%
    chexy_card = CIBC_DIVIDEND.model_copy(
        update={
            "category_rates": {
                "grocery": 4.0,
                "gas": 4.0,
                "dining": 2.0,
                "other": 3.0,
            }
        }
    )

    net_rate = max(0.0, 3.0 - 1.75)  # 1.25

    row = _make_assignment_row(
        bucket_id="chexy_rent",
        label="Chexy Rent",
        card_id="cibc_dividend_vi",
        card_name="CIBC Dividend Visa Infinite",
        monthly_spend=1500.0,
        reward_rate_pct=net_rate,
        expected_monthly_reward=1500.0 * net_rate / 100,
        is_chexy=True,
        chexy_net_rate_pct=net_rate,
    )
    bucket = SpendBucket(
        bucket_id="chexy_rent",
        monthly_amount=1500.0,
        resolved_category="other",
        store_slug=None,
        is_chexy=True,
    )

    result = generator.annotate(
        rows=[row],
        cards_by_id={"cibc_dividend_vi": chexy_card},
        buckets_by_id={"chexy_rent": bucket},
    )

    assert len(result) == 1
    explanation = result[0].explanation
    assert "after Chexy's 1.75% fee, the net return on rent is 1.25%" in explanation
    assert "CIBC Dividend Visa Infinite" in explanation


# ---------------------------------------------------------------------------
# AC-4: All rows non-empty across a realistic mixed set
# ---------------------------------------------------------------------------

def test_all_rows_non_empty() -> None:
    """AC-4: Every AssignmentRow in a realistic set gets a non-empty explanation."""
    generator = ExplanationGenerator()

    # Row 1: grocery → CIBC Dividend (category rate)
    row_grocery = _make_assignment_row(
        bucket_id="grocery",
        card_id="cibc_dividend_vi",
        card_name="CIBC Dividend Visa Infinite",
        monthly_spend=400.0,
        reward_rate_pct=4.0,
        expected_monthly_reward=16.0,
    )
    bucket_grocery = SpendBucket(
        bucket_id="grocery",
        monthly_amount=400.0,
        resolved_category="grocery",
        store_slug=None,
        is_chexy=False,
    )

    # Row 2: Chexy → CIBC Dividend (chexy)
    row_chexy = _make_assignment_row(
        bucket_id="chexy_rent",
        label="Chexy Rent",
        card_id="cibc_dividend_vi",
        card_name="CIBC Dividend Visa Infinite",
        monthly_spend=1500.0,
        reward_rate_pct=max(0.0, 1.0 - 1.75),
        expected_monthly_reward=0.0,
        is_chexy=True,
        chexy_net_rate_pct=max(0.0, 1.0 - 1.75),
    )
    bucket_chexy = SpendBucket(
        bucket_id="chexy_rent",
        monthly_amount=1500.0,
        resolved_category="other",
        store_slug=None,
        is_chexy=True,
    )

    # Row 3: Shoppers Drug Mart → CIBC Dividend (store override)
    row_shoppers = _make_assignment_row(
        bucket_id="shoppers_drug_mart",
        label="Shoppers Drug Mart",
        card_id="cibc_dividend_vi",
        card_name="CIBC Dividend Visa Infinite",
        monthly_spend=200.0,
        reward_rate_pct=4.0,
        expected_monthly_reward=8.0,
    )
    bucket_shoppers = SpendBucket(
        bucket_id="shoppers_drug_mart",
        monthly_amount=200.0,
        resolved_category="grocery",
        store_slug="shoppers_drug_mart",
        is_chexy=False,
    )

    # Rows 4 + 5: split grocery2 bucket — CIBC Dividend (primary 4%) + Rogers overflow (1.5%)
    # Note: same bucket_id for split detection
    row_split_primary = _make_assignment_row(
        bucket_id="grocery2",
        label="Grocery2",
        card_id="cibc_dividend_vi",
        card_name="CIBC Dividend Visa Infinite",
        monthly_spend=80.0,     # cap amount
        reward_rate_pct=4.0,
        expected_monthly_reward=3.20,
    )
    row_split_overflow = _make_assignment_row(
        bucket_id="grocery2",
        label="Grocery2",
        card_id="rogers_world_elite",
        card_name="Rogers World Elite Mastercard",
        monthly_spend=320.0,    # overflow
        reward_rate_pct=1.5,
        expected_monthly_reward=4.80,
    )
    bucket_split = SpendBucket(
        bucket_id="grocery2",
        monthly_amount=400.0,
        resolved_category="grocery",
        store_slug=None,
        is_chexy=False,
    )

    all_rows = [row_grocery, row_chexy, row_shoppers, row_split_primary, row_split_overflow]
    all_buckets = {
        "grocery": bucket_grocery,
        "chexy_rent": bucket_chexy,
        "shoppers_drug_mart": bucket_shoppers,
        "grocery2": bucket_split,
    }
    all_cards = {
        "cibc_dividend_vi": CIBC_DIVIDEND,
        "rogers_world_elite": ROGERS,
    }

    results = generator.annotate(all_rows, all_cards, all_buckets)

    assert len(results) == 5
    for r in results:
        assert r.explanation, f"Empty explanation for bucket_id={r.bucket_id}, card_id={r.card_id}"

    # Spot-check the split rows
    split_results = [r for r in results if r.bucket_id == "grocery2"]
    assert len(split_results) == 2
    split_results.sort(key=lambda r: r.reward_rate_pct, reverse=True)

    # Primary row gets a category explanation (highest rate)
    assert "no eligible card earns more in this category" in split_results[0].explanation

    # Overflow row gets a split explanation
    overflow = split_results[1]
    assert "cap reached" in overflow.explanation
    assert "CIBC Dividend" in overflow.explanation


# ---------------------------------------------------------------------------
# Edge case: split — overflow row references correct primary card name
# ---------------------------------------------------------------------------

def test_split_overflow_references_primary_card() -> None:
    """Split overflow row must name the primary card and say 'cap reached'."""
    generator = ExplanationGenerator()

    primary_row = _make_assignment_row(
        bucket_id="grocery",
        card_id="cibc_dividend_vi",
        card_name="CIBC Dividend Visa Infinite",
        monthly_spend=80.0,
        reward_rate_pct=4.0,
        expected_monthly_reward=3.20,
    )
    overflow_row = _make_assignment_row(
        bucket_id="grocery",
        card_id="rogers_world_elite",
        card_name="Rogers World Elite Mastercard",
        monthly_spend=320.0,
        reward_rate_pct=1.5,
        expected_monthly_reward=4.80,
    )
    bucket = SpendBucket(
        bucket_id="grocery",
        monthly_amount=400.0,
        resolved_category="grocery",
        store_slug=None,
        is_chexy=False,
    )

    results = generator.annotate(
        rows=[primary_row, overflow_row],
        cards_by_id={"cibc_dividend_vi": CIBC_DIVIDEND, "rogers_world_elite": ROGERS},
        buckets_by_id={"grocery": bucket},
    )

    assert len(results) == 2
    by_card = {r.card_id: r for r in results}

    # Primary gets a normal category explanation
    assert "no eligible card earns more" in by_card["cibc_dividend_vi"].explanation

    # Overflow references the primary card
    overflow_exp = by_card["rogers_world_elite"].explanation
    assert "CIBC Dividend Visa Infinite" in overflow_exp
    assert "cap reached" in overflow_exp
    assert "1.5%" in overflow_exp


# ---------------------------------------------------------------------------
# Edge case: missing card/bucket falls back gracefully
# ---------------------------------------------------------------------------

def test_missing_card_fallback() -> None:
    """Row referencing an unknown card_id gets a fallback explanation (non-empty)."""
    generator = ExplanationGenerator()

    row = _make_assignment_row(
        card_id="nonexistent_card",
        card_name="Unknown Card",
        bucket_id="grocery",
        reward_rate_pct=2.0,
    )
    bucket = SpendBucket(
        bucket_id="grocery",
        monthly_amount=400.0,
        resolved_category="grocery",
        store_slug=None,
        is_chexy=False,
    )

    results = generator.annotate(
        rows=[row],
        cards_by_id={},
        buckets_by_id={"grocery": bucket},
    )

    assert len(results) == 1
    assert results[0].explanation  # non-empty fallback
