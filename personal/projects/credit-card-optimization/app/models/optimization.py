"""Pydantic models for optimization results.

Covers: AssignmentRow, CardSummaryRow, OptimizationResult, DeltaResult.
"""

from typing import Literal

from pydantic import BaseModel

from app.models.card import CardRecord


class AssignmentRow(BaseModel):
    """One row in the spend-assignment table (bucket → card)."""

    bucket_id: str
    label: str
    cardholder: Literal["person1", "person2"] | None = None
    card_id: str
    card_name: str
    monthly_spend: float
    reward_rate_pct: float
    expected_monthly_reward: float
    is_chexy: bool = False
    chexy_net_rate_pct: float | None = None
    explanation: str


class CardSummaryRow(BaseModel):
    """Per-card summary in the recommended wallet."""

    card_id: str
    card_name: str
    annual_fee: float
    assigned_labels: list[str]
    estimated_annual_reward: float
    net_annual_value: float


class OptimizationResult(BaseModel):
    """Full output from a single MILP solve."""

    status: Literal["optimal", "feasible", "infeasible", "timeout"]
    monthly_net_reward: float
    annual_net_reward: float
    baseline_monthly_reward: float
    rows: list[AssignmentRow]
    card_summary: list[CardSummaryRow]
    cards_considered: list[CardRecord]


class DeltaResult(BaseModel):
    """Side-by-side comparison of current vs. optimal wallet."""

    current_annual_reward: float
    optimal_annual_reward: float
    delta_annual: float
    current_result: OptimizationResult
    optimal_result: OptimizationResult
