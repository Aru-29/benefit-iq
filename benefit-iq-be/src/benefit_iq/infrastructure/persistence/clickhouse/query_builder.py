"""ClickHouse Generic Query Builder.

Generates safe, parameterized ClickHouse SQL queries with schema validation
from QueryRequest definitions to prevent SQL injection and enforce strong typing.
"""
from typing import Any
import re
import structlog
from benefit_iq.api.schemas.query import (
    FilterCondition,
    FilterGroup,
    FilterOperator,
    QueryRequest,
    SortCondition,
    SortDirection,
)

logger = structlog.get_logger(__name__)


class ClickHouseQueryBuilder:
    """Datatype-aware parameterized SQL builder for ClickHouse queries."""

    def __init__(self, table_name: str, allowed_fields: dict[str, str], searchable_fields: list[str] | None = None) -> None:
        """
        :param table_name: Name of ClickHouse table.
        :param allowed_fields: Map of API field names to ClickHouse column name / data type.
                               e.g. {"id": "id", "email": "email", "is_active": "is_active"}
        :param searchable_fields: List of fields checked when request.search is provided.
        """
        self.table_name = table_name
        self.allowed_fields = allowed_fields
        self.searchable_fields = searchable_fields or [
            f for f in allowed_fields.keys() if f.endswith(("name", "email", "title", "key", "description", "username"))
        ]

    def build_query(self, request: QueryRequest) -> tuple[str, str, dict[str, Any], int, int]:
        """
        Builds (data_sql, count_sql, params, limit, offset).
        """
        params: dict[str, Any] = {}
        param_counter = [0]

        def get_param_name() -> str:
            param_counter[0] += 1
            return f"p_{param_counter[0]}"

        where_clauses: list[str] = []

        # 1. Handle Global Search
        if request.search and request.search.strip() and self.searchable_fields:
            search_param = get_param_name()
            params[search_param] = f"%{request.search.strip()}%"
            search_conditions = []
            for field in self.searchable_fields:
                if field in self.allowed_fields:
                    col = self.allowed_fields[field]
                    search_conditions.append(f"lower({col}) LIKE lower(%({search_param})s)")
            if search_conditions:
                where_clauses.append(f"({' OR '.join(search_conditions)})")

        # 2. Handle Filter Group
        if request.filter_group:
            fg_clause = self._build_filter_group(request.filter_group, params, get_param_name)
            if fg_clause:
                where_clauses.append(fg_clause)

        where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # 3. Handle Group By & Aggregations
        group_cols = [self.allowed_fields[f] for f in request.group_by if f in self.allowed_fields]
        group_by_str = f" GROUP BY {', '.join(group_cols)}" if group_cols else ""

        # 4. Handle Sorting
        sort_clauses: list[str] = []
        for sort in request.sorts:
            if sort.field in self.allowed_fields:
                col = self.allowed_fields[sort.field]
                direction = "DESC" if sort.direction == SortDirection.DESC else "ASC"
                sort_clauses.append(f"{col} {direction}")
        sort_str = f" ORDER BY {', '.join(sort_clauses)}" if sort_clauses else ""

        # 5. Handle Pagination
        limit = request.page_size
        offset = (request.page - 1) * request.page_size

        data_sql = f"SELECT * FROM {self.table_name}{where_str}{group_by_str}{sort_str} LIMIT {limit} OFFSET {offset}"
        count_sql = f"SELECT count(*) FROM {self.table_name}{where_str}"

        return data_sql, count_sql, params, limit, offset

    def _build_filter_group(self, group: FilterGroup, params: dict[str, Any], get_param_name) -> str:
        clauses: list[str] = []
        logic = " OR " if group.logic.upper() == "OR" else " AND "

        for filter_cond in group.filters:
            clause = self._build_condition(filter_cond, params, get_param_name)
            if clause:
                clauses.append(clause)

        for sub_group in group.groups:
            sub_clause = self._build_filter_group(sub_group, params, get_param_name)
            if sub_clause:
                clauses.append(sub_clause)

        if not clauses:
            return ""
        return f"({logic.join(clauses)})"

    def _build_condition(self, cond: FilterCondition, params: dict[str, Any], get_param_name) -> str:
        if cond.field not in self.allowed_fields:
            return ""

        col = self.allowed_fields[cond.field]
        op = cond.operator

        if op == FilterOperator.IS_NULL:
            return f"{col} IS NULL OR {col} = ''"
        if op == FilterOperator.IS_NOT_NULL:
            return f"{col} IS NOT NULL AND {col} != ''"

        p1 = get_param_name()

        if op == FilterOperator.EQ:
            params[p1] = cond.value
            return f"{col} = %({p1})s"
        if op == FilterOperator.NEQ:
            params[p1] = cond.value
            return f"{col} != %({p1})s"
        if op == FilterOperator.GT:
            params[p1] = cond.value
            return f"{col} > %({p1})s"
        if op == FilterOperator.GTE:
            params[p1] = cond.value
            return f"{col} >= %({p1})s"
        if op == FilterOperator.LT:
            params[p1] = cond.value
            return f"{col} < %({p1})s"
        if op == FilterOperator.LTE:
            params[p1] = cond.value
            return f"{col} <= %({p1})s"
        if op in (FilterOperator.CONTAINS, FilterOperator.ICONTAINS):
            params[p1] = f"%{cond.value}%"
            return f"lower({col}) LIKE lower(%({p1})s)"
        if op == FilterOperator.STARTS_WITH:
            params[p1] = f"{cond.value}%"
            return f"lower({col}) LIKE lower(%({p1})s)"
        if op == FilterOperator.ENDS_WITH:
            params[p1] = f"%{cond.value}"
            return f"lower({col}) LIKE lower(%({p1})s)"
        if op == FilterOperator.IN:
            vals = list(cond.value) if isinstance(cond.value, (list, tuple, set)) else [cond.value]
            params[p1] = tuple(vals)
            return f"{col} IN %({p1})s"
        if op == FilterOperator.NOT_IN:
            vals = list(cond.value) if isinstance(cond.value, (list, tuple, set)) else [cond.value]
            params[p1] = tuple(vals)
            return f"{col} NOT IN %({p1})s"
        if op == FilterOperator.BETWEEN:
            p2 = get_param_name()
            params[p1] = cond.value
            params[p2] = cond.value_to
            return f"{col} BETWEEN %({p1})s AND %({p2})s"

        return ""
