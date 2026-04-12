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
                    f"{table_name}.id must have sequence, got {column_default}"
                )
                assert "nextval" in column_default, (
                    f"{table_name}.id must be sequence, got {column_default}"
                )

    async def test_models_match_migrations(self, test_engine: AsyncEngine):
        """Models SQLAlchemy should match migrations (both ways)."""
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
        extra_tables = db_tables - model_tables

        assert not missing_tables, f"Tables missing in DB: {missing_tables}"
        assert not extra_tables, f"Extra tables in DB (not in models): {extra_tables}"


class TestColumnTypes:
    """Verify column types match expected (only PostgreSQL)."""

    async def test_user_username_is_varchar_50(self, test_engine: AsyncEngine):
        """users.username should be VARCHAR(50)."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT data_type, character_maximum_length "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'users' "
                    "AND column_name = 'username'"
                )
            )
            row = result.fetchone()
            assert row is not None, "users.username must exist"
            assert row[0] == "character varying", f"Expected VARCHAR, got {row[0]}"
            assert row[1] == 50, f"Expected length 50, got {row[1]}"

    async def test_task_is_active_is_boolean(self, test_engine: AsyncEngine):
        """tasks.is_active should be BOOLEAN."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT data_type "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'tasks' "
                    "AND column_name = 'is_active'"
                )
            )
            data_type = result.scalar()
            assert data_type == "boolean", f"Expected boolean, got {data_type}"


class TestForeignKeys:
    """Verify foreign keys exist (only PostgreSQL)."""

    async def test_tasks_have_group_fk(self, test_engine: AsyncEngine):
        """tasks.group_id should have foreign key to user_groups."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM information_schema.table_constraints tc "
                    "JOIN information_schema.key_column_usage kcu "
                    "ON tc.constraint_name = kcu.constraint_name "
                    "WHERE tc.table_schema = 'public' "
                    "AND tc.table_name = 'tasks' "
                    "AND tc.constraint_type = 'FOREIGN KEY' "
                    "AND kcu.column_name = 'group_id'"
                )
            )
            count = result.scalar()
            assert count > 0, "tasks.group_id must have foreign key"

    async def test_user_roles_have_user_fk(self, test_engine: AsyncEngine):
        """user_roles.user_id should have foreign key to users."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM information_schema.table_constraints tc "
                    "JOIN information_schema.key_column_usage kcu "
                    "ON tc.constraint_name = kcu.constraint_name "
                    "WHERE tc.table_schema = 'public' "
                    "AND tc.table_name = 'user_roles' "
                    "AND tc.constraint_type = 'FOREIGN KEY' "
                    "AND kcu.column_name = 'user_id'"
                )
            )
            count = result.scalar()
            assert count > 0, "user_roles.user_id must have foreign key"


class TestIndexes:
    """Verify indexes exist (only PostgreSQL)."""

    async def test_users_username_has_index(self, test_engine: AsyncEngine):
        """users.username should have unique index."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM pg_indexes "
                    "WHERE schemaname = 'public' "
                    "AND tablename = 'users' "
                    "AND indexdef LIKE '%username%'"
                )
            )
            count = result.scalar()
            assert count > 0, "users.username should have index"

    async def test_tasks_group_id_has_index(self, test_engine: AsyncEngine):
        """tasks.group_id should have an index on the column."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT indexdef "
                    "FROM pg_indexes "
                    "WHERE schemaname = 'public' "
                    "AND tablename = 'tasks' "
                    "AND indexdef LIKE '%group_id%'"
                )
            )
            indexdef = result.scalar()
            assert indexdef is not None, "tasks.group_id must have index"
            assert "group_id" in indexdef, (
                f"Index must be on group_id column, got: {indexdef}"
            )


class TestConstraints:
    """Verify constraints exist (only PostgreSQL)."""

    async def test_users_username_is_unique(self, test_engine: AsyncEngine):
        """users.username should have unique index (via pg_indexes)."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM pg_indexes "
                    "WHERE schemaname = 'public' "
                    "AND tablename = 'users' "
                    "AND indexdef LIKE '%username%' "
                    "AND indexdef LIKE '%UNIQUE%'"
                )
            )
            count = result.scalar()
            assert count > 0, "users.username must have UNIQUE index"

    async def test_users_email_is_unique(self, test_engine: AsyncEngine):
        """users.email should have unique index (via pg_indexes)."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM pg_indexes "
                    "WHERE schemaname = 'public' "
                    "AND tablename = 'users' "
                    "AND indexdef LIKE '%email%' "
                    "AND indexdef LIKE '%UNIQUE%'"
                )
            )
            count = result.scalar()
            assert count > 0, "users.email must have UNIQUE index"

    async def test_users_email_is_not_nullable(self, test_engine: AsyncEngine):
        """users.email should be NOT NULL."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'users' "
                    "AND column_name = 'email'"
                )
            )
            nullable = result.scalar()
            assert nullable == "NO", "users.email must be NOT NULL"


class TestDefaultValues:
    """Verify default values (only PostgreSQL)."""

    async def test_users_is_active_not_null(self, test_engine: AsyncEngine):
        """users.is_active should be NOT NULL."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'users' "
                    "AND column_name = 'is_active'"
                )
            )
            nullable = result.scalar()
            assert nullable == "NO", "users.is_active should be NOT NULL"
