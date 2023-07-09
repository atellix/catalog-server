{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "event_name",
            "nullable": false,
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_ip_address_1"
            ],
            "length": "specify",
            "length_specify": "45",
            "name": "ip_address",
            "nullable": true,
            "type": "string"
        },
        {
            "default": "specify",
            "default_value": "0",
            "length": "default",
            "length_specify": 255,
            "name": "ip_address_ipv6",
            "nullable": false,
            "type": "boolean"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_note_session_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "note_session_id",
            "nullable": false,
            "type": "record"
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
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_ts_log_1",
                "ix_user_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "ts_log",
            "nullable": false,
            "type": "datetime"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "user_agent",
            "nullable": true,
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
                    "column": "ip_address"
                }
            ],
            "name": "ix_ip_address_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "note_session_id"
                }
            ],
            "name": "ix_note_session_id_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "session_id"
                }
            ],
            "name": "ix_session_id_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "ts_log"
                }
            ],
            "name": "ix_ts_log_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "user_id"
                },
                {
                    "column": "ts_log"
                }
            ],
            "name": "ix_user_id_1",
            "type": "index"
        }
    ],
    "table": "client_session_log"
}