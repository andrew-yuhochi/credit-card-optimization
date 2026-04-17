"""Tests for app.services.eligibility — EligibilityFilter."""

import json
from pathlib import Path

import pytest

from app.models.card import ApprovalRequirements, CardRecord
from app.models.spending import (
    CreditScoreBand,
    DummyCard,
    IncomeBand,
    PersonProfile,
    SpendingProfile,
)
from app.services.eligibility import EligibilityFilter

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CARDS_PATH = DATA_DIR / "cards" / "cards.json"


# --- helpers ---


def _card(
    card_id: str = "test_card",
    network: str = "Visa",
    requires_amex: bool = False,
    min_credit_score: int = 600,
    min_personal_income: float = 30000,
    min_household_income: float = 50000,
    store_acceptance: dict | None = None,
    is_dummy: bool = False,
) -> CardRecord:
    return CardRecord(
        id=card_id,
        name=f"Test {card_id}",
        issuer="TestBank",
        network=network,
        annual_fee=0.0,
        first_year_fee=0.0,
        requires_amex=requires_amex,
        approval=ApprovalRequirements(
            min_credit_score=min_credit_score,
            min_personal_income=min_personal_income,
            min_household_income=min_household_income,
            source="estimated",
            confidence="low",
        ),
        category_rates={"other": 1.0},
        store_acceptance=store_acceptance or {},
        point_system="cashback",
        cpp_default=1.0,
        last_verified_date="2026-01-01",
        source_url="https://example.com",
        is_dummy=is_dummy,
    )


def _profile(
    score: CreditScoreBand = CreditScoreBand.VERY_GOOD,
    income: IncomeBand = IncomeBand.B80_100K,
    include_amex: bool = False,
    couple_mode: bool = False,
    person2_score: CreditScoreBand | None = None,
    person2_income: IncomeBand | None = None,
    store_spend: dict | None = None,
) -> SpendingProfile:
    p2 = None
    if couple_mode:
        p2 = PersonProfile(
            credit_score_band=person2_score or CreditScoreBand.GOOD,
            income_band=person2_income or IncomeBand.B60_80K,
        )
    return SpendingProfile(
        category_spend={"grocery": 500.0},
        store_spend=store_spend or {},
        include_amex=include_amex,
        person1=PersonProfile(credit_score_band=score, income_band=income),
        couple_mode=couple_mode,
        person2=p2,
    )


@pytest.fixture()
def seed_cards() -> list[CardRecord]:
    with open(CARDS_PATH) as f:
        data = json.load(f)
    return [CardRecord.model_validate(c) for c in data["cards"]]


# --- Amex filter ---


class TestAmexFilter:
    def test_amex_off_removes_amex_cards(self) -> None:
        cards = [
            _card("visa_card"),
            _card("amex_card", network="Amex", requires_amex=True),
        ]
        result = EligibilityFilter.filter(cards, _profile(include_amex=False))
        assert len(result) == 1
        assert result[0].id == "visa_card"

    def test_amex_on_keeps_amex_cards(self) -> None:
        cards = [
            _card("visa_card"),
            _card("amex_card", network="Amex", requires_amex=True),
        ]
        result = EligibilityFilter.filter(cards, _profile(include_amex=True))
        assert len(result) == 2

    def test_amex_off_keeps_non_amex(self) -> None:
        cards = [_card("mc_card", network="Mastercard")]
        result = EligibilityFilter.filter(cards, _profile(include_amex=False))
        assert len(result) == 1


# --- Credit score filter ---


