"""Authenticated benefit workflow. Customer identity always comes from the session."""

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import AwareDatetime, BaseModel, Field

from benefit_iq.api.dependencies.auth import get_current_admin_user, get_current_user
from benefit_iq.api.schemas.common import ApiResponse
from benefit_iq.domain.entities.benefit_usage import BenefitUsage
from benefit_iq.domain.entities.transaction import Transaction
from benefit_iq.domain.entities.user import User
from benefit_iq.domain.enums.benefit_enums import TransactionChannel, TransactionStatus

router = APIRouter(
    prefix="/analytics", tags=["Benefit analytics"], dependencies=[Depends(get_current_user)]
)
Currency = Annotated[str, Query(pattern="^[A-Z]{3}$")]


class AddCardRequest(BaseModel):
    product_id: UUID
    last_four: str = Field(pattern=r"^\d{4}$")
    alias: str = Field(default="My card", max_length=80)


class TransactionRequest(BaseModel):
    external_id: str = Field(min_length=1, max_length=120)
    card_id: UUID
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=4, allow_inf_nan=False)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    merchant_name: str = Field(min_length=1, max_length=200)
    merchant_category_code: str = Field(pattern=r"^\d{4}$")
    transaction_date: AwareDatetime


class UsageRequest(BaseModel):
    external_id: str = Field(min_length=1, max_length=120)
    card_id: UUID
    benefit_id: UUID
    value: Decimal = Field(ge=0, max_digits=18, decimal_places=4, allow_inf_nan=False)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")


async def customer_scope(customer_id: UUID, user: User = Depends(get_current_user)):
    if customer_id != user.id:
        raise HTTPException(403, "This customer is outside your account")
    return user


@router.get("/cards")
@inject
async def catalog(repo=Depends(Provide["card_product_repository"])):
    return ApiResponse(success=True, data=[asdict(p) for p in await repo.list_all(0, 100)])


@router.get("/benefits")
@inject
async def benefits(repo=Depends(Provide["benefit_repository"])):
    return ApiResponse(success=True, data=[asdict(p) for p in await repo.list_all(0, 100)])


@router.get("/me/cards")
@inject
async def my_cards(
    user: User = Depends(get_current_user), repo=Depends(Provide["card_repository"])
):
    return ApiResponse(success=True, data=[asdict(c) for c in await repo.get_by_customer(user.id)])


@router.post("/me/cards", status_code=201)
@inject
async def add_card(
    request: AddCardRequest,
    user: User = Depends(get_current_user),
    service=Depends(Provide["workflow_service"]),
):
    return ApiResponse(
        success=True,
        data=asdict(
            await service.add_card(user.id, request.product_id, request.last_four, request.alias)
        ),
    )


@router.get("/me/utilization")
@inject
async def my_utilization(
    currency: Currency = "USD",
    as_of: AwareDatetime | None = None,
    user: User = Depends(get_current_user),
    service=Depends(Provide["utilization_service"]),
):
    return ApiResponse(
        success=True,
        data=asdict(
            await service.calculate_customer_utilization(
                user.id, period_end=as_of, currency=currency
            )
        ),
    )


@router.get("/customers/{customer_id}/utilization", dependencies=[Depends(customer_scope)])
@inject
async def customer_utilization(
    customer_id: UUID, currency: Currency = "USD", service=Depends(Provide["utilization_service"])
):
    return ApiResponse(
        success=True,
        data=asdict(await service.calculate_customer_utilization(customer_id, currency=currency)),
    )


@router.get("/me/recommendations")
@inject
async def recommendations(
    currency: Currency = "USD",
    user: User = Depends(get_current_user),
    service=Depends(Provide["utilization_service"]),
    scorer=Depends(Provide["ml_prediction_service"]),
):
    summary = await service.calculate_customer_utilization(user.id, currency=currency)
    return ApiResponse(
        success=True,
        data=[
            asdict(p) for p in await scorer.predict_recommendations(user.id, summary.utilizations)
        ],
    )


@router.get("/me/transactions")
@inject
async def transactions(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    repo=Depends(Provide["transaction_repository"]),
):
    return ApiResponse(
        success=True,
        data=[asdict(t) for t in await repo.get_by_customer(user.id, offset=offset, limit=limit)],
    )


@router.post("/me/transactions", status_code=201)
@inject
async def ingest(
    request: TransactionRequest,
    user: User = Depends(get_current_user),
    service=Depends(Provide["workflow_service"]),
):
    now = datetime.now(UTC)
    when = request.transaction_date.astimezone(UTC).replace(microsecond=0)
    if when > now:
        raise HTTPException(422, "Future transactions are not accepted")
    tx = Transaction(
        id=uuid4(),
        external_transaction_id=request.external_id,
        customer_id=user.id,
        card_id=request.card_id,
        merchant_id=None,
        merchant_name=request.merchant_name,
        merchant_category_code=request.merchant_category_code,
        amount=request.amount,
        currency=request.currency,
        transaction_date=when,
        posted_date=when,
        status=TransactionStatus.POSTED,
        channel=TransactionChannel.ONLINE,
        description=None,
        country=None,
        city=None,
        is_recurring=False,
        source_system="user_import",
        idempotency_key="",
        created_at=now,
        updated_at=now,
    )
    return ApiResponse(success=True, data=asdict(await service.ingest(tx)))


