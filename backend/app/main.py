import os
import uuid
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Kyudai Campus SNS API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json"
)

def _get_cors_origins() -> list[str]:
    origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in origins_env.split(",") if o.strip()]

# CORS 設定（本番は .env のみ許可、開発はlocalhost）
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
)


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    # 構造化ログは簡略化（将来loggerへ）
    response: Response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}