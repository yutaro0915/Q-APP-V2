"""
Kyudai Campus SNS API ルーターパッケージ

このパッケージは全てのAPIルーターモジュールを含みます。
各ルーターは特定のリソースやエンドポイントグループを管理します。

ルーター登録方法:
1. 新しいルーターモジュールを作成
2. このファイルの__all__リストに追加
3. main.pyでapp.include_router()を使用して登録

例:
    from app.routers import health_router
    app.include_router(health_router, prefix="/api/v1/health")
"""

# 将来のルーターをここにインポート
# from .health import router as health_router
# from .auth import router as auth_router
# from .threads import router as threads_router
# from .comments import router as comments_router
# from .reactions import router as reactions_router
# from .profile import router as profile_router
# from .uploads import router as uploads_router
# from .search import router as search_router

__all__ = [
    # 公開するルーターをここにリスト
    # "health_router",
    # "auth_router",
    # "threads_router",
    # "comments_router",
    # "reactions_router",
    # "profile_router",
    # "uploads_router",
    # "search_router",
]