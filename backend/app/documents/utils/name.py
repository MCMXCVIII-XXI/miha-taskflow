from .settings_index import load_index_mappings


def get_index_name(index_key: str) -> str:
    """Get index name by key."""
    prefix = load_index_mappings().get(index_key, {}).get("prefix")
    return f"{prefix}_{index_key}" if prefix else index_key
