"""Generic Data Query Schemas.

Defines schemas for datatype-aware filtering, pagination, sorting, grouping,
and aggregation across backend query repositories.
"""
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class FilterOperator(str, Enum):
    """Supported filter operators."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"


class FilterCondition(BaseModel):
    """Single field filter condition."""

    field: str
    operator: FilterOperator = FilterOperator.EQ
    value: Any = None
    value_to: Any = None


class FilterGroup(BaseModel):
    """Nested filter group supporting AND/OR logical combinations."""

    logic: str = "AND"  # "AND" or "OR"
    filters: list[FilterCondition] = Field(default_factory=list)
    groups: list["FilterGroup"] = Field(default_factory=list)


FilterGroup.model_rebuild()


class SortDirection(str, Enum):
    """Sort direction."""

    ASC = "ASC"
    DESC = "DESC"


class SortCondition(BaseModel):
    """Field sorting condition."""

    field: str
    direction: SortDirection = SortDirection.ASC


class AggregateFunction(str, Enum):
    """Aggregation functions."""

    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"


class AggregationQuery(BaseModel):
    """Aggregation query item."""

    field: str
    function: AggregateFunction = AggregateFunction.COUNT
    alias: str | None = None


class QueryRequest(BaseModel):
    """Unified generic query request."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=500)
    search: str | None = None
    filter_group: FilterGroup | None = None
    sorts: list[SortCondition] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    aggregations: list[AggregationQuery] = Field(default_factory=list)


class QueryResponse(BaseModel):
    """Unified generic query response."""

    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    aggregations: dict[str, Any] | None = None
