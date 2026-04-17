"""Tests for app.models.spending — enums, PersonProfile, DummyCard, SpendBucket, SpendingProfile."""

import pytest
from pydantic import ValidationError

from app.models.spending import (
    CreditScoreBand,
    DummyCard,
    IncomeBand,
    PersonProfile,
    SpendBucket,
    SpendingProfile,
)


# --- helper ---

def _person(
    score: CreditScoreBand = CreditScoreBand.GOOD,
    income: IncomeBand = IncomeBand.B60_80K,
) -> PersonProfile:
    return PersonProfile(credit_score_band=score, income_band=income)


def _profile(**overrides) -> SpendingProfile:
    defaults = {
        "category_spend": {"grocery": 500.0},
        "person1": _person(),
    }
    defaults.update(overrides)
    return SpendingProfile(**defaults)


# --- Enums ---


class TestCreditScoreBand:
    def test_values(self) -> None:
        assert CreditScoreBand.FAIR.value == "fair"
        assert CreditScoreBand.GOOD.value == "good"
        assert CreditScoreBand.VERY_GOOD.value == "very_good"
        assert CreditScoreBand.EXCELLENT.value == "excellent"

    def test_count(self) -> None:
        assert len(CreditScoreBand) == 4

    def test_from_string(self) -> None:
        assert CreditScoreBand("excellent") == CreditScoreBand.EXCELLENT


class TestIncomeBand:
    def test_values(self) -> None:
        assert IncomeBand.UNDER_40K.value == "under_40k"
        assert IncomeBand.B40_60K.value == "40k_60k"
        assert IncomeBand.B60_80K.value == "60k_80k"
        assert IncomeBand.B80_100K.value == "80k_100k"
        assert IncomeBand.B100_150K.value == "100k_150k"
        assert IncomeBand.OVER_150K.value == "over_150k"

    def test_count(self) -> None:
        assert len(IncomeBand) == 6


# --- PersonProfile ---


class TestPersonProfile:
    def test_valid(self) -> None:
        p = _person()
        assert p.credit_score_band == CreditScoreBand.GOOD

    def test_invalid_score_band(self) -> None:
        with pytest.raises(ValidationError, match="credit_score_band"):
            PersonProfile(credit_score_band="terrible", income_band="60k_80k")


# --- DummyCard ---


class TestDummyCard:
    def test_valid(self) -> None:
        dc = DummyCard(name="My old card", base_rate=1.0)
        assert dc.annual_fee == 0.0
        assert dc.category_rates == {}

    def test_with_category_rates(self) -> None:
        dc = DummyCard(name="Custom", base_rate=1.0, category_rates={"grocery": 2.0})
        assert dc.category_rates["grocery"] == 2.0

    def test_negative_base_rate_rejected(self) -> None:
        with pytest.raises(ValidationError, match="base_rate"):
            DummyCard(name="Bad", base_rate=-1.0)

    def test_negative_fee_rejected(self) -> None:
        with pytest.raises(ValidationError, match="annual_fee"):
            DummyCard(name="Bad", base_rate=1.0, annual_fee=-50)


# --- SpendBucket ---


class TestSpendBucket:
    def test_valid(self) -> None:
        sb = SpendBucket(
            bucket_id="grocery",
            monthly_amount=500.0,
            resolved_category="grocery",
        )
        assert sb.store_slug is None
        assert sb.acceptance_constraints == set()

    def test_store_bucket(self) -> None:
        sb = SpendBucket(
            bucket_id="costco",
            monthly_amount=300.0,
            resolved_category="wholesale",
            store_slug="costco",
            acceptance_constraints={"cibc_dividend_vi"},
        )
        assert sb.store_slug == "costco"
        assert "cibc_dividend_vi" in sb.acceptance_constraints

    def test_negative_amount_rejected(self) -> None:
        with pytest.raises(ValidationError, match="monthly_amount"):
            SpendBucket(bucket_id="x", monthly_amount=-10, resolved_category="other")


# --- SpendingProfile ---


class TestSpendingProfile:
    def test_minimal_valid(self) -> None:
        sp = _profile()
        assert sp.user_id == "default"
        assert sp.couple_mode is False
        assert sp.person2 is None

    def test_all_zero_spending_rejected(self) -> None:
        with pytest.raises(ValidationError, match="at least one positive spend"):
            SpendingProfile(
                category_spend={"grocery": 0.0},
                store_spend={"costco": 0.0},
                person1=_person(),
            )

    def test_empty_spending_rejected(self) -> None:
        with pytest.raises(ValidationError, match="at least one positive spend"):
            SpendingProfile(
                category_spend={},
                person1=_person(),
            )

    def test_store_spend_only(self) -> None:
        sp = _profile(category_spend={}, store_spend={"costco": 200.0})
        assert sp.store_spend["costco"] == 200.0

    def test_custom_store_spend_only(self) -> None:
        sp = _profile(
            category_spend={},
            custom_store_spend=[("My Store", "other", 100.0)],
        )
        assert len(sp.custom_store_spend) == 1

    def test_chexy_only(self) -> None:
        sp = _profile(category_spend={}, chexy_rent_amount=1500.0)
        assert sp.chexy_rent_amount == 1500.0

    def test_couple_mode_requires_person2(self) -> None:
        with pytest.raises(ValidationError, match="person2 is required"):
            _profile(couple_mode=True, person2=None)

    def test_couple_mode_with_person2(self) -> None:
        sp = _profile(
            couple_mode=True,
            person2=_person(CreditScoreBand.EXCELLENT, IncomeBand.OVER_150K),
        )
        assert sp.person2 is not None
        assert sp.person2.credit_score_band == CreditScoreBand.EXCELLENT

    def test_defaults(self) -> None:
        sp = _profile()
        assert sp.household_id == "default"
        assert sp.include_amex is False
        assert sp.current_card_ids == []
        assert sp.dummy_cards == []
        assert sp.chexy_rent_amount == 0.0

    def test_negative_chexy_rejected(self) -> None:
        with pytest.raises(ValidationError, match="chexy_rent_amount"):
            _profile(chexy_rent_amount=-100)

    def test_with_dummy_cards(self) -> None:
        sp = _profile(
            dummy_cards=[DummyCard(name="Old card", base_rate=1.5)],
        )
        assert len(sp.dummy_cards) == 1
        assert sp.dummy_cards[0].name == "Old card"

    def test_model_roundtrip(self) -> None:
        sp = _profile(
            store_spend={"costco": 300},
            include_amex=True,
            current_card_ids=["cibc_dividend_vi"],
        )
        roundtrip = SpendingProfile.model_validate(sp.model_dump())
        assert roundtrip == sp
