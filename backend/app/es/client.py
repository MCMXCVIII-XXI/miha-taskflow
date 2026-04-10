"""Provides Elasticsearch connection management and health checking.

This module implements a helper class for managing Elasticsearch connections
with automatic health checking, authentication, and proper resource cleanup.
It ensures reliable connection establishment and validation before use.
"""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from elasticsearch import AsyncElasticsearch

from app.core.config import ElasticsearchSettings, elasticsearch_settings

from .exceptions import es_exc


class ElasticsearchHelper:
    """Manages Elasticsearch connections with health checking and resource management.

    Handles the complete lifecycle of Elasticsearch connections including
    initialization, health validation, authentication, and proper resource disposal.
    Supports various authentication methods and connection configurations.

    Attributes:
        _settings (ElasticsearchSettings): Elasticsearch configuration settings
        _client (AsyncElasticsearch | None): Active Elasticsearch client instance
    """

    def __init__(self, settings: ElasticsearchSettings):
        self._settings = settings
        self._client: AsyncElasticsearch | None = None

    async def _health_check(self) -> None:
        """Validates Elasticsearch connection health.

        Performs a ping operation to verify the Elasticsearch cluster is accessible
        and ready for operations. Raises exceptions if connection is unavailable.

        Raises:
            es_exc.ElasticsearchUnavailableError: When client is not initialized
            es_exc.ElasticsearchConnectionError: When ping operation fails
        """
        if self._client is None:
            raise es_exc.ElasticsearchUnavailableError(
                message="Elasticsearch unavailable"
            )
        elif not await self._client.ping():
            raise es_exc.ElasticsearchConnectionError(
                message="Elasticsearch connection error"
            )

    async def dispose(self) -> None:
        """Closes Elasticsearch client connection and frees resources.

        Properly closes the active Elasticsearch client connection during application
        shutdown to ensure clean resource cleanup and prevent connection leaks.
        """
        if self._client:
            await self._client.close()

    async def _get_client(self) -> AsyncElasticsearch:
        """Gets or creates a validated Elasticsearch client instance.

        Returns an existing healthy client or creates a new one with validation.
        Ensures the client is properly connected and responsive before returning.

        Returns:
            AsyncElasticsearch: Configured and validated Elasticsearch client

        Raises:
            es_exc.ElasticsearchUnavailableError: When connection cannot be established
            es_exc.ElasticsearchConnectionError: When health check fails
        """
        if self._client is None:
            self._client = self._create_client()
            await self._health_check()
        elif not await self._client.ping():
            self._client = self._create_client()
            await self._health_check()
        return self._client

    def _create_client(self) -> AsyncElasticsearch:
        """Creates a new Elasticsearch client with application settings.

        Initializes AsyncElasticsearch client with configured connection parameters
        including URLs, authentication credentials, timeouts, and cluster discovery.

        Returns:
            AsyncElasticsearch: New Elasticsearch client instance

        Note:
            Does not perform health checking - call _health_check() after creation.
        """
        auth_params: dict[str, Any] = {}

        if self._settings.API_KEY:
            auth_params["api_key"] = self._settings.API_KEY.get_secret_value()
        elif self._settings.USERNAME and self._settings.PASSWORD:
            auth_params["basic_auth"] = ":".join(
                [
                    self._settings.USERNAME,
                    self._settings.PASSWORD.get_secret_value(),
                ]
            )

        return AsyncElasticsearch(
            hosts=[str(url) for url in self._settings.URL],
            request_timeout=self._settings.REQUEST_TIMEOUT,
            max_retries=self._settings.MAX_RETRIES,
            retry_on_timeout=self._settings.RETRY_ON_TIMEOUT,
            sniff_on_start=self._settings.SNIFF_ON_START,
            sniff_timeout=self._settings.SNIFFER_TIMEOUT,
            **auth_params,
        )

    async def get_client(self) -> AsyncGenerator[AsyncElasticsearch, None]:
        yield await self._get_client()

    @asynccontextmanager
    async def get_client_ctx(self) -> AsyncIterator[AsyncElasticsearch]:
        client = await self._get_client()
        yield client


es_helper = ElasticsearchHelper(elasticsearch_settings)
