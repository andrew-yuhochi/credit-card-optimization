"""Tests for app.services.spend_normalizer — SpendBucketNormalizer and DummyCardBuilder."""

import pytest

from app.models.card import StoreMccEntry
from app.models.spending import (
    CreditScoreBand,
    DummyCard,
    IncomeBand,
    PersonProfile,
    SpendingProfile,
)
from app.services.spend_normalizer import STANDARD_CATEGORIES, DummyCardBuilder, SpendBucketNormalizer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_PERSON = PersonProfile(
    credit_score_band=CreditScoreBand.EXCELLENT,
    income_band=IncomeBand.B80_100K,
)

# Minimal store_mcc_map fixture — costco maps to wholesale
STORE_MCC_MAP: dict[str, StoreMccEntry] = {
    "costco": StoreMccEntry(mcc="5300", default_category="wholesale"),
    "loblaws": StoreMccEntry(mcc="5411", default_category="grocery"),
}


def _profile(**kwargs) -> SpendingProfile:
    """Build a SpendingProfile, merging caller kwargs with sensible defaults."""
    defaults = dict(
        category_spend={},
        store_spend={},
        custom_store_spend=[],
        chexy_rent_amount=0.0,
        person1=MINIMAL_PERSON,
    )
    defaults.update(kwargs)
    return SpendingProfile(**defaults)


# ---------------------------------------------------------------------------
# SpendBucketNormalizer — acceptance criteria tests
# ---------------------------------------------------------------------------


class TestSpendBucketNormalizer:
    normalizer = SpendBucketNormalizer()

    # AC-1: grocery=$400, costco=$300, chexy_rent=$1500 → 3 buckets
    def test_three_buckets_for_grocery_costco_chexy(self):
        profile = _profile(
            category_spend={"grocery": 400.0},
            store_spend={"costco": 300.0},
            chexy_rent_amount=1500.0,
        )
        buckets = self.normalizer.normalize(profile, STORE_MCC_MAP)
        assert len(buckets) == 3

    # AC-2: Costco bucket has resolved_category="wholesale" and store_slug="costco"
    def test_costco_resolved_category_and_slug(self):
        profile = _profile(
            category_spend={"grocery": 400.0},
            store_spend={"costco": 300.0},
            chexy_rent_amount=1500.0,
        )
        buckets = self.normalizer.normalize(profile, STORE_MCC_MAP)
        costco_bucket = next(b for b in buckets if b.bucket_id == "costco")
        assert costco_bucket.resolved_category == "wholesale"
        assert costco_bucket.store_slug == "costco"

    # AC-3: Chexy bucket has bucket_id="chexy_rent" and is_chexy=True
    def test_chexy_bucket_id_and_flag(self):
        profile = _profile(
            category_spend={"grocery": 400.0},
            store_spend={"costco": 300.0},
            chexy_rent_amount=1500.0,
        )
        buckets = self.normalizer.normalize(profile, STORE_MCC_MAP)
        chexy_bucket = next(b for b in buckets if b.bucket_id == "chexy_rent")
        assert chexy_bucket.is_chexy is True
        assert chexy_bucket.monthly_amount == 1500.0
        assert chexy_bucket.resolved_category == "other"

    # AC-4: Zero-amount entries are excluded from output
    def test_zero_amounts_excluded(self):
        profile = _profile(
            category_spend={"grocery": 400.0, "gas": 0.0, "dining": 0.0},
            store_spend={"costco": 0.0, "loblaws": 50.0},
        )
        buckets = self.normalizer.normalize(profile, STORE_MCC_MAP)
        bucket_ids = {b.bucket_id for b in buckets}
        assert "gas" not in bucket_ids
        assert "dining" not in bucket_ids
        assert "costco" not in bucket_ids
        assert "grocery" in bucket_ids
        assert "loblaws" in bucket_ids
        assert len(buckets) == 2

    # Extra: category bucket gets correct resolved_category and no store_slug
    def test_category_bucket_attributes(self):
        profile = _profile(category_spend={"dining": 200.0})
        buckets = self.normalizer.normalize(profile, STORE_MCC_MAP)
        assert len(buckets) == 1
        b = buckets[0]
        assert b.bucket_id == "dining"
        assert b.monthly_amount == 200.0
        assert b.resolved_category == "dining"
        assert b.store_slug is None
        assert b.is_chexy is False

    # Extra: unknown store slug defaults to "other" (logs WARNING)
    def test_unknown_store_slug_defaults_to_other(self):
        profile = _profile(store_spend={"unknown_store": 75.0})
        buckets = self.normalizer.normalize(profile, STORE_MCC_MAP)
        assert len(buckets) == 1
        assert buckets[0].resolved_category == "other"
        assert buckets[0].store_slug == "unknown_store"

    # Extra: custom_store_spend uses provided category_override
    def test_custom_store_spend_bucket(self):
        profile = _profile(
            custom_store_spend=[("My Butcher", "other", 120.0)],
        )
        buckets = self.normalizer.normalize(profile, STORE_MCC_MAP)
        assert len(buckets) == 1
        b = buckets[0]
        assert b.bucket_id == "custom_my_butcher"
        assert b.resolved_category == "other"
        assert b.monthly_amount == 120.0
        assert b.store_slug is None

    # Extra: custom_store_spend with zero amount is excluded
    def test_custom_store_spend_zero_excluded(self):
        profile = _profile(
            custom_store_spend=[("My Butcher", "other", 0.0)],
            category_spend={"grocery": 50.0},
        )
        buckets = self.normalizer.normalize(profile, STORE_MCC_MAP)
        assert all(b.bucket_id != "custom_my_butcher" for b in buckets)

    # Extra: chexy_rent_amount=0 produces no chexy bucket
    def test_zero_chexy_excluded(self):
        profile = _profile(category_spend={"grocery": 200.0}, chexy_rent_amount=0.0)
        buckets = self.normalizer.normalize(profile, STORE_MCC_MAP)
        assert all(b.bucket_id != "chexy_rent" for b in buckets)


