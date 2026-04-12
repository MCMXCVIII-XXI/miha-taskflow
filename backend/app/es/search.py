from typing import Any

from elasticsearch import AsyncElasticsearch
from elasticsearch.dsl import AsyncSearch
from fastapi import Depends

from app.indexes import CommentDoc, NotificationDoc, TaskDoc, UserDoc, UserGroupDoc
from app.schemas import CommentRead, NotificationRead, TaskRead, UserGroupRead, UserRead

from .client import es_helper
from .faceted_search import (
    CommentFacetedSearch,
    GroupFacetedSearch,
    NotificationFacetedSearch,
    TaskFacetedSearch,
    UserFacetedSearch,
)


class ElasticsearchSearch:
    """Provides full-text and filtered search functionality using Elasticsearch.

    Implements search operations across all indexed application entities including
    users, groups, tasks, comments, and notifications. Supports both text-based
    searches and structured filtering with pagination controls.

    Attributes:
        _client (AsyncElasticsearch): Elasticsearch client for search operations
    """

    def __init__(self, client: AsyncElasticsearch):
        """Initialize search service with Elasticsearch client.

        Args:
            client (AsyncElasticsearch): Configured Elasticsearch client
        """
        self._client = client

    def _apply_query_and_filters(
        self,
        s: AsyncSearch[Any],
        query: str,
        filters: dict[str, Any] | None,
        fields: list[str] | None = None,
    ) -> AsyncSearch[Any]:
        """Apply search query and filters to Elasticsearch search object.

        Applies multi-field text search using multi_match query and adds
        term filters for structured data filtering.

        Args:
            s: Elasticsearch AsyncSearch object to modify
            query: Text search query string
            filters: Dictionary of field-value pairs for term filtering
            fields: List of fields to search in (for multi_match query)

        Returns:
            AsyncSearch[Any]: Modified search object with query and filters applied
        """
        if query and fields:
            s = s.query("multi_match", query=query, fields=fields)
        if filters:
            for key, value in filters.items():
                if value is not None:
                    s = s.filter("term", **{key: value})
        return s

    async def search_tasks(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[TaskRead]:
        """Search for tasks using text query and filters.

        Performs full-text search on task titles, descriptions, and group names
        with configurable filtering and pagination. Results are sorted by
        relevance score and creation date.

        Args:
            query: Text search query for task titles, descriptions, etc.
            filters: Dictionary of field-value pairs for filtering results
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            list[TaskRead]: List of matching tasks in read format
        """
        s = TaskDoc.search(using=self._client)[offset : offset + limit]
        s = s.sort({"_score": {"order": "desc"}}).sort(
            {"created_at": {"order": "desc"}}
        )
        s = self._apply_query_and_filters(
            s, query, filters, fields=["title^3", "description^2", "group_name"]
        )
        response = await s.execute()
        return [hit.to_read_schema() for hit in response]

    async def search_users(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[UserRead]:
        """Search for users using text query and filters.

        Performs full-text search on user attributes including username,
        names, and email with configurable filtering and pagination.

        Args:
            query: Text search query for user attributes
            filters: Dictionary of field-value pairs for filtering results
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            list[UserRead]: List of matching users in read format
        """
        s = UserDoc.search(using=self._client)[offset : offset + limit]
        s = self._apply_query_and_filters(
            s,
            query,
            filters,
            fields=["username^3", "first_name^2", "last_name^2", "email"],
        )
        response = await s.execute()
        return [hit.to_read_schema() for hit in response]

    async def search_groups(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[UserGroupRead]:
        """Search for groups using text query and filters.

        Performs full-text search on group attributes including name,
        description, and administrator username with configurable filtering
        and pagination.

        Args:
            query: Text search query for group attributes
            filters: Dictionary of field-value pairs for filtering results
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            list[UserGroupRead]: List of matching groups in read format
        """
        s = UserGroupDoc.search(using=self._client)[offset : offset + limit]
        s = self._apply_query_and_filters(
            s, query, filters, fields=["name^3", "description^2", "admin_username"]
        )
        response = await s.execute()
        return [hit.to_read_schema() for hit in response]

    async def search_comments(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[CommentRead]:
        """Search for comments using text query and filters.

        Performs full-text search on comment content and related attributes
        with configurable filtering and pagination.

        Args:
            query: Text search query for comment content and related attributes
            filters: Dictionary of field-value pairs for filtering results
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            list[CommentRead]: List of matching comments in read format
        """
        s = CommentDoc.search(using=self._client)[offset : offset + limit]
        s = self._apply_query_and_filters(
            s, query, filters, fields=["content^2", "task_title", "username"]
        )
        response = await s.execute()
        return [hit.to_read_schema() for hit in response]

    async def search_notifications(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[NotificationRead]:
        """Search for notifications using text query and filters.

        Performs full-text search on notification attributes with configurable
        filtering and pagination.

        Args:
            query: Text search query for notification attributes
            filters: Dictionary of field-value pairs for filtering results
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            list[NotificationRead]: List of matching notifications in read format
        """
        s = NotificationDoc.search(using=self._client)[offset : offset + limit]
        s = self._apply_query_and_filters(
            s,
            query,
            filters,
            fields=[
                "title^3",
                "message^2",
                "type",
            ],
        )
        response = await s.execute()
        return [hit.to_read_schema() for hit in response]

    def _get_total(self, response: Any) -> int:
        """Safely extract total hit count from Elasticsearch response.

        Handles different versions of Elasticsearch response formats for
        total hit count extraction.

        Args:
            response: Elasticsearch response object

        Returns:
            int: Total number of hits
        """
        total = getattr(response.hits.total, "value", None)
        return (
            int(total)
            if total is not None
            else getattr(response.hits.total, "value", 0)
        )

    def _extract_facets(
        self,
        response: Any,
        facets_config: dict[str, Any],
        filters: dict[str, Any] | None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Extract facet data from Elasticsearch response.

        Processes aggregation results from Elasticsearch response and formats
        them for use in faceted search UI components.

        Args:
            response: Elasticsearch response containing aggregation data
            facets_config: Configuration of facets to extract
            filters: Current filter selections for marking selected facets

        Returns:
            dict[str, list[dict[str, Any]]]: Dictionary mapping facet names to
                lists of facet data including key, count, and selection status
        """
        facets: dict[str, list[dict[str, Any]]] = {}
        for name in facets_config.keys():
            facets[name] = []
            facet_data = getattr(response.aggregations, name, None)
            if facet_data and hasattr(facet_data, "buckets"):
                for bucket in facet_data.buckets:
                    facets[name].append(
                        {
                            "key": bucket.key,
                            "count": bucket.doc_count,
                            "selected": bucket.key in (filters or {}),
                        }
                    )
        return facets

    async def _search_faceted(
        self,
        faceted_class: Any,
        facets_config: dict[str, Any],
        query: str = "",
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Perform generic faceted search using Elasticsearch DSL.

        Executes faceted search with query, filters, and pagination, returning
        both search results and facet data for filtering UI.

        Args:
            faceted_class: Elasticsearch faceted search class to use
            facets_config: Configuration of facets for this search type
            query: Text search query string (optional)
            filters: Dictionary of field-value pairs for filtering (optional)
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            dict[str, Any]: Dictionary containing results, facets, total count,
                and pagination information
        """
        fs = faceted_class()
        if query:
            fs = fs.query(query)
        if filters:
            fs = fs.filter(filters)
        fs = fs[offset : offset + limit]

        response = await fs.execute()

        results = [hit.to_read_schema() for hit in response]
        facets = self._extract_facets(response, facets_config, filters)
        total = self._get_total(response)

        return {
            "results": results,
            "facets": facets,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def search_tasks_faceted(
        self,
        query: str = "",
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Perform faceted search for tasks with filtering options.

        Provides advanced task search with faceted navigation capabilities
        including filtering by status, priority, difficulty, and other attributes.
        Returns both search results and available facets for UI filtering.

        Args:
            query: Text search query string (optional)
            filters: Dictionary of field-value pairs for filtering (optional)
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            dict[str, Any]: Dictionary containing task results, facets, total count,
                and pagination information
        """
        return await self._search_faceted(
            TaskFacetedSearch,
            TaskFacetedSearch.facets,
            query,
            filters,
            limit,
            offset,
        )

    async def search_users_faceted(
        self,
        query: str = "",
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Perform faceted search for users with filtering options.

        Provides advanced user search with faceted navigation capabilities
        including filtering by role, active status, and group membership.
        Returns both search results and available facets for UI filtering.

        Args:
            query: Text search query string (optional)
            filters: Dictionary of field-value pairs for filtering (optional)
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            dict[str, Any]: Dictionary containing user results, facets, total count,
                and pagination information
        """
        return await self._search_faceted(
            UserFacetedSearch,
            UserFacetedSearch.facets,
            query,
            filters,
            limit,
            offset,
        )

    async def search_groups_faceted(
        self,
        query: str = "",
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Perform faceted search for groups with filtering options.

        Provides advanced group search with faceted navigation capabilities
        including filtering by visibility, join policy, and invite policy.
        Returns both search results and available facets for UI filtering.

        Args:
            query: Text search query string (optional)
            filters: Dictionary of field-value pairs for filtering (optional)
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            dict[str, Any]: Dictionary containing group results, facets, total count,
                and pagination information
        """
        return await self._search_faceted(
            GroupFacetedSearch,
            GroupFacetedSearch.facets,
            query,
            filters,
            limit,
            offset,
        )

    async def search_comments_faceted(
        self,
        query: str = "",
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Perform faceted search for comments with filtering options.

        Provides advanced comment search with faceted navigation capabilities
        including filtering by task and user. Returns both search results and
        available facets for UI filtering.

        Args:
            query: Text search query string (optional)
            filters: Dictionary of field-value pairs for filtering (optional)
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            dict[str, Any]: Dictionary containing comment results, facets, total count,
                and pagination information
        """
        return await self._search_faceted(
            CommentFacetedSearch,
            CommentFacetedSearch.facets,
            query,
            filters,
            limit,
            offset,
        )

    async def search_notifications_faceted(
        self,
        query: str = "",
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Perform faceted search for notifications with filtering options.

        Provides advanced notification search with faceted navigation capabilities
        including filtering by type, status, sender, recipient, and target type.
        Returns both search results and available facets for UI filtering.

        Args:
            query: Text search query string (optional)
            filters: Dictionary of field-value pairs for filtering (optional)
            limit: Maximum number of results to return (default: 10)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            dict[str, Any]: Dictionary containing notification
                results, facets, total count and pagination information
        """
        return await self._search_faceted(
            NotificationFacetedSearch,
            NotificationFacetedSearch.facets,
            query,
            filters,
            limit,
            offset,
        )


def get_es_search(
    es: AsyncElasticsearch = Depends(es_helper.get_client),
) -> ElasticsearchSearch:
    """Create ElasticsearchSearch service instance with client dependency.

    Args:
        es: Elasticsearch client dependency injected by FastAPI

    Returns:
        ElasticsearchSearch: Initialized Elasticsearch search service instance
    """
    return ElasticsearchSearch(client=es)
