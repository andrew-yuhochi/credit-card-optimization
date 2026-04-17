"""Tests for app.models.card — CardRecord, ApprovalRequirements, StoreOverride."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.card import ApprovalRequirements, CardRecord, StoreOverride

CARDS_JSON = Path(__file__).resolve().parent.parent / "data" / "cards" / "cards.json"


# --- fixtures ---


@pytest.fixture()
def seed_cards() -> list[dict]:
    with open(CARDS_JSON) as f:
        return json.load(f)["cards"]


@pytest.fixture()
def minimal_card_dict() -> dict:
    return {
        "id": "test_card",
        "name": "Test Card",
        "issuer": "TestBank",
        "network": "Visa",
        "annual_fee": 0.0,
        "first_year_fee": 0.0,
        "requires_amex": False,
        "approval": {
            "min_credit_score": 600,
            "min_personal_income": 30000,
            "min_household_income": 50000,
            "source": "estimated",
            "confidence": "low",
        },
        "category_rates": {"other": 1.0},
        "point_system": "cashback",
        "cpp_default": 1.0,
        "last_verified_date": "2026-01-01",
        "source_url": "https://example.com",
    }


# --- ApprovalRequirements ---


class TestApprovalRequirements:
    def test_valid(self) -> None:
        ar = ApprovalRequirements(
            min_credit_score=700,
            min_personal_income=60000,
            min_household_income=100000,
            source="issuer",
            confidence="high",
        )
        assert ar.min_credit_score == 700

    def test_negative_credit_score_rejected(self) -> None:
        with pytest.raises(ValidationError, match="min_credit_score"):
            ApprovalRequirements(
                min_credit_score=-1,
                min_personal_income=0,
                min_household_income=0,
                source="issuer",
                confidence="high",
            )

    def test_negative_income_rejected(self) -> None:
        with pytest.raises(ValidationError, match="min_personal_income"):
            ApprovalRequirements(
                min_credit_score=0,
                min_personal_income=-100,
                min_household_income=0,
                source="issuer",
                confidence="high",
            )

    def test_invalid_source_rejected(self) -> None:
        with pytest.raises(ValidationError, match="source"):
            ApprovalRequirements(
                min_credit_score=0,
                min_personal_income=0,
                min_household_income=0,
                source="blog_post",
                confidence="high",
            )

    def test_invalid_confidence_rejected(self) -> None:
        with pytest.raises(ValidationError, match="confidence"):
            ApprovalRequirements(
                min_credit_score=0,
                min_personal_income=0,
                min_household_income=0,
                source="issuer",
                confidence="unknown",
            )


# --- StoreOverride ---


class TestStoreOverride:
    def test_valid(self) -> None:
        so = StoreOverride(rate=4.0, source="issuer", note="test")
        assert so.rate == 4.0
        assert so.note == "test"

    def test_default_note(self) -> None:
        so = StoreOverride(rate=1.0, source="community")
        assert so.note == ""

    def test_negative_rate_rejected(self) -> None:
        with pytest.raises(ValidationError, match="rate"):
            StoreOverride(rate=-0.5, source="issuer")


# --- CardRecord ---


class TestCardRecord:
    def test_all_seed_cards_validate(self, seed_cards: list[dict]) -> None:
        for card_dict in seed_cards:
            card = CardRecord.model_validate(card_dict)
            assert card.id
            assert card.name

    def test_seed_card_count(self, seed_cards: list[dict]) -> None:
        assert len(seed_cards) == 5

    def test_minimal_card(self, minimal_card_dict: dict) -> None:
        card = CardRecord.model_validate(minimal_card_dict)
        assert card.id == "test_card"
        assert card.store_overrides == {}
        assert card.store_acceptance == {}
        assert card.category_caps_monthly == {}
        assert card.override_notes == ""
        assert card.is_dummy is False

    def test_invalid_network_rejected(self, minimal_card_dict: dict) -> None:
        minimal_card_dict["network"] = "Discover"
        with pytest.raises(ValidationError, match="network"):
            CardRecord.model_validate(minimal_card_dict)

    def test_negative_annual_fee_rejected(self, minimal_card_dict: dict) -> None:
        minimal_card_dict["annual_fee"] = -10.0
        with pytest.raises(ValidationError, match="annual_fee"):
            CardRecord.model_validate(minimal_card_dict)

    def test_zero_cpp_rejected(self, minimal_card_dict: dict) -> None:
        minimal_card_dict["cpp_default"] = 0.0
        with pytest.raises(ValidationError, match="cpp_default"):
            CardRecord.model_validate(minimal_card_dict)

    def test_negative_cpp_rejected(self, minimal_card_dict: dict) -> None:
        minimal_card_dict["cpp_default"] = -1.0
        with pytest.raises(ValidationError, match="cpp_default"):
            CardRecord.model_validate(minimal_card_dict)

    def test_cibc_store_acceptance(self, seed_cards: list[dict]) -> None:
        cibc = CardRecord.model_validate(seed_cards[0])
        assert cibc.store_acceptance["costco_instore"] is False
        assert cibc.store_acceptance["costco_online"] is True

    def test_amex_cobalt_requires_amex(self, seed_cards: list[dict]) -> None:
        cobalt = CardRecord.model_validate(seed_cards[4])
        assert cobalt.requires_amex is True
        assert cobalt.network == "Amex"

    def test_store_overrides_parsed(self, seed_cards: list[dict]) -> None:
        cibc = CardRecord.model_validate(seed_cards[0])
        assert "shoppers_drug_mart" in cibc.store_overrides
        assert isinstance(cibc.store_overrides["shoppers_drug_mart"], StoreOverride)
        assert cibc.store_overrides["shoppers_drug_mart"].rate == 2.0

    def test_model_roundtrip(self, minimal_card_dict: dict) -> None:
        card = CardRecord.model_validate(minimal_card_dict)
        roundtrip = CardRecord.model_validate(card.model_dump())
        assert roundtrip == card
