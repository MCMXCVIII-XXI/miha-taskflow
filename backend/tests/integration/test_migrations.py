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
                    "WHERE table_name = 'users' "
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
                    "WHERE table_name = 'tasks' "
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
                    "SELECT tc.constraint_name "
                    "FROM information_schema.table_constraints tc "
                    "JOIN information_schema.key_column_usage kcu "
                    "ON tc.constraint_name = kcu.constraint_name "
                    "WHERE tc.table_name = 'tasks' "
                    "AND tc.constraint_type = 'FOREIGN KEY' "
                    "AND kcu.column_name = 'group_id'"
                )
            )
            fk = result.scalar()
            assert fk is not None, "tasks.group_id must have foreign key"

    async def test_user_roles_have_user_fk(self, test_engine: AsyncEngine):
        """user_roles.user_id should have foreign key to users."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT tc.constraint_name "
                    "FROM information_schema.table_constraints tc "
                    "JOIN information_schema.key_column_usage kcu "
                    "ON tc.constraint_name = kcu.constraint_name "
                    "WHERE tc.table_name = 'user_roles' "
                    "AND tc.constraint_type = 'FOREIGN KEY' "
                    "AND kcu.column_name = 'user_id'"
                )
            )
            fk = result.scalar()
            assert fk is not None, "user_roles.user_id must have foreign key"


class TestIndexes:
    """Verify indexes exist (only PostgreSQL)."""

    async def test_users_username_has_index(self, test_engine: AsyncEngine):
        """users.username should have unique index."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT indexname, indexdef "
                    "FROM pg_indexes "
                    "WHERE tablename = 'users' "
                    "AND indexname LIKE '%username%'"
                )
            )
            indexes = result.fetchall()
            assert len(indexes) > 0, "users.username should have index"

    async def test_tasks_group_id_has_index(self, test_engine: AsyncEngine):
        """tasks.group_id should have index."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT indexname "
                    "FROM pg_indexes "
                    "WHERE tablename = 'tasks' "
                    "AND indexname LIKE '%group_id%'"
                )
            )
            indexes = result.fetchall()
            assert len(indexes) > 0, "tasks.group_id should have index"


class TestConstraints:
    """Verify constraints exist (only PostgreSQL)."""

    async def test_users_username_is_unique(self, test_engine: AsyncEngine):
        """users.username should have UNIQUE constraint."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT tc.constraint_name "
                    "FROM information_schema.table_constraints tc "
                    "WHERE tc.table_name = 'users' "
                    "AND tc.constraint_type = 'UNIQUE' "
                    "AND tc.constraint_name LIKE '%username%'"
                )
            )
            constraint = result.scalar()
            assert constraint is not None, "users.username must be unique"

    async def test_users_email_is_not_nullable(self, test_engine: AsyncEngine):
        """users.email should be NOT NULL."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_name = 'users' "
                    "AND column_name = 'email'"
                )
            )
            nullable = result.scalar()
            assert nullable == "NO", "users.email must be NOT NULL"


class TestDefaultValues:
    """Verify default values (only PostgreSQL)."""

    async def test_users_is_active_default_true(self, test_engine: AsyncEngine):
        """users.is_active should default to TRUE."""
        if not is_postgresql(test_engine):
            pytest.skip("Test is only for PostgreSQL")

        async with test_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT column_default "
                    "FROM information_schema.columns "
                    "WHERE table_name = 'users' "
                    "AND column_name = 'is_active'"
                )
            )
            default = result.scalar()
            assert default is not None, "users.is_active must have DEFAULT"
            assert "true" in default.lower(), (
                f"users.is_active should default to TRUE, got {default}"
            )
