{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_backend_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "backend_id",
            "nullable": false,
            "type": "record"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_backend_id_1",
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
                "ix_backend_id_1",
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
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_ts_created_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "ts_created",
            "nullable": false,
            "type": "datetime"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "ts_updated",
            "nullable": false,
            "type": "datetime"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_user_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "user_id",
            "nullable": false,
            "type": "record"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "backend_id"
                },
                {
                    "column": "catalog_id"
                },
                {
                    "column": "category_hash"
                }
            ],
            "name": "ix_backend_id_1",
            "type": "unique"
        },
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
                    "column": "ts_created"
                }
            ],
            "name": "ix_ts_created_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "user_id"
                }
            ],
            "name": "ix_user_id_1",
            "type": "index"
        }
    ],
    "table": "listing_spec"
}