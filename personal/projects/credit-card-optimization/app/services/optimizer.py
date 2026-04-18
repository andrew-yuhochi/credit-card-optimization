"""MILP-based credit card spend optimizer.

OptimizerBase: ABC defining the solver interface.
MILPOptimizer: concrete solver using PuLP + CBC.

The optimizer assigns spend buckets to cards to maximize net monthly reward
minus annualized fees, subject to coverage, spend caps, and store acceptance
constraints.
"""

import abc
import logging
import os
import time
from collections import defaultdict

import pulp

from app.models.card import CardRecord
from app.models.optimization import (
    AssignmentRow,
    CardSummaryRow,
    OptimizationResult,
)
from app.models.spending import SpendBucket

logger = logging.getLogger(__name__)


class OptimizerBase(abc.ABC):
    """Abstract base class for card wallet optimizers."""

    @abc.abstractmethod
    def solve(
        self,
        cards: list[CardRecord],
        buckets: list[SpendBucket],
        couple_mode: bool = False,
        forced_excluded_card_ids: set[str] | None = None,
    ) -> OptimizationResult:
        """Run the optimization and return a result.

        Args:
            cards: Eligible card pool (post-eligibility-filter).
            buckets: Normalized spend buckets from SpendBucketNormalizer.
            couple_mode: When True, each card can be held by two people
                independently (person1 and person2).
            forced_excluded_card_ids: When set, those card ids are pinned to
                y=0 (not selected). Used by the Delta Calculator for the
                "current cards only" constrained solve.
        """
        ...


def _effective_rate(card: CardRecord, bucket: SpendBucket) -> float:
    """Return the effective earn rate (as a decimal) for a card/bucket pair.

    Resolution order:
    1. Chexy bucket: use 'other' rate minus the 1.75% processing fee, floored at 0.
    2. Store override: use the per-store override rate.
    3. Category rate: use the category rate, falling back to 'other'.
    """
    if bucket.is_chexy:
        other_rate = card.category_rates.get("other", 0.0) / 100.0
        return max(0.0, other_rate - 0.0175)
    if bucket.store_slug and bucket.store_slug in card.store_overrides:
        return card.store_overrides[bucket.store_slug].rate / 100.0
    category = bucket.resolved_category
    rate = card.category_rates.get(category, card.category_rates.get("other", 0.0))
    return rate / 100.0