# ---------------------------------------------------------------------------
# DummyCardBuilder — acceptance criteria tests
# ---------------------------------------------------------------------------


class TestDummyCardBuilder:
    builder = DummyCardBuilder()

    # AC-5: DummyCardBuilder produces CardRecord with is_dummy=True,
    #       approval.min_credit_score=0, approval.min_personal_income=0
    def test_dummy_card_is_dummy_and_zero_approval(self):
        dummy = DummyCard(name="My Hypothetical Card", base_rate=1.5)
        records = self.builder.build([dummy])
        assert len(records) == 1
        card = records[0]
        assert card.is_dummy is True
        assert card.approval.min_credit_score == 0
        assert card.approval.min_personal_income == 0
        assert card.approval.min_household_income == 0

    # AC-6: Dummy card with base_rate=2.0 and no category_rates uses 2.0% for all categories
    def test_base_rate_fills_all_standard_categories(self):
        dummy = DummyCard(name="Flat 2% Card", base_rate=2.0)
        records = self.builder.build([dummy])
        card = records[0]
        for category in STANDARD_CATEGORIES:
            assert card.category_rates[category] == 2.0, (
                f"Expected 2.0% for category '{category}', got {card.category_rates[category]}"
            )

    # Extra: category-specific override takes precedence over base_rate
    def test_category_rate_override_wins(self):
        dummy = DummyCard(
            name="Grocery Focused",
            base_rate=1.0,
            category_rates={"grocery": 4.0, "gas": 3.0},
        )
        records = self.builder.build([dummy])
        card = records[0]
        assert card.category_rates["grocery"] == 4.0
        assert card.category_rates["gas"] == 3.0
        # Other categories fall back to base_rate
        assert card.category_rates["dining"] == 1.0
        assert card.category_rates["other"] == 1.0

    # Extra: multiple dummy cards get sequential ids
    def test_multiple_dummy_cards_have_sequential_ids(self):
        dummies = [
            DummyCard(name="Card A", base_rate=1.0),
            DummyCard(name="Card B", base_rate=2.0),
            DummyCard(name="Card C", base_rate=3.0),
        ]
        records = self.builder.build(dummies)
        assert len(records) == 3
        assert records[0].id == "dummy_0"
        assert records[1].id == "dummy_1"
        assert records[2].id == "dummy_2"

    # Extra: empty list returns empty list
    def test_empty_list_returns_empty(self):
        records = self.builder.build([])
        assert records == []

    # Extra: card metadata is set correctly
    def test_dummy_card_metadata(self):
        dummy = DummyCard(name="My Card", annual_fee=120.0, base_rate=1.5)
        records = self.builder.build([dummy])
        card = records[0]
        assert card.name == "My Card"
        assert card.issuer == "Custom"
        assert card.network == "Other"
        assert card.annual_fee == 120.0
        assert card.first_year_fee == 120.0
        assert card.requires_amex is False
        assert card.point_system == "cashback"
        assert card.cpp_default == 1.0
        assert card.is_dummy is True

    # Extra: all standard categories are present on every dummy card
    def test_all_standard_categories_present(self):
        dummy = DummyCard(name="Test", base_rate=1.0)
        records = self.builder.build([dummy])
        card = records[0]
        for category in STANDARD_CATEGORIES:
            assert category in card.category_rates
