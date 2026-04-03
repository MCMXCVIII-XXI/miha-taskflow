"""
Main test configuration - switches between SQLite and PostgreSQL.

SQLite:  make test-sqlite (default, fast)
PostgreSQL: make test-pg (uses Testcontainers)
"""

import os

# Detect which database to use
USE_POSTGRES = os.getenv("POSTGRES_DB") is not None

if USE_POSTGRES:
    # Import PostgreSQL fixtures from pg_conftest
    from tests.pg_conftest import *  # noqa: F403
else:
    # Import SQLite fixtures from conftest_sqlite
    from tests.conftest_sqlite import *  # noqa: F403
