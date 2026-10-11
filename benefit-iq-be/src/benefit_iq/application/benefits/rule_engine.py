"""Benefit Rule Evaluation Engine.

A data-driven, reusable rule engine that evaluates benefit entitlement
based on configurable rules. Rules are evaluated in priority order with
deterministic, explainable results.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import structlog

from benefit_iq.domain.entities.benefit import Benefit
from benefit_iq.domain.entities.card import Card
from benefit_iq.domain.entities.card_product import CardProduct
from benefit_iq.domain.enums.benefit_enums import (
    BenefitFrequency,
    RuleConditionType,
    RuleOperator,
)

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class RuleEvaluationContext:
    """Context data provided to the rule engine for evaluation.

    Contains all information needed to evaluate whether a customer
    is entitled to a benefit without the engine needing to fetch data.
    """

    customer_id: UUID
    card: Card
    card_product: CardProduct
    benefit: Benefit
    current_date: datetime
    accumulated_spend: Decimal = Decimal("0")
    accumulated_spend_in_category: dict[str, Decimal] = field(default_factory=dict)
    usage_count: int = 0
    usage_value: Decimal = Decimal("0")
    customer_tenure_days: int = 0
    transaction_amount: Decimal | None = None
    merchant_category_code: str | None = None
    merchant_name: str | None = None
    country: str | None = None
    currency: str = "USD"
    enrolled: bool = False


@dataclass
class RuleEvaluationResult:
    """Result of evaluating a benefit rule.

    Provides deterministic, explainable results for audit purposes.
    """

    is_entitled: bool
    rule_id: UUID | None
    rule_name: str
    rule_version: int
    benefit_id: UUID
    benefit_name: str
    entitled_value: Decimal
    remaining_value: Decimal
    remaining_usage: int | None
    reasons: list[str] = field(default_factory=list)
    failed_conditions: list[str] = field(default_factory=list)
    evaluation_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def explanation(self) -> str:
        """Human-readable explanation of the evaluation result."""
        if self.is_entitled:
            return f"Entitled to {self.benefit_name}: {'; '.join(self.reasons)}"
        return f"Not entitled to {self.benefit_name}: {'; '.join(self.failed_conditions)}"


class BenefitRuleEngine:
    """Fail-closed entitlement evaluation; limits describe capacity, not eligibility."""

    def evaluate(self, rules, context):
        benefit = context.benefit
        now = context.current_date
        failures = []
        if context.card.status.value != "active" or not (
            context.card.issued_at <= now < context.card.expiry_date
        ):
            failures.append("Card is not active at the calculation timestamp")
        if (
            not benefit.is_active
            or now < benefit.effective_from
            or (benefit.effective_to and now >= benefit.effective_to)
        ):
            failures.append("Benefit is outside its effective dates")
        if benefit.requires_activation and not context.enrolled:
            failures.append("Benefit enrollment is required")
        candidates = [
            r
            for r in rules
            if r.is_active
            and r.benefit_id == benefit.id
            and r.card_product_id in (None, context.card.card_product_id)
            and (not r.effective_from or r.effective_from <= now)
            and (not r.effective_to or now < r.effective_to)
        ]
        # A later version supersedes an older version of the same named policy.
        latest = {}
        for r in candidates:
            key = (r.name, r.card_product_id)
            if key not in latest or r.version > latest[key].version:
                latest[key] = r
        for rule in sorted(latest.values(), key=lambda r: (r.priority, -r.version, str(r.id))):
            failed = list(failures)
            if rule.spend_currency and rule.spend_currency != context.currency:
                failed.append("Spend currency does not match the rule")
            if (
                rule.min_spend_amount is not None
                and context.accumulated_spend < rule.min_spend_amount
            ):
                failed.append(
                    f"Minimum spend {rule.min_spend_amount} not reached; actual {context.accumulated_spend}"
                )
            if (
                rule.max_spend_amount is not None
                and context.accumulated_spend > rule.max_spend_amount
            ):
                failed.append("Maximum spend exceeded")
            for condition in rule.conditions:
                if not self._evaluate_condition(condition, context):
                    failed.append(
                        f"Condition failed: {condition.condition_type.value} {condition.operator.value} {condition.value}"
                    )
            limits = [
                v
                for v in (rule.usage_limit, self._get_period_limit(rule, benefit.frequency))
                if v is not None
            ]
            if not failed:
                return self._result(context, rule, [], min(limits) if limits else None)
            failures.extend(failed)
        if not rules and not failures:
            return self._result(context, None, [], None)
        return self._result(
            context,
            None,
            list(dict.fromkeys(failures)) or ["No rule is effective at this timestamp"],
            None,
        )

    @staticmethod
    def _result(context, rule, failed, limit):
        from benefit_iq.domain.enums.benefit_enums import BenefitCategory, BenefitValueType

        b = context.benefit
        cash = b.value_type == BenefitValueType.MONETARY and b.category not in (
            BenefitCategory.INSURANCE,
            BenefitCategory.PURCHASE_PROTECTION,
            BenefitCategory.EXTENDED_WARRANTY,
        )
        value = b.max_value if cash and not failed else Decimal("0")
        if b.value_type == BenefitValueType.COUNT and limit is None:
            limit = int(b.max_value) if b.max_value > 0 else None
        return RuleEvaluationResult(
            is_entitled=not failed,
            rule_id=rule.id if rule else None,
            rule_name=rule.name if rule else "product_linkage",
            rule_version=rule.version if rule else 0,
            benefit_id=b.id,
            benefit_name=b.name,
            entitled_value=value,
            remaining_value=max(Decimal("0"), value - context.usage_value),
            remaining_usage=max(0, limit - context.usage_count) if limit is not None else None,
            reasons=[f"Included with {context.card_product.name}"] if not failed else [],
            failed_conditions=failed,
            evaluation_timestamp=context.current_date,
        )

    def _evaluate_condition(self, condition, context):
        values = {
            RuleConditionType.CARD_TIER: context.card_product.tier.value,
            RuleConditionType.CARD_NETWORK: context.card_product.network.value,
            RuleConditionType.CARD_PRODUCT: str(context.card.card_product_id),
            RuleConditionType.MIN_SPEND: context.accumulated_spend,
            RuleConditionType.MAX_SPEND: context.accumulated_spend,
            RuleConditionType.ACCUMULATED_SPEND: context.accumulated_spend,
            RuleConditionType.MERCHANT_CATEGORY: context.merchant_category_code,
            RuleConditionType.TRANSACTION_CATEGORY: context.merchant_category_code,
            RuleConditionType.MERCHANT: context.merchant_name,
            RuleConditionType.GEOGRAPHY: context.country,
            RuleConditionType.CURRENCY: context.currency,
            RuleConditionType.CUSTOMER_TENURE: context.customer_tenure_days,
            RuleConditionType.ACTIVATION_REQUIRED: str(context.enrolled).lower(),
            RuleConditionType.TIME_PERIOD: context.current_date.isoformat(),
        }
        actual = values.get(condition.condition_type)
        if actual is None:
            return False
        return self._compare(actual, condition.operator, condition.value, condition.value_to)

    @staticmethod
    def _compare(actual, operator, expected, upper=None):
        from decimal import InvalidOperation

        a, b = str(actual).lower(), str(expected).lower()
        if operator == RuleOperator.EXISTS:
            return bool(a)
        if operator == RuleOperator.EQ:
            return a == b
        if operator == RuleOperator.NEQ:
            return a != b
        if operator in (RuleOperator.IN, RuleOperator.NOT_IN):
            present = a in [v.strip() for v in b.split(",")]
            return present if operator == RuleOperator.IN else not present
        if operator == RuleOperator.CONTAINS:
            return b in a
        try:
            a, b = Decimal(a), Decimal(b)
            if not a.is_finite() or not b.is_finite():
                return False
            if operator == RuleOperator.BETWEEN:
                return upper is not None and a >= b and a <= Decimal(upper)
            return {
                RuleOperator.GT: a > b,
                RuleOperator.GTE: a >= b,
                RuleOperator.LT: a < b,
                RuleOperator.LTE: a <= b,
            }.get(operator, False)
        except InvalidOperation, ValueError:
            return False

    @staticmethod
    def _get_period_limit(rule, frequency):
        return {
            BenefitFrequency.MONTHLY: rule.monthly_limit,
            BenefitFrequency.QUARTERLY: rule.quarterly_limit,
            BenefitFrequency.ANNUAL: rule.annual_limit,
        }.get(frequency)
