{
    "column": [
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "attributes",
            "nullable": true,
            "type": "json"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_catalog_id_1",
                "ix_catalog_id_2"
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
                "ix_category_hash_1"
            ],
            "length": "specify",
            "length_specify": "16",
            "name": "category_hash",
            "nullable": "",
            "type": "binary"
        },
        {
            "default": "specify",
            "default_value": "0",
            "length": "default",
            "length_specify": 255,
            "name": "deleted",
            "nullable": false,
            "type": "boolean"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "deleted_ts",
            "nullable": true,
            "type": "datetime"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "detail",
            "nullable": true,
            "type": "json"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_filter_by_1_1"
            ],
            "length": "specify",
            "length_specify": "16",
            "name": "filter_by_1",
            "nullable": true,
            "type": "binary"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_filter_by_2_1"
            ],
            "length": "specify",
            "length_specify": "16",
            "name": "filter_by_2",
            "nullable": true,
            "type": "binary"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_filter_by_3_1"
            ],
            "length": "specify",
            "length_specify": "16",
            "name": "filter_by_3",
            "nullable": true,
            "type": "binary"
        },
        {
            "default": "specify",
            "default_value": "1",
            "length": "default",
            "length_specify": 255,
            "name": "internal",
            "nullable": false,
            "type": "boolean"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "specify",
            "length_specify": "255",
            "name": "label",
            "nullable": "",
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_latitude_1"
            ],
            "length": "specify",
            "length_specify": "32",
            "name": "latitude",
            "nullable": true,
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_listing_account_1"
            ],
            "length": "specify",
            "length_specify": "64",
            "name": "listing_account",
            "nullable": false,
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "long",
            "length_specify": 255,
            "name": "listing_data",
            "nullable": true,
            "type": "json"
        },
        {
            "default": "specify",
            "default_value": "0",
            "indexes": [
                "ix_catalog_id_2"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "listing_idx",
            "nullable": false,
            "type": "integer"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_longitude_1"
            ],
            "length": "specify",
            "length_specify": "32",
            "name": "longitude",
            "nullable": true,
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_owner_1"
            ],
            "length": "specify",
            "length_specify": "64",
            "name": "owner",
            "nullable": false,
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "update_count",
            "nullable": true,
            "type": "integer"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_update_ts_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "update_ts",
            "nullable": false,
            "type": "datetime"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_user_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "user_id",
            "nullable": true,
            "type": "record"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_catalog_id_1",
                "ix_uuid_1"
            ],
            "length": "specify",
            "length_specify": "16",
            "name": "uuid",
            "nullable": false,
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
                    "column": "uuid"
                }
            ],
            "name": "ix_catalog_id_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "catalog_id"
                },
                {
                    "column": "listing_idx"
                }
            ],
            "name": "ix_catalog_id_2",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "category_hash"
                }
            ],
            "name": "ix_category_hash_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "filter_by_1"
                }
            ],
            "name": "ix_filter_by_1_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "filter_by_2"
                }
            ],
            "name": "ix_filter_by_2_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "filter_by_3"
                }
            ],
            "name": "ix_filter_by_3_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "latitude"
                }
            ],
            "name": "ix_latitude_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "listing_account"
                }
            ],
            "name": "ix_listing_account_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "longitude"
                }
            ],
            "name": "ix_longitude_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "owner"
                }
            ],
            "name": "ix_owner_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "update_ts"
                }
            ],
            "name": "ix_update_ts_1",
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
    "table": "listing_posted"
}