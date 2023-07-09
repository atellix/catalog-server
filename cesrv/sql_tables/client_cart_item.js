{
    "column": [
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "backend_data",
            "nullable": true,
            "type": "json"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_backend_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "backend_id",
            "nullable": true,
            "type": "record"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_cart_id_1",
                "ix_entry_key_index_cart"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "cart_id",
            "nullable": false,
            "type": "record"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_entry_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "entry_id",
            "nullable": true,
            "type": "record"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_entry_key_index_cart"
            ],
            "length": "specify",
            "length_specify": "10",
            "name": "entry_key",
            "nullable": false,
            "type": "binary"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "specify",
            "length_specify": 255,
            "name": "image_url",
            "nullable": true,
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "specify",
            "length_specify": 255,
            "name": "label",
            "nullable": true,
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "net_tax",
            "nullable": true,
            "type": "currency"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "option_data",
            "nullable": true,
            "type": "json"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "price",
            "nullable": true,
            "type": "currency"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_entry_key_index_cart"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "product_index",
            "nullable": false,
            "type": "integer"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "quantity",
            "nullable": true,
            "type": "currency"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "backend_id"
                }
            ],
            "name": "ix_backend_id_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "cart_id"
                }
            ],
            "name": "ix_cart_id_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "entry_key"
                },
                {
                    "column": "product_index"
                },
                {
                    "column": "cart_id"
                }
            ],
            "name": "ix_entry_key_index_cart",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "entry_id"
                }
            ],
            "name": "ix_entry_id_1",
            "type": "index"
        }
    ],
    "table": "client_cart_item"
}