{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "length": "specify",
            "length_specify": "32",
            "name": "cart_currency",
            "nullable": false,
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "cart_data",
            "nullable": false,
            "type": "json"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "cart_shipping",
            "nullable": true,
            "type": "currency"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "cart_subtotal",
            "nullable": false,
            "type": "currency"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "cart_tax",
            "nullable": false,
            "type": "currency"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "cart_total",
            "nullable": false,
            "type": "currency"
        },
        {
            "default": "specify",
            "default_value": "0",
            "length": "default",
            "length_specify": 255,
            "name": "checkout_cancel",
            "nullable": false,
            "type": "boolean"
        },
        {
            "default": "specify",
            "default_value": "0",
            "length": "default",
            "length_specify": 255,
            "name": "checkout_complete",
            "nullable": false,
            "type": "boolean"
        },
        {
            "default": "specify",
            "default_value": "0",
            "length": "default",
            "length_specify": 255,
            "name": "checkout_prepared",
            "nullable": false,
            "type": "boolean"
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
            "indexes": [
                "ix_ts_updated_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "ts_updated",
            "nullable": false,
            "type": "datetime"
        }
    ],
    "index": [
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
        }
    ],
    "table": "client_cart"
}