@router.post("/me/transactions/{transaction_id}/reverse")
@inject
async def reverse(
    transaction_id: UUID,
    user: User = Depends(get_current_user),
    service=Depends(Provide["workflow_service"]),
):
    return ApiResponse(success=True, data=asdict(await service.reverse(user.id, transaction_id)))


@router.post("/me/usage", status_code=201)
@inject
async def redeem(
    request: UsageRequest,
    user: User = Depends(get_current_user),
    service=Depends(Provide["workflow_service"]),
):
    now = datetime.now(UTC)
    usage = BenefitUsage(
        id=uuid4(),
        customer_id=user.id,
        card_id=request.card_id,
        benefit_id=request.benefit_id,
        transaction_id=None,
        usage_date=now,
        value_used=request.value,
        currency=request.currency,
        description="Self-reported benefit use",
        source_system="self_reported",
        created_at=now,
    )
    return ApiResponse(success=True, data=asdict(await service.redeem(usage, request.external_id)))


@router.get("/kpi", dependencies=[Depends(get_current_admin_user)])
@inject
async def kpi(currency: Currency = "USD", service=Depends(Provide["portfolio_analytics_service"])):
    return ApiResponse(success=True, data=await service.get_kpi_summary(currency))


@router.get("/me/nudges")
@inject
async def get_nudges(
    user: User = Depends(get_current_user), service=Depends(Provide["nudge_service"])
):
    return ApiResponse(
        success=True, data=[asdict(n) for n in await service.get_customer_nudges(user.id)]
    )


@router.post("/me/nudges")
@inject
async def generate_nudges(
    currency: Currency = "USD",
    user: User = Depends(get_current_user),
    utilization=Depends(Provide["utilization_service"]),
    service=Depends(Provide["nudge_service"]),
    locks=Depends(Provide["redis"]),
):
    async with locks.lock(f"nudges:{user.id}"):
        summary = await utilization.calculate_customer_utilization(user.id, currency=currency)
        nudges = await service.generate_nudges_for_customer(user.id, summary.utilizations)
        return ApiResponse(success=True, data=[asdict(n) for n in nudges])


class NudgeAcknowledgement(BaseModel):
    status: Literal["opened", "dismissed"]


@router.post("/me/nudges/{nudge_id}/status")
@inject
async def acknowledge(
    nudge_id: UUID,
    request: NudgeAcknowledgement,
    user: User = Depends(get_current_user),
    service=Depends(Provide["nudge_service"]),
):
    from benefit_iq.domain.enums.benefit_enums import NudgeStatus

    return ApiResponse(
        success=True,
        data=asdict(await service.acknowledge(user.id, nudge_id, NudgeStatus(request.status))),
    )


class EnrollmentRequest(BaseModel):
    card_id: UUID
    benefit_id: UUID


@router.post("/me/enrollments")
@inject
async def enroll(
    request: EnrollmentRequest,
    user: User = Depends(get_current_user),
    workflow=Depends(Provide["workflow_service"]),
    benefits=Depends(Provide["benefit_repository"]),
    enrollments=Depends(Provide["enrollment_repository"]),
    locks=Depends(Provide["redis"]),
):
    card = await workflow.owned_card(user.id, request.card_id)
    linked = await benefits.get_by_card_product(card.card_product_id)
    if not any(b.id == request.benefit_id for b in linked):
        raise HTTPException(404, "Benefit not found on this card")
    now = datetime.now(UTC)
    async with locks.lock(f"enrollment:{user.id}:{card.id}:{request.benefit_id}"):
        if not await enrollments.is_enrolled(user.id, card.id, request.benefit_id, now):
            await enrollments.enroll(user.id, card.id, request.benefit_id, now)
    return ApiResponse(
        success=True,
        data={
            "source": "self_reported",
            "message": "Enrollment recorded. Confirm enrollment with your issuer.",
        },
    )


@router.get("/me/redemption-predictions")
@inject
async def redemption_predictions(
    currency: Currency = "USD",
    user: User = Depends(get_current_user),
    utilization=Depends(Provide["utilization_service"]),
    model=Depends(Provide["ml_prediction_service"]),
):
    summary = await utilization.calculate_customer_utilization(user.id, currency=currency)
    return ApiResponse(
        success=True, data=await model.predict_redemption(user.id, summary.utilizations)
    )
