import json
import os
from typing import Any

from app.es.exceptions import es_exc


def load_index_mappings() -> dict[str, dict[str, Any]]:
    """Load index mappings from JSON file."""
    json_path = os.path.join(os.path.dirname(__file__), "../indices.json")
    if not os.path.exists(json_path):
        raise es_exc.ElasticsearchSettingsNotFoundError(
            message=f"Index mappings file not found: {json_path}"
        )

    with open(json_path, encoding="utf-8") as f:
        return json.load(f)
