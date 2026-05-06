"""E2E test configuration - reuses fixtures from pg_conftest."""

pytest_plugins = ["tests.pg_conftest"]


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "celery_real: tests with real Celery broker")
