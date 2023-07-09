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
            "length": "default",
            "length_specify": 255,
            "name": "record_id",
            "nullable": false,
            "type": "record"
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
            "default": "specify",
            "default_value": "0",
            "length": "default",
            "length_specify": 255,
            "name": "update_count",
            "nullable": false,
            "type": "integer"
        },
        {
            "default": "none",
            "default_value": "",
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
                "ix_catalog_1"
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
            "name": "ix_catalog_1",
            "type": "unique"
        }
    ],
    "table": "listing"
}