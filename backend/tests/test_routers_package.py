"""
ルーターパッケージの初期化テスト
"""


def test_routers_package_import():
    """routersパッケージがインポート可能であることを確認"""
    try:
        import app.routers
        assert app.routers is not None
    except ImportError:
        assert False, "Failed to import app.routers package"


def test_routers_package_all_attribute():
    """__all__属性が定義されていることを確認"""
    import app.routers
    assert hasattr(app.routers, '__all__')
    assert isinstance(app.routers.__all__, list)


def test_routers_package_docstring():
    """パッケージdocstringが存在することを確認"""
    import app.routers
    assert app.routers.__doc__ is not None
    assert len(app.routers.__doc__) > 0
    assert "ルーター" in app.routers.__doc__