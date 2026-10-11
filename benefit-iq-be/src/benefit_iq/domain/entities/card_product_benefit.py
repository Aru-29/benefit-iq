"""Card Product Benefit mapping entity.

Links benefits to card products, establishing which benefits are available on which cards.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class CardProductBenefit:
    """Association between a card product and a benefit."""

    id: UUID
    card_product_id: UUID
    benefit_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
