{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "length": "specify",
            "length_specify": "255",
            "name": "uri",
            "nullable": "",
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_uri_hash_1"
            ],
            "length": "specify",
            "length_specify": "16",
            "name": "uri_hash",
            "nullable": "",
            "type": "binary"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "uri"
                }
            ],
            "name": "ix_uri_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "uri_hash"
                }
            ],
            "name": "ix_uri_hash_1",
            "type": "unique"
        }
    ],
    "table": "uri"
}