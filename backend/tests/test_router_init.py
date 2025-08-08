"""Test for routers package initialization."""

import importlib
import sys


def test_routers_package_import():
    """Test that routers package can be imported."""
    import app.routers
    assert app.routers is not None


def test_routers_package_has_all():
    """Test that routers package defines __all__."""
    import app.routers
    assert hasattr(app.routers, '__all__')
    assert isinstance(app.routers.__all__, list)


def test_routers_health_import():
    """Test that health router can be imported from routers."""
    from app.routers import health
    assert health is not None
    assert hasattr(health, 'router')