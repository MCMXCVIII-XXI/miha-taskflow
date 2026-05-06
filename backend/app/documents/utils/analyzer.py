RUSSIAN_ANALYZER_SETTINGS = {
    "analysis": {
        "analyzer": {
            "notification_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "russian_stop", "russian_stemmer"],
            }
        },
        "filter": {
            "russian_stop": {"type": "stop", "stopwords": "_russian_"},
            "russian_stemmer": {"type": "stemmer", "language": "russian"},
        },
    }
}
