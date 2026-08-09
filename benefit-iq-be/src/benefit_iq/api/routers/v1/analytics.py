"""Benefit Utilization Analytics API Router.

Provides analytics endpoints for customer benefit utilization, KPI summaries,
trend calculations, and generic data querying.
"""
from typing import Any
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from benefit_iq.api.dependencies.auth import get_current_user
from benefit_iq.api.schemas.common import ApiResponse
from benefit_iq.api.schemas.query import QueryRequest, QueryResponse
from benefit_iq.domain.entities.user import User

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics & Utilization"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/kpi", response_model=ApiResponse[dict[str, Any]])
async def get_kpi_summary(
    current_user: User = Depends(get_current_user),
):
    """Retrieves top-level Benefit Utilization KPI metrics."""
    return ApiResponse(
        success=True,
        data={
            "total_claims_ytd": "$1,482,900",
            "claims_growth": "+12.4%",
            "approved_claims_pct": "94.8%",
            "total_savings": "$342,150",
            "active_members": 1420,
            "avg_processing_days": 1.8,
            "loss_ratio_pct": "68.2%",
        },
    )


@router.get("/utilization-trends", response_model=ApiResponse[list[dict[str, Any]]])
async def get_utilization_trends():
    """Retrieves monthly utilization trend timeline data."""
    trends = [
        {"month": "Jan", "medical": 125000, "dental": 42000, "vision": 18000, "rx": 54000},
        {"month": "Feb", "medical": 132000, "dental": 39000, "vision": 21000, "rx": 58000},
        {"month": "Mar", "medical": 148000, "dental": 45000, "vision": 24000, "rx": 62000},
        {"month": "Apr", "medical": 141000, "dental": 41000, "vision": 19000, "rx": 59000},
        {"month": "May", "medical": 156000, "dental": 48000, "vision": 26000, "rx": 67000},
        {"month": "Jun", "medical": 169000, "dental": 52000, "vision": 28000, "rx": 71000},
        {"month": "Jul", "medical": 162000, "dental": 49000, "vision": 25000, "rx": 68000},
    ]
    return ApiResponse(success=True, data=trends)


@router.get("/category-breakdown", response_model=ApiResponse[list[dict[str, Any]]])
async def get_category_breakdown():
    """Retrieves category breakdown percentages for claims."""
    breakdown = [
        {"category": "Inpatient Hospital", "percentage": 38.5, "amount": 570916},
        {"category": "Outpatient Care", "percentage": 24.2, "amount": 358861},
        {"category": "Prescription Drugs", "percentage": 18.6, "amount": 275819},
        {"category": "Dental Services", "percentage": 11.4, "amount": 169050},
        {"category": "Vision & Wellness", "percentage": 7.3, "amount": 108254},
    ]
    return ApiResponse(success=True, data=breakdown)


@router.post("/query", response_model=ApiResponse[QueryResponse])
async def query_analytics(request: QueryRequest):
    """Executes datatype-aware generic query over benefit utilization records."""
    mock_records = [
        {
            "id": f"CLM-2026-00{i}",
            "member_name": f"Member {i}",
            "benefit_type": ["Medical", "Dental", "Vision", "Prescription"][i % 4],
            "claim_amount": round(150.0 + (i * 37.5), 2),
            "approved_amount": round((150.0 + (i * 37.5)) * 0.9, 2),
            "status": ["APPROVED", "APPROVED", "PENDING", "REJECTED"][i % 4],
            "submitted_date": f"2026-08-0{min(i+1, 9)}",
        }
        for i in range(1, 21)
    ]
    total = len(mock_records)
    total_pages = (total + request.page_size - 1) // request.page_size
    return ApiResponse(
        success=True,
        data=QueryResponse(
            items=mock_records[: request.page_size],
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            aggregations={"total_claimed": 1482900, "total_approved": 1334610},
        ),
    )
