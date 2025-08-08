import os
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時処理
    logger.info("Starting Kyudai Campus SNS API")
    yield
    # 終了時処理
    logger.info("Shutting down Kyudai Campus SNS API")

app = FastAPI(
    title="Kyudai Campus SNS API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# CORS設定（環境変数から読み込み）
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# X-Request-Id生成ミドルウェア
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    # リクエストに保存（他のミドルウェアや処理で使用可能）
    request.state.request_id = request_id
    
    # リクエストログ
    logger.info(f"Request: {request.method} {request.url.path} - X-Request-Id: {request_id}")
    
    try:
        response = await call_next(request)
        # レスポンスヘッダーに追加
        response.headers["X-Request-Id"] = request_id
        
        # レスポンスログ
        logger.info(f"Response: {response.status_code} - X-Request-Id: {request_id}")
        return response
    except Exception as e:
        # エラーハンドリング
        logger.error(f"Error processing request - X-Request-Id: {request_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "type": "INTERNAL_SERVER_ERROR",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred",
                "instance": request.url.path
            },
            headers={"X-Request-Id": request_id}
        )

# ヘルスチェックエンドポイント
@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

# OPTIONS メソッドのサポート（CORSプリフライト用）
@app.options("/api/v1/health")
async def health_options():
    return Response(status_code=200)

# 将来のルーター登録箇所
# TODO: 認証ルーター
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
# TODO: スレッドルーター
# app.include_router(threads_router, prefix="/api/v1/threads", tags=["threads"])
# TODO: コメントルーター
# app.include_router(comments_router, prefix="/api/v1/comments", tags=["comments"])
# TODO: リアクションルーター
# app.include_router(reactions_router, prefix="/api/v1/reactions", tags=["reactions"])
# TODO: プロフィールルーター
# app.include_router(profile_router, prefix="/api/v1/profile", tags=["profile"])
# TODO: アップロードルーター
# app.include_router(uploads_router, prefix="/api/v1/uploads", tags=["uploads"])
# TODO: 検索ルーター
# app.include_router(search_router, prefix="/api/v1/search", tags=["search"])