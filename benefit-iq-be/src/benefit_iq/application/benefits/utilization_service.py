"""Benefit Utilization Calculation Service.

Implements the core business logic for benefit under-utilization analytics.
Calculates entitlements, usage, remaining value, and generates utilization summaries.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import structlog

from benefit_iq.application.benefits.rule_engine import (
    BenefitRuleEngine,
    RuleEvaluationContext,
)
from benefit_iq.application.contracts.repositories.benefit_repositories import (
    BenefitRepository,
    BenefitRuleRepository,
    BenefitUsageRepository,
    CardProductBenefitRepository,
    CardProductRepository,
    CardRepository,
    TransactionRepository,
)
from benefit_iq.domain.enums.benefit_enums import (
    BenefitFrequency,
    UtilizationStatus,
)
from benefit_iq.domain.valueobjects.benefit_utilization import (
    BenefitUtilization,
    CustomerBenefitSummary,
)

logger = structlog.get_logger(__name__)

# Expiry warning threshold in days
EXPIRY_WARNING_DAYS = 30


class BenefitUtilizationService:
    """Service for calculating benefit utilization analytics.

    This is the core business calculation engine that determines:
    - What benefits a customer is entitled to
    - How much they have used
    - What remains unused (the underutilization gap)
    - Whether benefits are at risk of expiry
    """

    def __init__(
        self,
        card_repository: CardRepository,
        card_product_repository: CardProductRepository,
        card_product_benefit_repository: CardProductBenefitRepository,
        benefit_repository: BenefitRepository,
        benefit_rule_repository: BenefitRuleRepository,
        benefit_usage_repository: BenefitUsageRepository,
        transaction_repository: TransactionRepository,
        enrollment_repository=None,
    ) -> None:
        """Initialize with all required repository dependencies."""
        self._enrollments = enrollment_repository
        self._cards = card_repository
        self._card_products = card_product_repository
        self._card_product_benefits = card_product_benefit_repository
        self._benefits = benefit_repository
        self._rules = benefit_rule_repository
        self._usage = benefit_usage_repository
        self._transactions = transaction_repository
        self._rule_engine = BenefitRuleEngine()

    async def calculate_customer_utilization(
        self,
        customer_id: UUID,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        currency: str = "USD",
    ) -> CustomerBenefitSummary:
        """Snapshot of the cycle containing as-of time, in one currency only."""
        now = period_end or datetime.now(UTC)
        if now.tzinfo is None or (period_start and period_start.tzinfo is None):
            raise ValueError("Calculation timestamps must include a timezone")
        now = now.astimezone(UTC)
        if period_start and period_start > now:
            raise ValueError("Start must not follow end")
        cards = await self._cards.get_by_customer(customer_id)
        utilizations = []
        products, benefits, rule_sets, spend_cache = {}, {}, {}, {}
        for card in cards:
            if card.status.value != "active" or not card.issued_at <= now < card.expiry_date:
                continue
            if card.card_product_id not in products:
                products[card.card_product_id] = await self._card_products.get_by_id(
                    card.card_product_id
                )
            product = products[card.card_product_id]
            if not product or not product.is_active:
                continue
            mappings = await self._card_product_benefits.get_benefits_for_product(
                card.card_product_id
            )
            for mapping in mappings:
                if not mapping.is_active:
                    continue
                if mapping.benefit_id not in benefits:
                    benefits[mapping.benefit_id] = await self._benefits.get_by_id(
                        mapping.benefit_id
                    )
                benefit = benefits[mapping.benefit_id]
                if not benefit or benefit.currency != currency:
                    continue
                start, end = self._get_frequency_period(benefit.frequency, card.issued_at, now)
                start = max(start, card.issued_at, benefit.effective_from)
                if benefit.effective_to:
                    end = min(end, benefit.effective_to)
                end = min(end, card.expiry_date)
                cutoff = min(now + timedelta(microseconds=1), end)
                usages = await self._usage.get_usage_for_customer_benefit(
                    customer_id, benefit.id, start, cutoff
                )
                usages = {
                    u.id: u for u in usages if u.card_id == card.id and u.currency == currency
                }
                used = sum((u.value_used for u in usages.values()), Decimal("0"))
                key = (benefit.id, product.id)
                if key not in rule_sets:
                    rule_sets[key] = await self._rules.get_active_rules(benefit.id, product.id)
                rules = rule_sets[key]
                spend_start = start
                # Each rule may specify its own rolling spend qualification window.
                evaluations = []
                for rule in rules or [None]:
                    if rule and rule.spend_period_days:
                        spend_start = max(
                            card.issued_at, now - timedelta(days=rule.spend_period_days)
                        )
                    else:
                        spend_start = start
                    spend_key = (card.id, spend_start, cutoff, currency)
                    if spend_key not in spend_cache:
                        spend_cache[spend_key] = await self._transactions.get_customer_spend(
                            customer_id, card.id, spend_start, cutoff, currency=currency
                        )
                    spend = spend_cache[spend_key]
                    context = RuleEvaluationContext(
                        customer_id=customer_id,
                        card=card,
                        card_product=product,
                        benefit=benefit,
                        current_date=now,
                        accumulated_spend=spend,
                        usage_count=len(usages),
                        usage_value=used,
                        currency=currency,
                        customer_tenure_days=(now - card.issued_at).days,
                        enrolled=await self._enrollments.is_enrolled(
                            customer_id, card.id, benefit.id, now
                        )
                        if self._enrollments and benefit.requires_activation
                        else False,
                    )
                    evaluations.append((rule, context))
                # Preserve version selection inside the engine; use per-rule spend in future
                # only when windows differ. Reject ambiguous configurations instead of guessing.
                windows = {r.spend_period_days for r in rules}
                if len(windows) > 1:
                    raise ValueError("Rules for a benefit must share a spend qualification window")
                decision = self._rule_engine.evaluate(rules, evaluations[0][1])
                selected = next((r for r in rules if r.id == decision.rule_id), None)
                limit = None
                if decision.remaining_usage is not None:
                    limits = [
                        v
                        for v in (
                            selected.usage_limit if selected else None,
                            self._rule_engine._get_period_limit(selected, benefit.frequency)
                            if selected
                            else None,
                        )
                        if v is not None
                    ]
                    limit = min(limits) if limits else int(benefit.max_value)
                entitled = decision.entitled_value
                # Only cash-equivalent benefits contribute to monetary totals.
                used_cash = min(max(used, Decimal("0")), entitled)
                remaining = max(Decimal("0"), entitled - used_cash)
                pct = used_cash / entitled * 100 if entitled else Decimal("0")
                if not decision.is_entitled:
                    status = UtilizationStatus.NOT_ELIGIBLE
                elif (limit is not None and len(usages) >= limit) or (
                    entitled > 0 and used_cash >= entitled
                ):
                    status = UtilizationStatus.FULLY_USED
                elif usages:
                    status = UtilizationStatus.PARTIALLY_USED
                else:
                    status = UtilizationStatus.UNUSED
                days = max(0, (end - now).days)
                at_risk = (
                    decision.is_entitled
                    and status != UtilizationStatus.FULLY_USED
                    and days <= EXPIRY_WARNING_DAYS
                )
                utilizations.append(
                    BenefitUtilization(
                        customer_id=customer_id,
                        card_id=card.id,
                        benefit_id=benefit.id,
                        benefit_name=benefit.name,
                        benefit_category=benefit.category.value,
                        period_start=start,
                        period_end=end,
                        entitled_value=entitled,
                        used_value=used_cash,
                        remaining_value=remaining,
                        utilization_percentage=pct.quantize(Decimal("0.01")),
                        currency=currency,
                        status=status,
                        usage_count=len(usages),
                        usage_limit=limit,
                        eligibility_reason=decision.explanation,
                        expiry_date=end,
                        days_until_expiry=days,
                        at_risk_of_expiry=at_risk,
                        rule_id=decision.rule_id,
                        rule_version=decision.rule_version,
                        calculated_at=now,
                        value_type=benefit.value_type.value,
                    )
                )
        return self._build_summary(
            customer_id,
            period_start or datetime(now.year, 1, 1, tzinfo=UTC),
            now,
            utilizations,
            currency,
        )

    @staticmethod
    def _get_frequency_period(frequency, period_start, period_end):
        now = period_end.astimezone(UTC)
        months = {
            BenefitFrequency.MONTHLY: 1,
            BenefitFrequency.QUARTERLY: 3,
            BenefitFrequency.SEMI_ANNUAL: 6,
            BenefitFrequency.ANNUAL: 12,
        }
        if frequency in months:
            size = months[frequency]
            month = ((now.month - 1) // size) * size + 1
            start = datetime(now.year, month, 1, tzinfo=UTC)
            next_month = month + size
            end = datetime(
                now.year + (next_month - 1) // 12, (next_month - 1) % 12 + 1, 1, tzinfo=UTC
            )
            return start, end
        # Lifetime benefits end with the card; callers cap further at effective_to.
        return period_start, datetime(2100, 1, 1, tzinfo=UTC)

    @staticmethod
    def _build_summary(customer_id, period_start, period_end, utilizations, currency="USD"):
        entitled = sum((u.entitled_value for u in utilizations), Decimal("0"))
        used = sum((u.used_value for u in utilizations), Decimal("0"))
        return CustomerBenefitSummary(
            customer_id=customer_id,
            period_start=period_start,
            period_end=period_end,
            total_entitled_value=entitled,
            total_used_value=used,
            total_unused_value=sum((u.remaining_value for u in utilizations), Decimal("0")),
            overall_utilization_percentage=(used / entitled * 100).quantize(Decimal("0.01"))
            if entitled
            else Decimal("0"),
            currency=currency,
            total_benefits=len(utilizations),
            utilized_benefits=sum(u.status == UtilizationStatus.FULLY_USED for u in utilizations),
            partially_utilized_benefits=sum(
                u.status == UtilizationStatus.PARTIALLY_USED for u in utilizations
            ),
            unused_benefits=sum(u.status == UtilizationStatus.UNUSED for u in utilizations),
            expired_benefits=sum(u.status == UtilizationStatus.EXPIRED for u in utilizations),
            at_risk_benefits=sum(u.at_risk_of_expiry for u in utilizations),
            utilizations=utilizations,
        )
