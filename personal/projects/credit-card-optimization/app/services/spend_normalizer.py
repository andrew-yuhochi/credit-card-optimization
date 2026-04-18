"""Spend bucket normalizer and dummy card builder.

SpendBucketNormalizer converts a SpendingProfile into a flat list of SpendBucket
objects ready for the MILP optimizer. DummyCardBuilder converts user-defined
DummyCard objects into CardRecord objects indistinguishable from real cards.
"""

import logging
from typing import Final

from app.models.card import ApprovalRequirements, CardRecord, StoreMccEntry
from app.models.spending import DummyCard, SpendBucket, SpendingProfile

logger = logging.getLogger(__name__)

# All standard spend categories the optimizer understands.
STANDARD_CATEGORIES: Final[list[str]] = [
    "grocery",
    "gas",
    "dining",
    "transit",
    "recurring",
    "pharmacy",
    "travel",
    "hotel",
    "entertainment",
    "streaming",
    "online",
    "other",
    "wholesale",
    "department_store",
    "home_improvement",
    "pet",
    "healthcare",
    "education",
    "insurance",
]


class SpendBucketNormalizer:
    """Converts a SpendingProfile into a flat list of SpendBucket objects.

    Resolution order:
    1. category_spend entries  → one bucket per category key with amount > 0
    2. store_spend entries     → resolved via store_mcc_map; unknown slugs default
                                 to "other" and are logged at WARNING
    3. custom_store_spend      → one bucket per entry using the caller-provided
                                 category_override
    4. chexy_rent_amount       → single "chexy_rent" bucket with is_chexy=True

    Zero-amount buckets are excluded from the output list.
    """

    def normalize(
        self,
        profile: SpendingProfile,
        store_mcc_map: dict[str, StoreMccEntry],
    ) -> list[SpendBucket]:
        """Return a flat list of non-zero SpendBucket objects from the profile."""
        buckets: list[SpendBucket] = []

        # 1. Category spend
        for category_key, amount in profile.category_spend.items():
            if amount > 0:
                buckets.append(
                    SpendBucket(
                        bucket_id=category_key,
                        monthly_amount=amount,
                        resolved_category=category_key,
                        store_slug=None,
                    )
                )

        # 2. Store spend — resolve category from MCC map
        for slug, amount in profile.store_spend.items():
            if amount > 0:
                entry = store_mcc_map.get(slug)
                if entry is not None:
                    resolved_category = entry.default_category
                else:
                    logger.warning(
                        "Unknown store slug '%s' in store_spend — defaulting to 'other'",
                        slug,
                    )
                    resolved_category = "other"
                buckets.append(
                    SpendBucket(
                        bucket_id=slug,
                        monthly_amount=amount,
                        resolved_category=resolved_category,
                        store_slug=slug,
                    )
                )

        # 3. Custom store spend
        for store_name, category_override, amount in profile.custom_store_spend:
            if amount > 0:
                bucket_id = f"custom_{store_name.lower().replace(' ', '_')}"
                buckets.append(
                    SpendBucket(
                        bucket_id=bucket_id,
                        monthly_amount=amount,
                        resolved_category=category_override,
                        store_slug=None,
                    )
                )

        # 4. Chexy rent
        if profile.chexy_rent_amount > 0:
            buckets.append(
                SpendBucket(
                    bucket_id="chexy_rent",
                    monthly_amount=profile.chexy_rent_amount,
                    resolved_category="other",
                    store_slug=None,
                    is_chexy=True,
                )
            )

        return buckets


class DummyCardBuilder:
    """Converts user-defined DummyCard objects into CardRecord objects.

    Dummy cards are treated identically to real cards by the optimizer.
    Any category not explicitly specified in DummyCard.category_rates receives
    the card's base_rate. All approval thresholds are set to zero so a dummy
    card is always eligible.
    """

    def build(self, dummy_cards: list[DummyCard]) -> list[CardRecord]:
        """Return a CardRecord for each DummyCard in the input list."""
        records: list[CardRecord] = []
        for i, dummy in enumerate(dummy_cards):
            card_id = f"dummy_{i}"
            category_rates = {
                category: dummy.category_rates.get(category, dummy.base_rate)
                for category in STANDARD_CATEGORIES
            }
            record = CardRecord(
                id=card_id,
                name=dummy.name,
                issuer="Custom",
                network="Other",
                annual_fee=dummy.annual_fee,
                first_year_fee=dummy.annual_fee,
                requires_amex=False,
                approval=ApprovalRequirements(
                    min_credit_score=0,
                    min_personal_income=0,
                    min_household_income=0,
                    source="estimated",
                    confidence="low",
                ),
                category_rates=category_rates,
                category_caps_monthly={},
                store_overrides={},
                store_acceptance={},
                point_system="cashback",
                cpp_default=1.0,
                last_verified_date="2026-04-17",
                source_url="",
                is_dummy=True,
            )
            records.append(record)
            logger.debug("Built dummy card '%s' as id='%s'", dummy.name, card_id)
        return records
