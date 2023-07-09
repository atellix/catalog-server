{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_type_name_1"
            ],
            "length": "specify",
            "length_specify": "64",
            "name": "type_name",
            "nullable": false,
            "type": "string"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "type_name"
                }
            ],
            "name": "ix_type_name_1",
            "type": "unique"
        }
    ],
    "table": "entry_type"
}