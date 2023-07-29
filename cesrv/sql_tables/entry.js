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
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "data",
            "nullable": true,
            "type": "json"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "specify",
            "length_specify": "32",
            "name": "data_hash",
            "nullable": true,
            "type": "binary"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "data_index",
            "nullable": true,
            "type": "json"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "data_summary",
            "nullable": true,
            "type": "json"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_entry_key_1"
            ],
            "length": "specify",
            "length_specify": "10",
            "name": "entry_key",
            "nullable": true,
            "type": "binary"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_backend_id_1",
                "ix_user_id_1"
            ],
            "length": "specify",
            "length_specify": "64",
            "name": "external_id",
            "nullable": true,
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_external_uri_1"
            ],
            "length": "specify",
            "length_specify": "128",
            "name": "external_uri",
            "nullable": false,
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "specify",
            "length_specify": "64",
            "name": "slug",
            "nullable": true,
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_ts_created_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "ts_created",
            "nullable": true,
            "type": "datetime"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_ts_updated_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "ts_updated",
            "nullable": true,
            "type": "datetime"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_type_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "type_id",
            "nullable": false,
            "type": "record"
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
                    "column": "backend_id"
                },
                {
                    "column": "external_id"
                }
            ],
            "name": "ix_backend_id_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "entry_key"
                }
            ],
            "name": "ix_entry_key_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "external_uri"
                }
            ],
            "name": "ix_external_uri_1",
            "type": "unique"
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
                    "column": "ts_updated"
                }
            ],
            "name": "ix_ts_updated_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "type_id"
                }
            ],
            "name": "ix_type_id_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "user_id"
                },
                {
                    "column": "external_id"
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
            "type": "unique"
        }
    ],
    "table": "entry"
}