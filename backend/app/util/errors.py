from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel


ErrorCode = Literal[
    "VALIDATION_ERROR",
    "UNAUTHORIZED",
    "FORBIDDEN",
    "NOT_FOUND",
    "CONFLICT",
    "RATE_LIMITED",
    "INTERNAL",
]


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str
    details: list[dict[str, Any]] = []
    requestId: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


@dataclass
class BaseAPIException(Exception):
    code: ErrorCode
    http_status: int
    message: str
    details: list[dict[str, Any]] | None = None


class BadRequestException(BaseAPIException):
    def __init__(self, message: str = "Bad Request", details: list[dict[str, Any]] | None = None):
        super().__init__("VALIDATION_ERROR", 400, message, details)


class UnauthorizedException(BaseAPIException):
    def __init__(self, message: str = "Unauthorized", details: list[dict[str, Any]] | None = None):
        super().__init__("UNAUTHORIZED", 401, message, details)


class ForbiddenException(BaseAPIException):
    def __init__(self, message: str = "Forbidden", details: list[dict[str, Any]] | None = None):
        super().__init__("FORBIDDEN", 403, message, details)


class NotFoundException(BaseAPIException):
    def __init__(self, message: str = "Not Found", details: list[dict[str, Any]] | None = None):
        super().__init__("NOT_FOUND", 404, message, details)


class ConflictException(BaseAPIException):
    def __init__(self, message: str = "Conflict", details: list[dict[str, Any]] | None = None):
        super().__init__("CONFLICT", 409, message, details)


class ValidationException(BaseAPIException):
    def __init__(self, message: str = "Validation Error", details: list[dict[str, Any]] | None = None):
        super().__init__("VALIDATION_ERROR", 422, message, details)


def to_error_response(code: ErrorCode, message: str, request_id: str | None, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details or [], requestId=request_id))
    return body.model_dump()