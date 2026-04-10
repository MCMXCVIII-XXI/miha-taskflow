from typing import ClassVar

from elasticsearch import AsyncElasticsearch, exceptions
from elasticsearch.dsl import AsyncDocument

from app.core.config import elasticsearch_settings
from app.indexes import (
    CommentDoc,
    NotificationDoc,
    TaskDoc,
    UserDoc,
    UserGroupDoc,
)

from .exceptions import es_exc


class IndexSettings:
    """Manages Elasticsearch index creation, deletion, and recreation operations.

    This class handles all index management operations for the application's
    Elasticsearch integration. It provides functionality to create, delete,
    and recreate indices for all document types used in the application.

    Attributes:
        DOCUMENTS (ClassVar[list[type[AsyncDocument]]]): List of document classes
            that require Elasticsearch indices
    """

    DOCUMENTS: ClassVar[list[type[AsyncDocument]]] = [
        UserDoc,
        TaskDoc,
        UserGroupDoc,
        CommentDoc,
        NotificationDoc,
    ]

    async def create_indices(self, client: AsyncElasticsearch) -> list[str]:
        """Create Elasticsearch indices for all document types.

        Creates indices for all document classes defined in DOCUMENTS if they
        don't already exist. Uses configured index prefix if specified.

        Args:
            client: Configured Elasticsearch client for index operations

        Returns:
            list[str]: List of created index names

        Raises:
            es_exc.ElasticsearchMappingError: If index creation fails
        """
        prefix = elasticsearch_settings.INDEX_PREFIX
        created = []

        for doc_class in self.DOCUMENTS:
            index_name = doc_class.Index.name
            full_name = f"{prefix}_{index_name}" if prefix else index_name

            if await client.indices.exists(index=full_name):
                continue

            try:
                index_obj = doc_class.Index.clone(name=full_name)
                await index_obj.create(using=client)
                created.append(full_name)
            except exceptions.RequestError as e:
                raise es_exc.ElasticsearchMappingError(
                    f"Failed to create {full_name}: {e}"
                ) from e

        return created

    async def delete_indices(self, client: AsyncElasticsearch) -> list[str]:
        """Delete Elasticsearch indices for all document types.

        Deletes indices for all document classes defined in DOCUMENTS if they
        exist. Uses configured index prefix if specified.

        Args:
            client: Configured Elasticsearch client for index operations

        Returns:
            list[str]: List of deleted index names

        Raises:
            es_exc.ElasticsearchIndexNotFoundError: If index deletion fails
        """
        prefix = elasticsearch_settings.INDEX_PREFIX
        deleted = []

        for doc_class in self.DOCUMENTS:
            index_name = doc_class.Index.name
            full_name = f"{prefix}_{index_name}" if prefix else index_name

            if not await client.indices.exists(index=full_name):
                continue

            try:
                await client.indices.delete(index=full_name, ignore_unavailable=True)
                deleted.append(full_name)
            except exceptions.RequestError as e:
                raise es_exc.ElasticsearchIndexNotFoundError(
                    f"Failed to delete {full_name}"
                ) from e

        return deleted

    async def recreate_indices(
        self, client: AsyncElasticsearch
    ) -> tuple[list[str], list[str]]:
        """Recreate all Elasticsearch indices by deleting and creating them.

        Performs a complete recreation of all indices by first deleting existing
        ones and then creating new ones. Useful for resetting the search index
        during development or testing.

        Args:
            client: Configured Elasticsearch client for index operations

        Returns:
            tuple[list[str], list[str]]: Tuple of (created_indices, deleted_indices)
        """
        deleted = await self.delete_indices(client)
        created = await self.create_indices(client)
        return created, deleted


es_index_settings = IndexSettings()