class TestCreditScoreFilter:
    def test_fair_score_removes_high_threshold(self) -> None:
        cards = [_card("high_score", min_credit_score=725)]
        result = EligibilityFilter.filter(
            cards, _profile(score=CreditScoreBand.FAIR)
        )
        assert len(result) == 0

    def test_excellent_score_keeps_all(self) -> None:
        cards = [
            _card("low", min_credit_score=600),
            _card("mid", min_credit_score=725),
            _card("high", min_credit_score=760),
        ]
        result = EligibilityFilter.filter(
            cards, _profile(score=CreditScoreBand.EXCELLENT)
        )
        assert len(result) == 3

    def test_good_score_boundary(self) -> None:
        # GOOD band max is 724
        cards = [
            _card("at_724", min_credit_score=724),
            _card("at_725", min_credit_score=725),
        ]
        result = EligibilityFilter.filter(
            cards, _profile(score=CreditScoreBand.GOOD)
        )
        assert len(result) == 1
        assert result[0].id == "at_724"

    def test_very_good_boundary(self) -> None:
        # VERY_GOOD band max is 759
        cards = [_card("at_759", min_credit_score=759)]
        result = EligibilityFilter.filter(
            cards, _profile(score=CreditScoreBand.VERY_GOOD)
        )
        assert len(result) == 1


# --- Income filter ---


class TestIncomeFilter:
    def test_low_income_removes_high_requirement(self) -> None:
        cards = [_card("expensive", min_personal_income=80000)]
        result = EligibilityFilter.filter(
            cards, _profile(income=IncomeBand.B60_80K)
        )
        assert len(result) == 0

    def test_high_income_keeps_all(self) -> None:
        cards = [
            _card("cheap", min_personal_income=30000),
            _card("mid", min_personal_income=80000),
        ]
        result = EligibilityFilter.filter(
            cards, _profile(income=IncomeBand.OVER_150K)
        )
        assert len(result) == 2

    def test_income_boundary(self) -> None:
        # B60_80K max is 79999
        cards = [
            _card("at_79999", min_personal_income=79999),
            _card("at_80000", min_personal_income=80000),
        ]
        result = EligibilityFilter.filter(
            cards, _profile(income=IncomeBand.B60_80K)
        )
        assert len(result) == 1
        assert result[0].id == "at_79999"


# --- Couple mode ---


class TestCoupleMode:
    def test_either_person_qualifies(self) -> None:
        # Card requires 725+ credit score; person1 has FAIR, person2 has EXCELLENT
        cards = [_card("needs_high_score", min_credit_score=725)]
        result = EligibilityFilter.filter(
            cards,
            _profile(
                score=CreditScoreBand.FAIR,
                couple_mode=True,
                person2_score=CreditScoreBand.EXCELLENT,
                person2_income=IncomeBand.B80_100K,
            ),
        )
        assert len(result) == 1

    def test_household_income_qualifies(self) -> None:
        # Card requires household income 100K; each person earns 60-80K range
        cards = [
            _card(
                "household_card",
                min_credit_score=600,
                min_personal_income=30000,
                min_household_income=100000,
            )
        ]
        result = EligibilityFilter.filter(
            cards,
            _profile(
                score=CreditScoreBand.VERY_GOOD,
                income=IncomeBand.B60_80K,
                couple_mode=True,
                person2_score=CreditScoreBand.GOOD,
                person2_income=IncomeBand.B60_80K,
            ),
        )
        # Combined: 79999 + 79999 = 159998 >= 100000
        assert len(result) == 1

    def test_neither_qualifies_removed(self) -> None:
        # Card requires 760+ credit; both persons have FAIR
        cards = [_card("elite", min_credit_score=760)]
        result = EligibilityFilter.filter(
            cards,
            _profile(
                score=CreditScoreBand.FAIR,
                couple_mode=True,
                person2_score=CreditScoreBand.FAIR,
                person2_income=IncomeBand.UNDER_40K,
            ),
        )
        assert len(result) == 0


# --- Store acceptance ---


