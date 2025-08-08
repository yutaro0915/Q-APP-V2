"""FastAPI Routers package.

本パッケージは API の各機能ルーター（auth/threads/comments/...）を提供します。

登録例：
    from fastapi import APIRouter
    router = APIRouter(prefix="/api/v1")
    # from .health import router as health_router
    # router.include_router(health_router)

公開ルーターは `__all__` に追加してください。
"""

# ここでは公開名の型を明示するのみ。実体は各モジュール側で定義。
__all__: list[str] = [
    # "health",
    # "auth",
    # "threads",
    # "comments",
    # "reactions",
    # "uploads",
    # "search",
    # "profile",
]