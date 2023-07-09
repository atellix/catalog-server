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
            "indexes": [
                "ix_catalog_1"
            ],
            "length": "specify",
            "length_specify": "64",
            "name": "owner",
            "nullable": false,
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "ts_created",
            "nullable": false,
            "type": "datetime"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_uuid_1"
            ],
            "length": "specify",
            "length_specify": "16",
            "name": "uuid",
            "nullable": true,
            "type": "binary"
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
        },
        {
            "columns": [
                {
                    "column": "uuid"
                }
            ],
            "name": "ix_uuid_1",
            "type": "index"
        }
    ],
    "table": "listing_lock"
}