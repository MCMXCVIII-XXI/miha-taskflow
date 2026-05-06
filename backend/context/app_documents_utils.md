# app_documents_utils.md

## 1. Purpose of the directory
The `app/documents/utils/` directory contains helper utilities for setting up Elasticsearch index settings and analyzers used when defining document structure.

## 2. Typical contents
- `__init__.py` - Package initialization.
- `analyzer.py` - Text analyzer settings (e.g., for Russian language).
- `settings_index.py` - Loading index mappings from JSON.
- `name.py` - Utilities for generating index names.

## 3. How key modules work
- `RUSSIAN_ANALYZER_SETTINGS` (in `analyzer.py`):
  - Input: None (constant).
  - Output: Dictionary of settings for Elasticsearch.
  - What it does: Defines a custom analyzer with tokenizer, stop-words filter, and stemmer for Russian.
  - How it interacts: Used when creating indices in `app/es/`.

- `load_index_mappings` (in `settings_index.py`):
  - Input: Path to `indices.json` file.
  - Output: Dictionary with mappings.
  - What it does: Reads JSON file with index field settings.
  - How it interacts: Called during ES client or indexer initialization.

## 4. Data flow and integration
1. On startup or reindex, loading of settings is triggered.
2. Utilities assemble the configuration (analyzers + mappings).
3. Configuration is passed to the Elasticsearch client for index creation/update.

## 5. Summary
Utility layer for Elasticsearch responsible for correct search setup and data structure, abstracting configuration details from the main service code.
