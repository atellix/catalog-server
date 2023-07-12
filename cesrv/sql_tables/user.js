{
    "column": [
        {
            "default": "specify",
            "default_value": "1",
            "length": "default",
            "length_specify": 255,
            "name": "active",
            "nullable": false,
            "type": "boolean"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "merchant_data",
            "nullable": true,
            "type": "json"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "specify",
            "length_specify": 255,
            "name": "merchant_label",
            "nullable": false,
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_merchant_pk_1"
            ],
            "length": "specify",
            "length_specify": "64",
            "name": "merchant_pk",
            "nullable": true,
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_merchant_uri_1"
            ],
            "length": "specify",
            "length_specify": "128",
            "name": "merchant_uri",
            "nullable": true,
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
                    "column": "merchant_pk"
                }
            ],
            "name": "ix_merchant_pk_1",
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
        },
        {
            "columns": [
                {
                    "column": "merchant_uri"
                }
            ],
            "name": "ix_merchant_uri_1",
            "type": "unique"
        }
    ],
    "table": "user"
}