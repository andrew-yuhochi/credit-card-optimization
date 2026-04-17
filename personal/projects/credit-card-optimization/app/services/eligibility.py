"""Eligibility pre-filter — removes ineligible cards before the MILP solve.

Filter rules (applied in order per TDD Section 2.2):
1. Amex toggle: remove requires_amex cards when include_amex is False
2. Credit score: remove cards above person's credit score band max
3. Personal income: remove cards above person's income band max
4. Household income (couple mode): retain if combined income meets threshold
5. Store acceptance: remove cards excluded at stores the user shops at
"""

import logging
from typing import ClassVar

from app.models.card import CardRecord
from app.models.spending import CreditScoreBand, IncomeBand, SpendingProfile

logger = logging.getLogger(__name__)


class EligibilityFilter:
    """Filters a card pool down to cards eligible for a given spending profile."""

    # Upper bound of each credit score band (used for >= comparison against
    # card's min_credit_score). FAIR's max is 659 because the band is "< 660".
    CREDIT_SCORE_MAX: ClassVar[dict[CreditScoreBand, int]] = {
        CreditScoreBand.FAIR: 659,
        CreditScoreBand.GOOD: 724,
        CreditScoreBand.VERY_GOOD: 759,
        CreditScoreBand.EXCELLENT: 900,
    }

    # Upper bound of each income band (used for >= comparison against
    # card's min_personal_income).
    INCOME_MAX: ClassVar[dict[IncomeBand, float]] = {
        IncomeBand.UNDER_40K: 39_999,
        IncomeBand.B40_60K: 59_999,
        IncomeBand.B60_80K: 79_999,
        IncomeBand.B80_100K: 99_999,
        IncomeBand.B100_150K: 149_999,
        IncomeBand.OVER_150K: 999_999,
    }

    @classmethod
    def filter(
        cls, cards: list[CardRecord], profile: SpendingProfile
    ) -> list[CardRecord]:
        """Return only the cards eligible for the given spending profile.

        Cards that are dummy (is_dummy=True) always pass all filters.
        """
        initial_count = len(cards)
        result = list(cards)

        result = cls._filter_amex(result, profile)
        result = cls._filter_eligibility(result, profile)
        result = cls._filter_store_acceptance(result, profile)

        removed = initial_count - len(result)
        logger.debug(
            "Eligibility filter: %d/%d cards removed, %d remaining",
            removed,
            initial_count,
            len(result),
        )
        return result

    @classmethod
    def _filter_amex(
        cls, cards: list[CardRecord], profile: SpendingProfile
    ) -> list[CardRecord]:
        if profile.include_amex:
            return cards
        before = len(cards)
        result = [c for c in cards if not c.requires_amex or c.is_dummy]
        logger.debug(
            "Amex filter: removed %d cards (include_amex=False)",
            before - len(result),
        )
        return result

    @classmethod
    def _filter_eligibility(
        cls, cards: list[CardRecord], profile: SpendingProfile
    ) -> list[CardRecord]:
        """Filter by credit score, personal income, and household income."""
        p1_score_max = cls.CREDIT_SCORE_MAX[profile.person1.credit_score_band]
        p1_income_max = cls.INCOME_MAX[profile.person1.income_band]

        if profile.couple_mode and profile.person2 is not None:
            p2_score_max = cls.CREDIT_SCORE_MAX[profile.person2.credit_score_band]
            p2_income_max = cls.INCOME_MAX[profile.person2.income_band]
            combined_income = p1_income_max + p2_income_max
        else:
            p2_score_max = None
            p2_income_max = None
            combined_income = p1_income_max

        before = len(cards)
        result: list[CardRecord] = []
        for card in cards:
            if card.is_dummy:
                result.append(card)
                continue

            # Person 1 qualifies individually?
            p1_qualifies = (
                card.approval.min_credit_score <= p1_score_max
                and card.approval.min_personal_income <= p1_income_max
            )

            if profile.couple_mode and p2_score_max is not None and p2_income_max is not None:
                # Person 2 qualifies individually?
                p2_qualifies = (
                    card.approval.min_credit_score <= p2_score_max
                    and card.approval.min_personal_income <= p2_income_max
                )
                # Household income qualification
                household_qualifies = (
                    card.approval.min_household_income <= combined_income
                    and (
                        card.approval.min_credit_score <= p1_score_max
                        or card.approval.min_credit_score <= p2_score_max
                    )
                )
                if p1_qualifies or p2_qualifies or household_qualifies:
                    result.append(card)
            else:
                if p1_qualifies:
                    result.append(card)

        logger.debug(
            "Eligibility filter (score+income): removed %d cards",
            before - len(result),
        )
        return result

    @classmethod
    def _filter_store_acceptance(
        cls, cards: list[CardRecord], profile: SpendingProfile
    ) -> list[CardRecord]:
        """Remove cards that are not accepted at stores the user shops at.

        Only filters based on stores in store_spend (not category_spend).
        """
        # Collect store acceptance keys the user cares about
        # e.g., if user shops at "costco", check "costco_instore" and "costco_online"
        store_slugs = set(profile.store_spend.keys())
        if not store_slugs:
            return cards

        before = len(cards)
        result: list[CardRecord] = []
        for card in cards:
            if card.is_dummy:
                result.append(card)
                continue

            excluded = False
            for slug in store_slugs:
                if profile.store_spend.get(slug, 0) <= 0:
                    continue
                # Check if the card has any store_acceptance entries for this store
                # Convention: keys like "costco_instore", "costco_online"
                for acc_key, accepted in card.store_acceptance.items():
                    if acc_key.startswith(slug) and not accepted:
                        # Card is not accepted at this store for at least one channel
                        # But only exclude if ALL channels for this store are rejected
                        pass
                # A card is only fully excluded from a store if it cannot be used
                # at that store at all. If it has costco_instore=False but
                # costco_online=True, it can still be used (online).
                # Only exclude if every acceptance entry for this slug is False.
                relevant = {
                    k: v
                    for k, v in card.store_acceptance.items()
                    if k.startswith(slug)
                }
                if relevant and not any(relevant.values()):
                    excluded = True
                    break

            if not excluded:
                result.append(card)

        logger.debug(
            "Store acceptance filter: removed %d cards", before - len(result)
        )
        return result
