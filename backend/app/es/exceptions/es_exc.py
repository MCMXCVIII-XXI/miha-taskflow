from typing import Any

from fastapi import status


class BaseElasticsearchError(Exception):
    """Custom exception for Elasticsearch errors."""

    def __init__(
        self,
        code: int,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.headers = headers
        self.details = details

    def __str__(self) -> str:
        return self.message


class ElasticsearchSettingsNotFoundError(BaseElasticsearchError):
    """Elasticsearch settings not found."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchInvalidSettingsError(BaseElasticsearchError):
    """Invalid Elasticsearch settings."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchConnectionError(BaseElasticsearchError):
    """Cannot connect to Elasticsearch cluster."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchUnavailableError(BaseElasticsearchError):
    """Elasticsearch cluster is unavailable."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchIndexNotFoundError(BaseElasticsearchError):
    """Elasticsearch index not found."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_404_NOT_FOUND,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchIndexExistsError(BaseElasticsearchError):
    """Elasticsearch index already exists."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_409_CONFLICT,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchIndexCreationError(BaseElasticsearchError):
    """Elasticsearch index creation failed."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchDocumentNotFoundError(BaseElasticsearchError):
    """Elasticsearch document not found."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_404_NOT_FOUND,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchDocumentConflictError(BaseElasticsearchError):
    """Elasticsearch document conflict."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_409_CONFLICT,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchSearchError(BaseElasticsearchError):
    """Elasticsearch search error."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchNoResultsError(BaseElasticsearchError):
    """Elasticsearch no results error."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_404_NOT_FOUND,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchBulkError(BaseElasticsearchError):
    """Elasticsearch bulk error."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchMappingError(BaseElasticsearchError):
    """Elasticsearch mapping error."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            headers=headers,
            details=details,
        )


class ElasticsearchBadRequestError(BaseElasticsearchError):
    """Elasticsearch bad request error."""

    def __init__(
        self,
        message: str,
        headers: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=status.HTTP_400_BAD_REQUEST,
            message=message,
            headers=headers,
            details=details,
        )
