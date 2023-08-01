{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "backend_data",
            "nullable": false,
            "type": "json"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_backend_id_1",
                "ix_cart_id_1"
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
                "ix_cart_id_1"
            ],
            "length": "specify",
            "length_specify": 255,
            "name": "cart_id",
            "nullable": false,
            "type": "record"
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
            "name": "ix_cart_id_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "backend_id"
                }
            ],
            "name": "ix_backend_id_1",
            "type": "index"
        }
    ],
    "table": "client_cart_backend"
}