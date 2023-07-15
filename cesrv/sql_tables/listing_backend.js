{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_backend_id_1",
                "ix_uuid_1"
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
                    "column": "uuid"
                },
                {
                    "column": "backend_id"
                }
            ],
            "name": "ix_uuid_1",
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
    "table": "listing_backend"
}