{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_public_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "internal_id",
            "nullable": false,
            "type": "record"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_public_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "public_id",
            "nullable": false,
            "type": "record"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "public_id"
                },
                {
                    "column": "internal_id"
                }
            ],
            "name": "ix_public_id_1",
            "type": "unique"
        }
    ],
    "table": "category_public_internal"
}