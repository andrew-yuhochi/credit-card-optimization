"""Tests for app.models.session — OptimizationSession."""

from datetime import datetime, timedelta, timezone

from app.models.optimization import OptimizationResult
from app.models.session import OptimizationSession
from app.models.spending import (
    CreditScoreBand,
    IncomeBand,
    PersonProfile,
    SpendingProfile,
)


def _spending_profile() -> SpendingProfile:
    return SpendingProfile(
        category_spend={"grocery": 500.0},
        person1=PersonProfile(
            credit_score_band=CreditScoreBand.GOOD,
            income_band=IncomeBand.B60_80K,
        ),
    )


def _result() -> OptimizationResult:
    return OptimizationResult(
        status="optimal",
        monthly_net_reward=45.0,
        annual_net_reward=540.0,
        baseline_monthly_reward=30.0,
        rows=[],
        card_summary=[],
        cards_considered=[],
    )


class TestOptimizationSession:
    def test_valid_without_result(self) -> None:
        now = datetime.now(tz=timezone.utc)
        session = OptimizationSession(
            id="abc-123",
            created_at=now,
            expires_at=now + timedelta(hours=24),
            input_data=_spending_profile(),
        )
        assert session.result is None
        assert session.user_id == "default"
        assert session.household_id == "default"

    def test_valid_with_result(self) -> None:
        now = datetime.now(tz=timezone.utc)
        session = OptimizationSession(
            id="abc-456",
            created_at=now,
            expires_at=now + timedelta(hours=24),
            input_data=_spending_profile(),
            result=_result(),
        )
        assert session.result is not None
        assert session.result.status == "optimal"

    def test_model_roundtrip(self) -> None:
        now = datetime.now(tz=timezone.utc)
        session = OptimizationSession(
            id="round-trip",
            created_at=now,
            expires_at=now + timedelta(hours=24),
            input_data=_spending_profile(),
            result=_result(),
        )
        roundtrip = OptimizationSession.model_validate(session.model_dump())
        assert roundtrip == session