class TestStoreAcceptanceFilter:
    def test_card_excluded_at_store(self) -> None:
        # Card not accepted at costco (both channels false)
        cards = [
            _card(
                "no_costco",
                store_acceptance={"costco_instore": False, "costco_online": False},
            )
        ]
        result = EligibilityFilter.filter(
            cards, _profile(store_spend={"costco": 300.0})
        )
        assert len(result) == 0

    def test_card_partially_accepted_kept(self) -> None:
        # Card accepted online but not in-store — still usable
        cards = [
            _card(
                "online_only",
                store_acceptance={"costco_instore": False, "costco_online": True},
            )
        ]
        result = EligibilityFilter.filter(
            cards, _profile(store_spend={"costco": 300.0})
        )
        assert len(result) == 1

    def test_no_acceptance_entries_kept(self) -> None:
        # Card has no store_acceptance at all — assumed accepted everywhere
        cards = [_card("universal")]
        result = EligibilityFilter.filter(
            cards, _profile(store_spend={"costco": 300.0})
        )
        assert len(result) == 1

    def test_zero_store_spend_ignored(self) -> None:
        # Even though card is excluded at costco, spend is $0 so it doesn't matter
        cards = [
            _card(
                "no_costco",
                store_acceptance={"costco_instore": False, "costco_online": False},
            )
        ]
        result = EligibilityFilter.filter(
            cards, _profile(store_spend={"costco": 0.0})
        )
        assert len(result) == 1


# --- Dummy cards ---


class TestDummyCardPassthrough:
    def test_dummy_cards_always_pass(self) -> None:
        dummy = _card("dummy_0", is_dummy=True, min_credit_score=900)
        result = EligibilityFilter.filter(
            [dummy], _profile(score=CreditScoreBand.FAIR)
        )
        assert len(result) == 1
        assert result[0].id == "dummy_0"

    def test_dummy_amex_card_passes_without_amex(self) -> None:
        dummy = _card(
            "dummy_amex", is_dummy=True, requires_amex=True, network="Amex"
        )
        result = EligibilityFilter.filter(
            [dummy], _profile(include_amex=False)
        )
        assert len(result) == 1

    def test_dummy_passes_store_filter(self) -> None:
        dummy = _card(
            "dummy_store",
            is_dummy=True,
            store_acceptance={"costco_instore": False, "costco_online": False},
        )
        result = EligibilityFilter.filter(
            [dummy], _profile(store_spend={"costco": 300.0})
        )
        assert len(result) == 1


# --- Seed data integration ---


class TestSeedCardIntegration:
    def test_reasonable_profile_keeps_some_cards(self, seed_cards: list[CardRecord]) -> None:
        # Very good credit, 80-100K income, no Amex
        result = EligibilityFilter.filter(
            seed_cards,
            _profile(
                score=CreditScoreBand.VERY_GOOD,
                income=IncomeBand.B80_100K,
                include_amex=False,
            ),
        )
        assert len(result) >= 1
        # Amex cards should be filtered out
        assert all(not c.requires_amex for c in result)

    def test_all_seed_with_amex(self, seed_cards: list[CardRecord]) -> None:
        result = EligibilityFilter.filter(
            seed_cards,
            _profile(
                score=CreditScoreBand.EXCELLENT,
                income=IncomeBand.OVER_150K,
                include_amex=True,
            ),
        )
        # All 5 should pass with max eligibility
        assert len(result) == 5

    def test_costco_spend_removes_amex_cards_at_costco(
        self, seed_cards: list[CardRecord]
    ) -> None:
        result = EligibilityFilter.filter(
            seed_cards,
            _profile(
                score=CreditScoreBand.EXCELLENT,
                income=IncomeBand.OVER_150K,
                include_amex=True,
                store_spend={"costco": 300.0},
            ),
        )
        # Scotiabank Gold Amex and Amex Cobalt have costco_instore=False
        # and costco_online=False — they should be excluded
        result_ids = {c.id for c in result}
        assert "scotiabank_gold_amex" not in result_ids
        assert "amex_cobalt" not in result_ids
        # CIBC has costco_online=True so should remain
        assert "cibc_dividend_vi" in result_ids
