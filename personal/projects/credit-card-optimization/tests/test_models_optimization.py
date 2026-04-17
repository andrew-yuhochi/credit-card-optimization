"""Tests for app.models.optimization — AssignmentRow, CardSummaryRow, OptimizationResult, DeltaResult."""

import pytest
from pydantic import ValidationError

from app.models.optimization import (
    AssignmentRow,
    CardSummaryRow,
    DeltaResult,
    OptimizationResult,
)


# --- helpers ---


def _assignment(**overrides) -> dict:
    defaults = {
        "bucket_id": "grocery",
        "label": "Grocery",
        "card_id": "cibc_dividend_vi",
        "card_name": "CIBC Dividend Visa Infinite",
        "monthly_spend": 500.0,
        "reward_rate_pct": 4.0,
        "expected_monthly_reward": 20.0,
        "explanation": "CIBC earns 4% on grocery.",
    }
    defaults.update(overrides)
    return defaults


def _card_summary(**overrides) -> dict:
    defaults = {
        "card_id": "cibc_dividend_vi",
        "card_name": "CIBC Dividend Visa Infinite",
        "annual_fee": 120.0,
        "assigned_labels": ["Grocery", "Gas"],
        "estimated_annual_reward": 360.0,
        "net_annual_value": 240.0,
    }
    defaults.update(overrides)
    return defaults


def _result(**overrides) -> dict:
    defaults = {
        "status": "optimal",
        "monthly_net_reward": 45.0,
        "annual_net_reward": 540.0,
        "baseline_monthly_reward": 30.0,
        "rows": [_assignment()],
        "card_summary": [_card_summary()],
        "cards_considered": [],
    }
    defaults.update(overrides)
    return defaults


# --- AssignmentRow ---


class TestAssignmentRow:
    def test_valid(self) -> None:
        row = AssignmentRow(**_assignment())
        assert row.bucket_id == "grocery"
        assert row.cardholder is None
        assert row.is_chexy is False
        assert row.chexy_net_rate_pct is None

    def test_couple_mode_cardholder(self) -> None:
        row = AssignmentRow(**_assignment(cardholder="person2"))
        assert row.cardholder == "person2"

    def test_invalid_cardholder_rejected(self) -> None:
        with pytest.raises(ValidationError, match="cardholder"):
            AssignmentRow(**_assignment(cardholder="person3"))

    def test_chexy_row(self) -> None:
        row = AssignmentRow(
            **_assignment(
                bucket_id="chexy_rent",
                is_chexy=True,
                chexy_net_rate_pct=0.25,
            )
        )
        assert row.is_chexy is True
        assert row.chexy_net_rate_pct == 0.25


# --- CardSummaryRow ---


class TestCardSummaryRow:
    def test_valid(self) -> None:
        cs = CardSummaryRow(**_card_summary())
        assert cs.card_id == "cibc_dividend_vi"
        assert len(cs.assigned_labels) == 2


# --- OptimizationResult ---


class TestOptimizationResult:
    def test_valid_optimal(self) -> None:
        result = OptimizationResult(**_result())
        assert result.status == "optimal"
        assert len(result.rows) == 1

    def test_infeasible(self) -> None:
        result = OptimizationResult(**_result(status="infeasible", rows=[], card_summary=[]))
        assert result.status == "infeasible"

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError, match="status"):
            OptimizationResult(**_result(status="error"))

    def test_model_roundtrip(self) -> None:
        result = OptimizationResult(**_result())
        roundtrip = OptimizationResult.model_validate(result.model_dump())
        assert roundtrip == result


# --- DeltaResult ---


class TestDeltaResult:
    def test_valid(self) -> None:
        dr = DeltaResult(
            current_annual_reward=300.0,
            optimal_annual_reward=540.0,
            delta_annual=240.0,
            current_result=OptimizationResult(**_result(annual_net_reward=300.0)),
            optimal_result=OptimizationResult(**_result(annual_net_reward=540.0)),
        )
        assert dr.delta_annual == 240.0

    def test_model_roundtrip(self) -> None:
        dr = DeltaResult(
            current_annual_reward=300.0,
            optimal_annual_reward=540.0,
            delta_annual=240.0,
            current_result=OptimizationResult(**_result()),
            optimal_result=OptimizationResult(**_result()),
        )
        roundtrip = DeltaResult.model_validate(dr.model_dump())
        assert roundtrip == dr
