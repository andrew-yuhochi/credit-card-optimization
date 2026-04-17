"""Pydantic model for optimization session persistence."""

from datetime import datetime

from pydantic import BaseModel

from app.models.optimization import OptimizationResult
from app.models.spending import SpendingProfile


class OptimizationSession(BaseModel):
    """A saved optimization run (input + result) stored in SQLite."""

    id: str
    user_id: str = "default"
    household_id: str = "default"
    created_at: datetime
    expires_at: datetime
    input_data: SpendingProfile
    result: OptimizationResult | None = None
