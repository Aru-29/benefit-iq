"""Portfolio metrics computed from the same entitlement engine as customer views."""

from decimal import Decimal


class PortfolioAnalyticsService:
    def __init__(self, card_repository, utilization_service):
        self.cards = card_repository
        self.utilization = utilization_service

    async def get_kpi_summary(self, currency="USD"):
        customers, count, offset = set(), 0, 0
        while True:
            cards = await self.cards.list_all(offset, 500)
            count += sum(c.status.value == "active" for c in cards)
            customers.update(c.customer_id for c in cards if c.status.value == "active")
            if len(cards) < 500:
                break
            offset += 500
        summaries = [
            await self.utilization.calculate_customer_utilization(c, currency=currency)
            for c in sorted(customers, key=str)
        ]
        entitled = sum((s.total_entitled_value for s in summaries), Decimal("0"))
        used = sum((s.total_used_value for s in summaries), Decimal("0"))
        return {
            "currency": currency,
            "active_cards": count,
            "active_customers": len(customers),
            "entitled_value": entitled,
            "used_value": used,
            "remaining_value": entitled - used,
            "utilization_pct": used / entitled * 100 if entitled else Decimal("0"),
            "calculation": "current benefit cycles; cash equivalents only",
        }
