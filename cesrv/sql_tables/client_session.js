{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "length": "long",
            "length_specify": 255,
            "name": "data",
            "nullable": true,
            "type": "binary"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "expiry",
            "nullable": true,
            "type": "datetime"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_session_id_1"
            ],
            "length": "specify",
            "length_specify": 255,
            "name": "session_id",
            "nullable": false,
            "type": "string"
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
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "session_id"
                }
            ],
            "name": "ix_session_id_1",
            "type": "unique"
        },
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
    "table": "client_session"
}