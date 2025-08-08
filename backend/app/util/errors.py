from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from fastapi import HTTPException
import uuid


ErrorCode = Literal[
    "VALIDATION_ERROR",
    "UNAUTHORIZED",
    "FORBIDDEN",
    "NOT_FOUND",
    "CONFLICT",
    "RATE_LIMITED",
    "INTERNAL",
]


def error_body(code: ErrorCode, message: str, request_id: str, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "requestId": request_id,
        }
    }


@dataclass
class BaseAPIException(Exception):
    message: str
    code: ErrorCode
    http_status: int
    details: list[dict[str, Any]] | None = None


class BadRequestException(BaseAPIException):
    def __init__(self, message: str = "Bad Request", details: list[dict[str, Any]] | None = None):
        super().__init__(message, "VALIDATION_ERROR", status.HTTP_400_BAD_REQUEST, details)


class UnauthorizedException(BaseAPIException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED", status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(BaseAPIException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN", status.HTTP_403_FORBIDDEN)


class NotFoundException(BaseAPIException):
    def __init__(self, message: str = "Not Found"):
        super().__init__(message, "NOT_FOUND", status.HTTP_404_NOT_FOUND)


class ConflictException(BaseAPIException):
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, "CONFLICT", status.HTTP_409_CONFLICT)


class RateLimitedException(BaseAPIException):
    def __init__(self, message: str = "Rate Limited"):
        super().__init__(message, "RATE_LIMITED", status.HTTP_429_TOO_MANY_REQUESTS)


def map_status_to_code(status_code: int) -> ErrorCode:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "UNAUTHORIZED"
    if status_code == status.HTTP_403_FORBIDDEN:
        return "FORBIDDEN"
    if status_code == status.HTTP_404_NOT_FOUND:
        return "NOT_FOUND"
    if status_code == status.HTTP_409_CONFLICT:
        return "CONFLICT"
    if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return "RATE_LIMITED"
    return "INTERNAL"


async def handle_base_api_exception(request: Request, exc: BaseAPIException):
    req_id = getattr(request.state, "request_id", uuid.uuid4().hex)
    body = error_body(exc.code, exc.message, req_id, exc.details)
    resp = JSONResponse(status_code=exc.http_status, content=body)
    resp.headers["X-Request-Id"] = req_id
    return resp


async def handle_http_exception(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", uuid.uuid4().hex)
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    code = map_status_to_code(exc.status_code)
    body = error_body(code, message, req_id)
    resp = JSONResponse(status_code=exc.status_code, content=body)
    resp.headers["X-Request-Id"] = req_id
    return resp


async def handle_validation_exception(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", uuid.uuid4().hex)
    details = [
        {"field": ".".join([str(x) for x in err.get("loc", [])]), "reason": err.get("msg", "")}
        for err in exc.errors()
    ]
    body = error_body("VALIDATION_ERROR", "Validation failed", req_id, details)
    resp = JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body)
    resp.headers["X-Request-Id"] = req_id
    return resp

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