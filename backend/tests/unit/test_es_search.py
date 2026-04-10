from unittest.mock import AsyncMock, MagicMock

import pytest
from elasticsearch.dsl import Search

from app.es import es_helper
from app.es.faceted_search import (
    CommentFacetedSearch,
    GroupFacetedSearch,
    NotificationFacetedSearch,
    TaskFacetedSearch,
    UserFacetedSearch,
)
from app.es.search import ElasticsearchSearch


class TestElasticsearchSearch:
    """Unit tests for ElasticsearchSearch."""

    @pytest.fixture
    def mock_es_client(self):
        client = MagicMock()
        client.search = AsyncMock()
        return client

    @pytest.fixture
    def search(self, mock_es_client):
        return ElasticsearchSearch(mock_es_client)

    @pytest.mark.asyncio
    async def test_search_instantiation(self, mock_es_client):
        """Test search can be instantiated."""
        search = ElasticsearchSearch(mock_es_client)
        assert search._client is mock_es_client

    @pytest.mark.asyncio
    async def test_get_total_with_value(self, search):
        """Test _get_total method with value."""
        mock_response = MagicMock()
        mock_response.hits.total.value = 100

        total = search._get_total(mock_response)
        assert total == 100

    @pytest.mark.asyncio
    async def test_get_total_with_none(self, search):
        """Test _get_total with None value returns 0."""
        mock_response = MagicMock()
        mock_response.hits.total.value = None
        mock_response.hits.total = None

        total = search._get_total(mock_response)
        assert total == 0

    @pytest.mark.asyncio
    async def test_extract_facets_empty(self, search):
        """Test _extract_facets with empty response."""
        mock_response = MagicMock()
        mock_response.aggregations = MagicMock()

        result = search._extract_facets(mock_response, {}, None)

        assert result == {}

    @pytest.mark.asyncio
    async def test_apply_query_and_filters_no_query(self, search):
        """Test _apply_query_and_filters with no query."""
        mock_search = MagicMock(spec=Search)
        mock_search.query = MagicMock(return_value=mock_search)
        mock_search.filter = MagicMock(return_value=mock_search)

        result = search._apply_query_and_filters(mock_search, "", None, None)

        assert result is mock_search

    @pytest.mark.asyncio
    async def test_apply_query_and_filters_with_query(self, search):
        """Test _apply_query_and_filters with query."""
        mock_search = MagicMock(spec=Search)
        mock_search.query = MagicMock(return_value=mock_search)
        mock_search.filter = MagicMock(return_value=mock_search)

        result = search._apply_query_and_filters(mock_search, "test", None, ["title^3"])

        assert result is mock_search

    @pytest.mark.asyncio
    async def test_apply_query_and_filters_with_filters(self, search):
        """Test _apply_query_and_filters with filters."""
        mock_search = MagicMock(spec=Search)
        mock_search.query = MagicMock(return_value=mock_search)
        mock_search.filter = MagicMock(return_value=mock_search)

        result = search._apply_query_and_filters(
            mock_search, "", {"status": "pending"}, None
        )

        assert result is mock_search


class TestElasticsearchHelper:
    """Unit tests for ElasticsearchHelper (es_helper)."""

    @pytest.mark.asyncio
    async def test_es_helper_instantiation(self):
        """Test es_helper can be imported."""
        assert es_helper is not None

    @pytest.mark.asyncio
    async def test_es_helper_has_get_client(self):
        """Test es_helper has get_client method."""
        assert hasattr(es_helper, "get_client")
        assert callable(es_helper.get_client)

    @pytest.mark.asyncio
    async def test_es_helper_has_dispose(self):
        """Test es_helper has dispose method."""
        assert hasattr(es_helper, "dispose")
        assert callable(es_helper.dispose)


class TestFacetedSearchClasses:
    """Unit tests for FacetedSearch classes."""

    @pytest.mark.asyncio
    async def test_task_faceted_search_attributes(self):
        """Test TaskFacetedSearch has correct attributes."""
        assert TaskFacetedSearch.doc_types is not None
        assert TaskFacetedSearch.fields is not None
        assert TaskFacetedSearch.facets is not None

    @pytest.mark.asyncio
    async def test_user_faceted_search_attributes(self):
        """Test UserFacetedSearch has correct attributes."""
        assert UserFacetedSearch.doc_types is not None
        assert UserFacetedSearch.fields is not None
        assert UserFacetedSearch.facets is not None

    @pytest.mark.asyncio
    async def test_group_faceted_search_attributes(self):
        """Test GroupFacetedSearch has correct attributes."""
        assert GroupFacetedSearch.doc_types is not None
        assert GroupFacetedSearch.fields is not None
        assert GroupFacetedSearch.facets is not None

    @pytest.mark.asyncio
    async def test_comment_faceted_search_attributes(self):
        """Test CommentFacetedSearch has correct attributes."""
        assert CommentFacetedSearch.doc_types is not None
        assert CommentFacetedSearch.fields is not None
        assert CommentFacetedSearch.facets is not None

    @pytest.mark.asyncio
    async def test_notification_faceted_search_attributes(self):
        """Test NotificationFacetedSearch has correct attributes."""
        assert NotificationFacetedSearch.doc_types is not None
        assert NotificationFacetedSearch.fields is not None
        assert NotificationFacetedSearch.facets is not None
