{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "data",
            "nullable": false,
            "type": "json"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_data_hash_1"
            ],
            "length": "specify",
            "length_specify": "32",
            "name": "data_hash",
            "nullable": true,
            "type": "binary"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "data_summary",
            "nullable": true,
            "type": "json"
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
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_user_id_1"
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
                    "column": "user_id"
                },
                {
                    "column": "uuid"
                }
            ],
            "name": "ix_user_id_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "data_hash"
                }
            ],
            "name": "ix_data_hash_1",
            "type": "index"
        }
    ],
    "table": "record"
}