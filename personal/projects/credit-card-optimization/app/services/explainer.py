"""Explanation generator for optimization assignment rows.

ExplanationGenerator.annotate() populates the `explanation` field on each
AssignmentRow using one of four templates:
  1. Chexy — rent row with Chexy fee applied
  2. Store override — card has a per-store rate override for this bucket
  3. Cap-constrained split — bucket spend split across two cards (cap hit)
  4. Category rate — default case, card earns best category rate
"""

import logging
from collections import defaultdict

from app.models.card import CardRecord
from app.models.optimization import AssignmentRow
from app.models.spending import SpendBucket

logger = logging.getLogger(__name__)


class ExplanationGenerator:
    """Annotates each AssignmentRow with a human-readable explanation."""

    def annotate(
        self,
        rows: list[AssignmentRow],
        cards_by_id: dict[str, CardRecord],
        buckets_by_id: dict[str, SpendBucket],
    ) -> list[AssignmentRow]:
        """Return a new list of AssignmentRow with explanation fields populated.

        Does not mutate input rows — returns copies with explanation set.

        Args:
            rows: Assignment rows produced by MILPOptimizer.solve().
            cards_by_id: Mapping of card id → CardRecord.
            buckets_by_id: Mapping of bucket_id → SpendBucket.

        Returns:
            New list of AssignmentRow with explanation populated on every row.
        """
        # Group rows by bucket_id to detect cap-constrained splits.
        # A split occurs when two or more rows share the same bucket_id.
        rows_by_bucket: dict[str, list[AssignmentRow]] = defaultdict(list)
        for row in rows:
            rows_by_bucket[row.bucket_id].append(row)

        # For each split bucket, sort descending by reward_rate_pct so index 0
        # is the primary (highest-rate) card.
        for bucket_id in rows_by_bucket:
            rows_by_bucket[bucket_id].sort(key=lambda r: r.reward_rate_pct, reverse=True)

        annotated: list[AssignmentRow] = []
        for row in rows:
            card = cards_by_id.get(row.card_id)
            bucket = buckets_by_id.get(row.bucket_id)

            if card is None or bucket is None:
                logger.warning(
                    "Missing card or bucket during explanation: card_id=%s bucket_id=%s — "
                    "using fallback explanation",
                    row.card_id,
                    row.bucket_id,
                )
                annotated.append(
                    row.model_copy(
                        update={"explanation": f"{row.card_name} earns {row.reward_rate_pct:.1f}%."}
                    )
                )
                continue

            explanation = self._build_explanation(row, card, bucket, rows_by_bucket, cards_by_id)
            annotated.append(row.model_copy(update={"explanation": explanation}))

        return annotated

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_explanation(
        self,
        row: AssignmentRow,
        card: CardRecord,
        bucket: SpendBucket,
        rows_by_bucket: dict[str, list[AssignmentRow]],
        cards_by_id: dict[str, CardRecord],
    ) -> str:
        """Select and render the correct explanation template for one row."""

        # --- Template 1: Chexy ---
        if bucket.is_chexy:
            other_rate = card.category_rates.get("other", 0.0)
            net_rate = row.reward_rate_pct  # already computed by the optimizer
            return (
                f"{card.name} earns {other_rate:.1f}% on all purchases (other category); "
                f"after Chexy's 1.75% fee, the net return on rent is {net_rate:.2f}%."
            )

        # --- Template 2: Store override ---
        if bucket.store_slug is not None and bucket.store_slug in card.store_overrides:
            store_label = bucket.store_slug.replace("_", " ").title()
            resolved_cat = bucket.resolved_category.replace("_", " ").title()
            return (
                f"{card.name} earns {row.reward_rate_pct:.1f}% at {store_label} "
                f"— it is classified as {resolved_cat} by {card.issuer} "
                f"and this is the highest rate among eligible cards."
            )

        # --- Template 4: Cap-constrained split (detected via bucket group) ---
        bucket_rows = rows_by_bucket.get(row.bucket_id, [])
        if len(bucket_rows) > 1:
            # This bucket is split. Determine if this row is the overflow card
            # (any row that is NOT the highest-rate row for this bucket).
            primary_row = bucket_rows[0]  # highest rate (sorted descending earlier)
            if row.card_id != primary_row.card_id or row.cardholder != primary_row.cardholder:
                primary_card = cards_by_id.get(primary_row.card_id)
                total_spend = sum(r.monthly_spend for r in bucket_rows)
                overflow_spend = row.monthly_spend

                if bucket.store_slug:
                    store_or_cat = bucket.store_slug.replace("_", " ").title()
                else:
                    store_or_cat = bucket.resolved_category.replace("_", " ").title()

                primary_name = primary_card.name if primary_card else primary_row.card_name
                return (
                    f"Spend at {store_or_cat} was split: {primary_name} earns "
                    f"{primary_row.reward_rate_pct:.1f}% on ${primary_row.monthly_spend:.0f} "
                    f"of ${total_spend:.0f} (cap reached); the remaining "
                    f"${overflow_spend:.0f} is routed to {card.name} "
                    f"at {row.reward_rate_pct:.1f}%."
                )

        # --- Template 3: Category rate (default) ---
        resolved_cat = bucket.resolved_category.replace("_", " ").title()
        return (
            f"{card.name} earns {row.reward_rate_pct:.1f}% on {resolved_cat} spending; "
            f"no eligible card earns more in this category."
        )
