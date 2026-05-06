# app_es_exceptions.md

## 1. Purpose of the directory
The `app/es/exceptions/` directory contains a hierarchy of exceptions for working with Elasticsearch, covering scenarios from connection errors to document indexing conflicts.

## 2. Typical contents
- `es_exc.py` - Base class and multiple specific Elasticsearch exceptions.

## 3. How key modules work
- `BaseElasticsearchError`:
  - Input: Message, HTTP code, details.
  - Output: Exception object.
  - What it does: Base class for all ES errors.
  - How it interacts: Handled in API layer or services.

- Specific errors:
  - `ElasticsearchConnectionError` (503): No cluster connection.
  - `ElasticsearchIndexNotFoundError` (404): Index not found.
  - `ElasticsearchDocumentNotFoundError` (404): Document not found.
  - `ElasticsearchDocumentConflictError` (409): Version conflict on write.
  - `ElasticsearchSearchError` (500): Search query execution error.
  - `ElasticsearchBulkError` (500): Bulk processing error.

## 4. Data flow and integration
1. The Elasticsearch client (from `app/es/client.py`) returns an error.
2. Code in `app/es/` or services converts it to one of `BaseElasticsearchError`.
3. The exception is raised and may be caught by a FastAPI handler.

## 5. Summary
Complete set of Elasticsearch exceptions allowing services to correctly react to search engine failures and return understandable error statuses to the client.
