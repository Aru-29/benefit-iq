"""Append-only self-reported enrollment events."""

from benefit_iq.application.contracts.repositories.benefit_repositories import EnrollmentRepository


class ClickHouseEnrollmentRepository(EnrollmentRepository):
    def __init__(self, database):
        self.db = database

    async def is_enrolled(self, customer_id, card_id, benefit_id, as_of):
        result = await self.db.query_async(
            "SELECT count() FROM benefitiq.benefit_enrollments WHERE customer_id=%(customer)s "
            "AND card_id=%(card)s AND benefit_id=%(benefit)s AND enrolled_at <= %(at)s",
            {
                "customer": str(customer_id),
                "card": str(card_id),
                "benefit": str(benefit_id),
                "at": as_of,
            },
        )
        return bool(result.result_rows[0][0])

    async def enroll(self, customer_id, card_id, benefit_id, at):
        await self.db.execute_async(
            "INSERT INTO benefitiq.benefit_enrollments (customer_id,card_id,benefit_id,enrolled_at) VALUES (%s,%s,%s,%s)",
            [str(customer_id), str(card_id), str(benefit_id), at],
        )
