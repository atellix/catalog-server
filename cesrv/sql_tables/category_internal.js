{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_internal_uri_1"
            ],
            "length": "specify",
            "length_specify": "128",
            "name": "internal_uri",
            "nullable": false,
            "type": "string"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "internal_uri"
                }
            ],
            "name": "ix_internal_uri_1",
            "type": "unique"
        }
    ],
    "table": "category_internal"
}