class MILPOptimizer(OptimizerBase):
    """Solves the card-wallet optimization problem with PuLP + CBC.

    Formulation:
        Maximize Σ x[c,p,k] * rate(c,k) * cpp(c)  -  Σ y[c,p] * annual_fee(c)/12
        Subject to:
            Coverage:          Σ_c Σ_p x[c,p,k] == monthly_amount(k)  ∀k
            Linking:           x[c,p,k] <= monthly_amount(k) * y[c,p]  ∀c,p,k
            Monthly caps:      Σ_k∈cap_group x[c,p,k] <= cap_amount   ∀c,p,cap
            Store acceptance:  x[c,p,k] == 0  if card c not accepted at bucket k
            Forced exclusions: y[c,p] == 0  for forced_excluded_card_ids
    """

    def solve(
        self,
        cards: list[CardRecord],
        buckets: list[SpendBucket],
        couple_mode: bool = False,
        forced_excluded_card_ids: set[str] | None = None,
    ) -> OptimizationResult:
        """Run the MILP solve and return an OptimizationResult."""
        persons = [0] if not couple_mode else [0, 1]

        # Baseline: flat 2% on all spend regardless of card selection
        baseline = sum(b.monthly_amount for b in buckets) * 0.02

        # Empty card pool → infeasible immediately
        if not cards:
            logger.warning("No cards provided; returning infeasible result")
            return OptimizationResult(
                status="infeasible",
                monthly_net_reward=0.0,
                annual_net_reward=0.0,
                baseline_monthly_reward=baseline,
                rows=[],
                card_summary=[],
                cards_considered=list(cards),
            )

        cards_idx = {i: card for i, card in enumerate(cards)}
        buckets_idx = {j: bucket for j, bucket in enumerate(buckets)}
        num_cards = len(cards)

        prob = pulp.LpProblem("card_optimizer", pulp.LpMaximize)

        # --- Decision variables ---
        # y[c, p] = 1 if person p holds card c
        y: dict[tuple[int, int], pulp.LpVariable] = {
            (c, p): pulp.LpVariable(f"y_{c}_{p}", cat="Binary")
            for c in range(num_cards)
            for p in persons
        }
        # x[c, p, k] = dollars allocated to card c, person p, bucket k
        x: dict[tuple[int, int, int], pulp.LpVariable] = {
            (c, p, k): pulp.LpVariable(f"x_{c}_{p}_{k}", lowBound=0)
            for c in range(num_cards)
            for p in persons
            for k in buckets_idx
        }

        # --- Objective ---
        reward_terms = [
            x[c, p, k] * _effective_rate(cards_idx[c], buckets_idx[k]) * cards_idx[c].cpp_default
            for c in range(num_cards)
            for p in persons
            for k in buckets_idx
        ]
        fee_terms = [
            y[c, p] * cards_idx[c].annual_fee / 12.0
            for c in range(num_cards)
            for p in persons
        ]
        prob += pulp.lpSum(reward_terms) - pulp.lpSum(fee_terms)

        # --- Constraint 1: Coverage ---
        for k, bucket in buckets_idx.items():
            prob += (
                pulp.lpSum(x[c, p, k] for c in range(num_cards) for p in persons)
                == bucket.monthly_amount,
                f"coverage_{k}",
            )

        # --- Constraint 2: Linking (can only spend on a selected card) ---
        for c in range(num_cards):
            for p in persons:
                for k, bucket in buckets_idx.items():
                    prob += (
                        x[c, p, k] <= bucket.monthly_amount * y[c, p],
                        f"link_{c}_{p}_{k}",
                    )

        # --- Constraint 3: Monthly spend caps ---
        for c, card in cards_idx.items():
            for cap_key, cap_amount in card.category_caps_monthly.items():
                if cap_key.startswith("_"):
                    # Combined cap: look up the group definition
                    cap_categories = card.category_cap_groups.get(cap_key, [])
                else:
                    # Single-category cap
                    cap_categories = [cap_key]

                relevant_k = [
                    k
                    for k, b in buckets_idx.items()
                    if b.resolved_category in cap_categories
                ]
                if not relevant_k:
                    continue
                for p in persons:
                    prob += (
                        pulp.lpSum(x[c, p, k] for k in relevant_k) <= cap_amount,
                        f"cap_{c}_{p}_{cap_key}",
                    )

        # --- Constraint 4: Store acceptance ---
        for c, card in cards_idx.items():
            for k, bucket in buckets_idx.items():
                if bucket.store_slug and not card.store_acceptance.get(
                    bucket.store_slug + "_instore", True
                ):
                    for p in persons:
                        prob += (
                            x[c, p, k] == 0,
                            f"acceptance_{c}_{p}_{k}",
                        )

        # --- Constraint 5: Forced exclusions ---
        if forced_excluded_card_ids:
            for c, card in cards_idx.items():
                if card.id in forced_excluded_card_ids:
                    for p in persons:
                        prob += (
                            y[c, p] == 0,
                            f"forced_excl_{c}_{p}",
                        )

        # --- Solve ---
        time_limit = int(os.getenv("MILP_TIME_LIMIT_SECONDS", "30"))
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)

        start = time.perf_counter()
        prob.solve(solver)
        elapsed = time.perf_counter() - start

        logger.info(
            "MILP solve completed in %.3fs, status: %s",
            elapsed,
            pulp.LpStatus[prob.status],
        )

        # --- Map PuLP status to our status string ---
        if prob.status == 1:
            solve_status = "optimal"
        elif prob.status in (-1, -2, -3):
            solve_status = "infeasible"
        else:
            # status == 0: not solved or CBC hit time limit with feasible incumbent
            if elapsed >= time_limit - 1:
                solve_status = "timeout"
            else:
                solve_status = "feasible"

        # --- Infeasible: return empty result ---
        if solve_status == "infeasible":
            return OptimizationResult(
                status="infeasible",
                monthly_net_reward=0.0,
                annual_net_reward=0.0,
                baseline_monthly_reward=baseline,
                rows=[],
                card_summary=[],
                cards_considered=list(cards),
            )

        # --- Build assignment rows ---
        EPSILON = 0.01

        card_monthly_rewards: dict[str, float] = defaultdict(float)
        card_labels: dict[str, list[str]] = defaultdict(list)
        selected_card_ids_per_person: dict[int, set[str]] = defaultdict(set)
        rows: list[AssignmentRow] = []

        for c, card in cards_idx.items():
            for p in persons:
                for k, bucket in buckets_idx.items():
                    alloc = pulp.value(x[c, p, k])
                    if alloc is None or alloc < EPSILON:
                        continue
                    rate = _effective_rate(card, bucket)
                    monthly_reward = alloc * rate * card.cpp_default
                    card_monthly_rewards[card.id] += monthly_reward
                    label = bucket.bucket_id.replace("_", " ").title()
                    card_labels[card.id].append(label)
                    selected_card_ids_per_person[p].add(card.id)

                    cardholder: str | None
                    if len(persons) > 1:
                        cardholder = "person1" if p == 0 else "person2"
                    else:
                        cardholder = None

                    rows.append(
                        AssignmentRow(
                            bucket_id=bucket.bucket_id,
                            label=label,
                            cardholder=cardholder,
                            card_id=card.id,
                            card_name=card.name,
                            monthly_spend=alloc,
                            reward_rate_pct=rate * 100,
                            expected_monthly_reward=monthly_reward,
                            is_chexy=bucket.is_chexy,
                            chexy_net_rate_pct=(rate * 100) if bucket.is_chexy else None,
                            explanation="",  # filled by ExplanationGenerator in TASK-008
                        )
                    )

        # Stable sort: bucket_id then card_name
        rows.sort(key=lambda r: (r.bucket_id, r.card_name))

        # --- Build card summaries ---
        all_selected_card_ids: set[str] = set().union(
            *selected_card_ids_per_person.values()
        ) if selected_card_ids_per_person else set()

        card_summary: list[CardSummaryRow] = []
        for c, card in cards_idx.items():
            if card.id not in all_selected_card_ids:
                continue
            annual_reward = card_monthly_rewards[card.id] * 12
            net_annual = annual_reward - card.annual_fee
            card_summary.append(
                CardSummaryRow(
                    card_id=card.id,
                    card_name=card.name,
                    annual_fee=card.annual_fee,
                    assigned_labels=list(dict.fromkeys(card_labels[card.id])),
                    estimated_annual_reward=annual_reward,
                    net_annual_value=net_annual,
                )
            )

        total_monthly_reward = sum(r.expected_monthly_reward for r in rows)
        total_annual_fee = sum(cs.annual_fee for cs in card_summary)
        annual_net = total_monthly_reward * 12 - total_annual_fee

        return OptimizationResult(
            status=solve_status,
            monthly_net_reward=total_monthly_reward - total_annual_fee / 12.0,
            annual_net_reward=annual_net,
            baseline_monthly_reward=baseline,
            rows=rows,
            card_summary=card_summary,
            cards_considered=list(cards),
        )
