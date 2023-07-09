{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_catalog_name_1"
            ],
            "length": "specify",
            "length_specify": "32",
            "name": "catalog_name",
            "nullable": false,
            "type": "string"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "catalog_name"
                }
            ],
            "name": "ix_catalog_name_1",
            "type": "unique"
        }
    ],
    "table": "listing_catalog"
}