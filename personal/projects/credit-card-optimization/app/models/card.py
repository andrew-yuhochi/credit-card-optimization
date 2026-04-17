"""Pydantic models for credit card data.

Covers: CardRecord, ApprovalRequirements, StoreOverride, StoreMccEntry.
Schema matches data/cards/cards.json (schema_version 1.0).
"""

from typing import Literal

from pydantic import BaseModel, Field


class ApprovalRequirements(BaseModel):
    """Eligibility thresholds for card approval."""

    min_credit_score: int = Field(ge=0)
    min_personal_income: float = Field(ge=0)
    min_household_income: float = Field(ge=0)
    source: Literal["issuer", "community", "estimated"]
    confidence: Literal["high", "medium", "low"]


class StoreOverride(BaseModel):
    """Per-store earn rate override on a card."""

    rate: float = Field(ge=0)
    source: Literal["issuer", "community", "estimated"]
    note: str = ""


class StoreMccEntry(BaseModel):
    """A store's MCC code and default category from store_mcc_map.json."""

    mcc: str
    default_category: str
    note: str = ""
    acceptance: dict[str, bool] = {}


class CardRecord(BaseModel):
    """A single credit card product with rates, caps, and eligibility info."""

    id: str
    name: str
    issuer: str
    network: Literal["Visa", "Mastercard", "Amex", "Other"]
    annual_fee: float = Field(ge=0)
    first_year_fee: float = Field(ge=0)
    requires_amex: bool
    approval: ApprovalRequirements
    category_rates: dict[str, float]
    category_caps_monthly: dict[str, float] = {}
    store_overrides: dict[str, StoreOverride] = {}
    store_acceptance: dict[str, bool] = {}
    point_system: str
    cpp_default: float = Field(gt=0)
    last_verified_date: str
    source_url: str
    override_notes: str = ""
    is_dummy: bool = False
