{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_entry_id_1",
                "ix_entry_id_2"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "entry_id",
            "nullable": false,
            "type": "record"
        },
        {
            "default": "specify",
            "default_value": "0",
            "length": "default",
            "length_specify": 255,
            "name": "entry_version",
            "nullable": false,
            "type": "integer"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_entry_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "listing_posted_id",
            "nullable": false,
            "type": "record"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "listing_posted_id"
                },
                {
                    "column": "entry_id"
                }
            ],
            "name": "ix_entry_id_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "entry_id"
                }
            ],
            "name": "ix_entry_id_2",
            "type": "index"
        }
    ],
    "table": "entry_listing"
}