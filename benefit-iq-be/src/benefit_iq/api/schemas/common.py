"""Common API schema definitions."""
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Class missing docstring."""
    code: str
    message: str
    details: dict | None = None
    correlation_id: str | None = None


class ResponseMeta(BaseModel):
    """Class missing docstring."""
    request_id: str
    timestamp: datetime


class ApiResponse(BaseModel, Generic[T]):
    """Class missing docstring."""
    success: bool
    data: T | None = None
    error: ErrorDetail | str | None = None
    meta: ResponseMeta | None = None
