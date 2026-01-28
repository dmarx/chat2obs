# tests/conftest.py
"""Root pytest configuration."""

import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as requiring database (deselect with '-m \"not integration\"')"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests in integration folder."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
