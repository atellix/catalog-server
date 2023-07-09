{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_catalog_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "catalog_id",
            "nullable": false,
            "type": "record"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_catalog_1"
            ],
            "length": "specify",
            "length_specify": "16",
            "name": "category_hash",
            "nullable": false,
            "type": "binary"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "listing_data",
            "nullable": false,
            "type": "json"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_catalog_1"
            ],
            "length": "specify",
            "length_specify": "64",
            "name": "owner",
            "nullable": false,
            "type": "string"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "catalog_id"
                },
                {
                    "column": "owner"
                },
                {
                    "column": "category_hash"
                }
            ],
            "name": "ix_catalog_1",
            "type": "index"
        }
    ],
    "table": "listing_spec"
}