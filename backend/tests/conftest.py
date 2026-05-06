"""
Main test configuration - switches between SQLite and PostgreSQL.

SQLite:  make test-sqlite (default, fast)
PostgreSQL: make test-pg (uses Testcontainers)
"""

import os

# Detect which database to use
USE_POSTGRES = os.getenv("POSTGRES_DB") is not None

if USE_POSTGRES:
    # Integration tests with PostgreSQL
    from tests.pg_conftest import *  # noqa: F403
else:
    # Unit tests with SQLite
    from tests.conftest_sqlite import *  # noqa: F403
