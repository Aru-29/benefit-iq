from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from benefit_iq.application.benefits.rule_engine import BenefitRuleEngine, RuleEvaluationContext
from benefit_iq.application.benefits.utilization_service import BenefitUtilizationService
from benefit_iq.domain.entities.benefit_rule import BenefitRule, RuleCondition
from benefit_iq.domain.enums.benefit_enums import (
    BenefitCategory,
    BenefitFrequency,
    BenefitValueType,
    RuleConditionType,
    RuleOperator,
)

UTC = UTC
NOW = datetime(2024, 2, 29, 12, tzinfo=UTC)


@pytest.fixture
def context():
    product = SimpleNamespace(
        id=uuid4(),
        name="Demo",
        tier=SimpleNamespace(value="gold"),
        network=SimpleNamespace(value="visa"),
    )
    card = SimpleNamespace(
        id=uuid4(),
        card_product_id=product.id,
        status=SimpleNamespace(value="active"),
        issued_at=datetime(2023, 1, 1, tzinfo=UTC),
        expiry_date=datetime(2028, 1, 1, tzinfo=UTC),
    )
    benefit = SimpleNamespace(
        id=uuid4(),
        name="Travel",
        max_value=Decimal("100.10"),
        currency="USD",
        frequency=BenefitFrequency.MONTHLY,
        value_type=BenefitValueType.MONETARY,
        category=BenefitCategory.TRAVEL_CREDIT,
        requires_activation=False,
        is_active=True,
        effective_from=card.issued_at,
        effective_to=None,
    )
    return RuleEvaluationContext(uuid4(), card, product, benefit, NOW)


def rule(c, **kwargs):
    return BenefitRule(
        id=uuid4(),
        benefit_id=c.benefit.id,
        card_product_id=c.card_product.id,
        name="eligibility",
        description=None,
        version=kwargs.pop("version", 1),
        priority=10,
        **kwargs,
    )


def test_exhaustion_preserves_original_entitlement(context):
    decision = BenefitRuleEngine().evaluate(
        [rule(context, usage_limit=1)],
        replace(context, usage_count=1, usage_value=Decimal("100.10")),
    )
    assert decision.is_entitled
    assert decision.entitled_value == Decimal("100.10")
    assert decision.remaining_value == 0
    assert decision.remaining_usage == 0


def test_newer_version_cannot_fall_back_to_lax_old_rule(context):
    decision = BenefitRuleEngine().evaluate(
        [rule(context), rule(context, version=2, min_spend_amount=Decimal("1000"))], context
    )
    assert not decision.is_entitled
    assert "Minimum spend" in decision.explanation


def test_enrollment_is_not_assumed(context):
    context.benefit.requires_activation = True
    assert not BenefitRuleEngine().evaluate([], context).is_entitled
    assert BenefitRuleEngine().evaluate([], replace(context, enrolled=True)).is_entitled


@pytest.mark.parametrize(
    "category",
    [
        BenefitCategory.INSURANCE,
        BenefitCategory.PURCHASE_PROTECTION,
        BenefitCategory.EXTENDED_WARRANTY,
    ],
)
def test_coverage_is_not_cash(context, category):
    context.benefit.category = category
    assert BenefitRuleEngine().evaluate([], context).entitled_value == 0


def test_count_is_not_cash(context):
    context.benefit.value_type = BenefitValueType.COUNT
    context.benefit.max_value = Decimal("4")
    decision = BenefitRuleEngine().evaluate([], replace(context, usage_count=1))
    assert decision.entitled_value == 0
    assert decision.remaining_usage == 3


@pytest.mark.parametrize(
    "operator,actual,expected,upper,answer",
    [
        (RuleOperator.BETWEEN, "10.1", "10", "11", True),
        (RuleOperator.GTE, "9", "10", None, False),
        (RuleOperator.GT, "invalid", "10", None, False),
        (RuleOperator.GTE, "NaN", "0", None, False),
        (RuleOperator.IN, "visa", "amex,visa", None, True),
    ],
)
def test_operator_semantics(operator, actual, expected, upper, answer):
    assert BenefitRuleEngine._compare(actual, operator, expected, upper) is answer


def test_missing_transaction_context_fails_closed(context):
    r = rule(
        context, conditions=[RuleCondition(RuleConditionType.MERCHANT, RuleOperator.EQ, "Target")]
    )
    assert not BenefitRuleEngine().evaluate([r], context).is_entitled


@pytest.mark.parametrize(
    "frequency,start,end",
    [
        (BenefitFrequency.MONTHLY, (2024, 2, 1), (2024, 3, 1)),
        (BenefitFrequency.QUARTERLY, (2024, 1, 1), (2024, 4, 1)),
        (BenefitFrequency.SEMI_ANNUAL, (2024, 1, 1), (2024, 7, 1)),
        (BenefitFrequency.ANNUAL, (2024, 1, 1), (2025, 1, 1)),
    ],
)
def test_historical_periods_are_half_open(frequency, start, end):
    assert BenefitUtilizationService._get_frequency_period(frequency, NOW, NOW) == (
        datetime(*start, tzinfo=UTC),
        datetime(*end, tzinfo=UTC),
    )


def test_rule_effective_end_is_exclusive(context):
    assert not BenefitRuleEngine().evaluate([rule(context, effective_to=NOW)], context).is_entitled
