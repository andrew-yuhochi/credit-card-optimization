"""Pydantic models for spending profiles and user eligibility.

Covers: CreditScoreBand, IncomeBand, PersonProfile, DummyCard, SpendBucket, SpendingProfile.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CreditScoreBand(str, Enum):
    """Credit score bands for eligibility filtering."""

    FAIR = "fair"              # < 660
    GOOD = "good"              # 660-724
    VERY_GOOD = "very_good"    # 725-759
    EXCELLENT = "excellent"    # 760+


class IncomeBand(str, Enum):
    """Personal income bands for eligibility filtering."""

    UNDER_40K = "under_40k"
    B40_60K = "40k_60k"
    B60_80K = "60k_80k"
    B80_100K = "80k_100k"
    B100_150K = "100k_150k"
    OVER_150K = "over_150k"


class PersonProfile(BaseModel):
    """Eligibility profile for one person in the household."""

    credit_score_band: CreditScoreBand
    income_band: IncomeBand


class DummyCard(BaseModel):
    """User-defined placeholder card for baseline comparison."""

    name: str
    annual_fee: float = Field(default=0.0, ge=0)
    base_rate: float = Field(ge=0)
    category_rates: dict[str, float] = {}


class SpendBucket(BaseModel):
    """A normalized spend bucket fed into the optimizer."""

    bucket_id: str
    monthly_amount: float = Field(ge=0)
    resolved_category: str
    store_slug: str | None = None
    acceptance_constraints: set[str] = set()
    is_chexy: bool = False


class SpendingProfile(BaseModel):
    """Full household spending and eligibility input for the optimizer."""

    user_id: str = "default"
    household_id: str = "default"
    category_spend: dict[str, float]
    store_spend: dict[str, float] = {}
    custom_store_spend: list[tuple[str, str, float]] = []
    chexy_rent_amount: float = Field(default=0.0, ge=0)
    include_amex: bool = False
    person1: PersonProfile
    couple_mode: bool = False
    person2: PersonProfile | None = None
    current_card_ids: list[str] = []
    dummy_cards: list[DummyCard] = []

    @model_validator(mode="after")
    def validate_has_spending(self) -> "SpendingProfile":
        """At least one spend source must have a positive amount."""
        has_category = any(v > 0 for v in self.category_spend.values())
        has_store = any(v > 0 for v in self.store_spend.values())
        has_custom = any(amount > 0 for _, _, amount in self.custom_store_spend)
        has_chexy = self.chexy_rent_amount > 0
        if not (has_category or has_store or has_custom or has_chexy):
            raise ValueError(
                "Spending profile must have at least one positive spend amount "
                "in category_spend, store_spend, custom_store_spend, or chexy_rent_amount"
            )
        return self

    @model_validator(mode="after")
    def validate_couple_mode(self) -> "SpendingProfile":
        """person2 is required when couple_mode is True."""
        if self.couple_mode and self.person2 is None:
            raise ValueError("person2 is required when couple_mode is True")
        return self
