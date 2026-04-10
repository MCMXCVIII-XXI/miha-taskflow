from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from elasticsearch.dsl import Search

from app.es import es_helper
from app.es.indexer import ElasticsearchIndexer
from app.es.search import ElasticsearchSearch


class TestElasticsearchIndexer:
    """Unit tests for ElasticsearchIndexer."""

    @pytest.fixture
    def mock_es_client(self):
        client = MagicMock()
        client.index = AsyncMock()
        client.delete = AsyncMock()
        client.bulk = AsyncMock()
        client.indices = MagicMock()
        client.indices.refresh = AsyncMock()
        return client

    @pytest.fixture
    def indexer(self, mock_es_client):
        return ElasticsearchIndexer(mock_es_client)

    @pytest.mark.asyncio
    async def test_indexer_instantiation(self, mock_es_client):
        """Test indexer can be instantiated."""
        indexer = ElasticsearchIndexer(mock_es_client)
        assert indexer._client is mock_es_client

    @pytest.mark.asyncio
    async def test_delete_task_calls_client(self, indexer, mock_es_client):
        """Test delete_task calls the client correctly."""
        with patch("app.es.indexer.TaskDoc") as MockTaskDoc:
            mock_doc = MagicMock()
            mock_doc.delete = AsyncMock()
            MockTaskDoc.get = AsyncMock(return_value=mock_doc)

            result = await indexer.delete_task(1)

            MockTaskDoc.get.assert_called_once_with(
                id=str(1), using=mock_es_client, ignore_status=(404,)
            )
            mock_doc.delete.assert_called_once()
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, indexer, mock_es_client):
        """Test deleting non-existent task returns False."""
        with patch("app.es.indexer.TaskDoc") as MockTaskDoc:
            MockTaskDoc.get = AsyncMock(return_value=None)

            result = await indexer.delete_task(999)

            assert result is False

    @pytest.mark.asyncio
    async def test_delete_user_calls_client(self, indexer, mock_es_client):
        """Test delete_user calls the client correctly."""
        with patch("app.es.indexer.UserDoc") as MockUserDoc:
            mock_doc = MagicMock()
            mock_doc.delete = AsyncMock()
            MockUserDoc.get = AsyncMock(return_value=mock_doc)

            result = await indexer.delete_user(1)

            MockUserDoc.get.assert_called_once_with(
                id=str(1), using=mock_es_client, ignore_status=(404,)
            )
            mock_doc.delete.assert_called_once()
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_group_calls_client(self, indexer, mock_es_client):
        """Test delete_group calls the client correctly."""
        with patch("app.es.indexer.UserGroupDoc") as MockGroupDoc:
            mock_doc = MagicMock()
            mock_doc.delete = AsyncMock()
            MockGroupDoc.get = AsyncMock(return_value=mock_doc)

            result = await indexer.delete_group(1)

            MockGroupDoc.get.assert_called_once_with(
                id=str(1), using=mock_es_client, ignore_status=(404,)
            )
            mock_doc.delete.assert_called_once()
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_comment_calls_client(self, indexer, mock_es_client):
        """Test delete_comment calls the client correctly."""
        with patch("app.es.indexer.CommentDoc") as MockCommentDoc:
            mock_doc = MagicMock()
            mock_doc.delete = AsyncMock()
            MockCommentDoc.get = AsyncMock(return_value=mock_doc)

            result = await indexer.delete_comment(1)

            MockCommentDoc.get.assert_called_once_with(
                id=str(1), using=mock_es_client, ignore_status=(404,)
            )
            mock_doc.delete.assert_called_once()
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_notification_calls_client(self, indexer, mock_es_client):
        """Test delete_notification calls the client correctly."""
        with patch("app.es.indexer.NotificationDoc") as MockNotifDoc:
            mock_doc = MagicMock()
            mock_doc.delete = AsyncMock()
            MockNotifDoc.get = AsyncMock(return_value=mock_doc)

            result = await indexer.delete_notification(1)

            MockNotifDoc.get.assert_called_once_with(
                id=str(1), using=mock_es_client, ignore_status=(404,)
            )
            mock_doc.delete.assert_called_once()
            assert result is True

    @pytest.mark.asyncio
    async def test_refresh_all_calls_client(self, indexer, mock_es_client):
        """Test refresh_all calls the client correctly."""
        await indexer.refresh_all()

        mock_es_client.indices.refresh.assert_called_once()


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
