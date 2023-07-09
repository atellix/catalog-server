{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "length": "specify",
            "length_specify": "32",
            "name": "backend_name",
            "nullable": false,
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "config_data",
            "nullable": false,
            "type": "json"
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
                    "column": "user_id"
                }
            ],
            "name": "ix_user_id_1",
            "type": "index"
        }
    ],
    "table": "user_backend"
}