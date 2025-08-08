from __future__ import annotations

import os
import uuid
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette import status
from fastapi import HTTPException


LOGGER = logging.getLogger("app")
logging.basicConfig(level=logging.INFO)


def _parse_cors_origins() -> list[str]:
    value = os.getenv("CORS_ORIGINS", "")
    origins = [v.strip() for v in value.split(",") if v.strip()]
    # 開発デフォルトを常に許可
    if "http://localhost:3000" not in origins:
        origins.append("http://localhost:3000")
    return origins


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # クライアント提供を尊重、無ければ生成
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            # 例外は後段のハンドラで処理されるが、ここで再送出
            raise
        response.headers["X-Request-Id"] = request_id
        return response


app = FastAPI(
    title="Kyudai Campus SNS API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)

# X-Request-Id（最外層になるよう先に追加）
app.add_middleware(RequestIdMiddleware)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
)


def _error_body(code: str, message: str, request_id: str, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "requestId": request_id,
        }
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", uuid.uuid4().hex)
    body = _error_body("VALIDATION_ERROR", "Validation failed", req_id, [
        {"field": ".".join([str(x) for x in err.get("loc", [])]), "reason": err.get("msg", "")}
        for err in exc.errors()
    ])
    resp = JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body)
    resp.headers["X-Request-Id"] = req_id
    return resp


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", uuid.uuid4().hex)
    # 既に JSONResponse の場合はそのまま流すが、ヘッダだけは保証したい
    try:
        # fastapi の HTTPException は detail をそのまま返すことがある
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    except Exception:
        message = "HTTP error"
    body = _error_body(_map_status_to_code(exc.status_code), message, req_id)
    resp = JSONResponse(status_code=exc.status_code, content=body)
    resp.headers["X-Request-Id"] = req_id
    return resp


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", uuid.uuid4().hex)
    LOGGER.exception("Unhandled error: %s", exc)
    body = _error_body("INTERNAL", "Internal Server Error", req_id)
    resp = JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body)
    resp.headers["X-Request-Id"] = req_id
    return resp


def _map_status_to_code(status_code: int) -> str:
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


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    req_id = getattr(request.state, "request_id", "-")
    LOGGER.info("%s %s req_id=%s", request.method, request.url.path, req_id)
    response = await call_next(request)
    return response


@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}