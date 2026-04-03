"""
Smoke tests for PostgreSQL migrations.

Verifies that Alembic migrations match SQLAlchemy models
and that all columns are configured correctly.

Note: The tests ONLY work with PostgreSQL.
To run: make test-pg
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


def is_postgresql(engine: AsyncEngine) -> bool:
    """Check if the engine is PostgreSQL."""
    url_str = str(engine.url)
    return "postgresql" in url_str


class TestMigrationIntegrity:
    """Check migration integrity (only PostgreSQL)."""

    async def test_user_roles_has_autoincrement(self, test_engine: AsyncEngine):
        """user_roles.id should have a sequence for autoincrement."""
        if not is_postgresql(test_engine):
            pytest.skip("Тест только для PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT column_default "
                    "FROM information_schema.columns "
                    "WHERE table_name = 'user_roles' "
                    "AND column_name = 'id'"
                )
            )
            default = result.scalar()
            assert default is not None, "user_roles.id must have a DEFAULT"
            assert "nextval" in default, (
                f"user_roles.id The DEFAULT must be sequence, received: {default}"
            )

    async def test_all_id_columns_have_sequences(self, test_engine: AsyncEngine):
        """All id columns must have a sequence (autoincrement)."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name, column_default "
                    "FROM information_schema.columns "
                    "WHERE column_name = 'id' "
                    "AND table_schema = 'public' "
                    "AND table_name NOT IN ('alembic_version') "
                    "ORDER BY table_name"
                )
            )
            rows = result.fetchall()

            for table_name, column_default in rows:
                assert column_default is not None, (
                    f"{table_name}.id must have a DEFAULT sequence, "
                    f"received: {column_default}"
                )
                assert "nextval" in column_default, (
                    f"{table_name}.id DEFAULT must be a sequence, "
                    f"received: {column_default}"
                )

    async def test_models_match_migrations(self, test_engine: AsyncEngine):
        """Models SQLAlchemy should match migrations."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        from app.db.base import Base

        model_tables = set(Base.metadata.tables.keys())

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name "
                    "FROM information_schema.tables "
                    "WHERE table_schema = 'public' "
                    "AND table_type = 'BASE TABLE' "
                    "AND table_name NOT IN ('alembic_version')"
                )
            )
            db_tables = {row[0] for row in result.fetchall()}

        missing_tables = model_tables - db_tables
        assert not missing_tables, (
            f"Tables from models are missing in DB: {missing_tables}"
        )
