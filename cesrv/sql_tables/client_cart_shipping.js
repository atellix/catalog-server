{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_cart_backend_1"
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
                "ix_cart_backend_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "cart_id",
            "nullable": false,
            "type": "record"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "shipping_price",
            "nullable": false,
            "type": "currency"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "shipping_tax",
            "nullable": false,
            "type": "currency"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "cart_id"
                },
                {
                    "column": "backend_id"
                }
            ],
            "name": "ix_cart_backend_1",
            "type": "unique"
        }
    ],
    "table": "client_cart_shipping"
}