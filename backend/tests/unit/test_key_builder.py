"""Unit tests for cache key_builder.

Tests the KeyBuilder class for cache key generation.
"""

import pytest

from app.cache.key_builder import KeyBuilder


@pytest.fixture
def key_builder():
    """Create KeyBuilder instance."""
    return KeyBuilder()


class TestNormalizeParams:
    """Tests for normalize_params method."""

    def test_simple_params(self, key_builder):
        """Simple key-value params get normalized."""
        result = key_builder.normalize_params({"user_id": "123", "limit": "10"})
        assert "user_id_123" in result
        assert "limit_10" in result

    def test_ampersand_separator(self, key_builder):
        """Ampersand becomes pipe separator."""
        result = key_builder.normalize_params({"q": "test", "limit": "10"})
        assert "|" in result

    def test_special_chars_escaped(self, key_builder):
        """Special characters get escaped."""
        result = key_builder.normalize_params({"q": "test?"})
        assert "?" not in result or "%" in result

    def test_lowercase_conversion(self, key_builder):
        """Keys get lowercased."""
        result = key_builder.normalize_params({"USER_ID": "123"})
        assert "user_id" in result

    def test_empty_params(self, key_builder):
        """Empty params return empty string."""
        result = key_builder.normalize_params({})
        assert result == ""


class TestBuildKey:
    """Tests for build_key method."""

    def test_build_key_minimal(self, key_builder):
        """Minimal key with only required fields."""
        result = key_builder.build_key(
            layer="api", area="search", entity="task", action="list"
        )
        assert "taskflow" in result
        assert "api" in result
        assert "task" in result
        assert "list" in result

    def test_build_key_with_params(self, key_builder):
        """Key with query parameters."""
        result = key_builder.build_key(
            layer="api",
            area="search",
            entity="task",
            action="search",
            params={"q": "test", "limit": "10"},
        )
        assert "search" in result

    def test_build_key_user_detail(self, key_builder):
        """User detail key."""
        result = key_builder.build_key(
            layer="api",
            area="rbac",
            entity="user",
            action="detail",
            params={"user_id": "123"},
        )
        assert "user" in result
        assert "detail" in result

    def test_build_key_with_dev_env(self, key_builder):
        """Key uses dev environment."""
        result = key_builder.build_key(
            layer="api", area="search", entity="task", action="list", env="dev"
        )
        assert result.startswith("dev:")

    def test_build_key_with_staging_env(self, key_builder):
        """Key uses staging environment."""
        result = key_builder.build_key(
            layer="api", area="search", entity="task", action="list", env="staging"
        )
        assert result.startswith("staging:")


class TestKeyBuilderConstants:
    """Tests for key builder constants."""

    def test_env_values(self):
        """Environment values are valid."""
        assert "prod" in KeyBuilder.ENV
        assert "dev" in KeyBuilder.ENV

    def test_layers_values(self):
        """Layer values are valid."""
        assert "api" in KeyBuilder.LAYERS
        assert "service" in KeyBuilder.LAYERS

    def test_areas_values(self):
        """Area values are valid."""
        assert "search" in KeyBuilder.AREAS
        assert "xp" in KeyBuilder.AREAS

    def test_entities_values(self):
        """Entity values are valid."""
        assert "task" in KeyBuilder.ENTITIES
        assert "user" in KeyBuilder.ENTITIES

    def test_prefix_constant(self):
        """Prefix is taskflow."""
        assert KeyBuilder.PREFIX == "taskflow"

    def test_version_constant(self):
        """Version is v1."""
        assert KeyBuilder.VERSION == "v1"

    def test_lifetime_constant(self):
        """Lifetime is temp."""
        assert KeyBuilder.LIFETIME == "temp"


class TestKeyFormat:
    """Tests for key format structure."""

    def test_format_has_all_parts(self, key_builder):
        """Key contains all required parts."""
        result = key_builder.build_key(
            layer="api", area="search", entity="task", action="list"
        )
        parts = result.split(":")
        assert len(parts) >= 5

    def test_format_starts_with_prod(self, key_builder):
        """Key starts with environment."""
        result = key_builder.build_key(
            layer="api", area="search", entity="task", action="list"
        )
        assert result.startswith("prod:")

    def test_format_includes_prefix(self, key_builder):
        """Key includes prefix."""
        result = key_builder.build_key(
            layer="api", area="search", entity="task", action="list"
        )
        assert "taskflow" in result

    def test_format_includes_version(self, key_builder):
        """Key includes version."""
        result = key_builder.build_key(
            layer="api", area="search", entity="task", action="list"
        )
        assert "v1" in result


class TestInferMethods:
    """Tests for _infer_* methods."""

    def test_infer_layer_api(self, key_builder):
        """Infer layer from api module."""
        result = key_builder._infer_layer("app.api.v1.endpoints.task")
        assert result == "api"

    def test_infer_layer_service(self, key_builder):
        """Infer layer from service module."""
        result = key_builder._infer_layer("app.service.task")
        assert result == "service"

    def test_infer_layer_db(self, key_builder):
        """Infer layer from query_db module."""
        result = key_builder._infer_layer("app.service.query_db.task")
        assert result == "db"

    def test_infer_layer_es(self, key_builder):
        """Infer layer from es module."""
        result = key_builder._infer_layer("app.es.search")
        assert result == "es"

    def test_infer_area_search(self, key_builder):
        """Infer area search."""
        result = key_builder._infer_area("app.service.search")
        assert result == "search"

    def test_infer_area_rbac(self, key_builder):
        """Infer area rbac."""
        result = key_builder._infer_area("app.core.permission")
        assert result == "rbac"

    def test_infer_area_auth(self, key_builder):
        """Infer area auth."""
        result = key_builder._infer_area("app.service.auth")
        assert result == "auth"

    def test_infer_area_xp(self, key_builder):
        """Infer area xp."""
        result = key_builder._infer_area("app.service.xp")
        assert result == "xp"

    def test_infer_search_entity_task(self, key_builder):
        """Infer search entity task."""
        result = key_builder._infer_search_entity("/tasks/search")
        assert result == "task"

    def test_infer_search_entity_user(self, key_builder):
        """Infer search entity user."""
        result = key_builder._infer_search_entity("/users/search")
        assert result == "user"

    def test_infer_search_entity_group(self, key_builder):
        """Infer search entity group."""
        result = key_builder._infer_search_entity("/groups/search")
        assert result == "group"
