{
    "column": [
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_parent_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "parent_id",
            "nullable": true,
            "type": "record"
        },
        {
            "default": "null",
            "default_value": "",
            "length": "default",
            "length_specify": 255,
            "name": "path",
            "nullable": true,
            "type": "json"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "specify",
            "length_specify": "255",
            "name": "public_uri",
            "nullable": "",
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "specify",
            "length_specify": "255",
            "name": "slug",
            "nullable": "",
            "type": "string"
        }
    ],
    "index": [
        {
            "columns": [
                {
                    "column": "public_uri"
                }
            ],
            "name": "ix_public_uri_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "slug"
                }
            ],
            "name": "ix_slug_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "parent_id"
                }
            ],
            "name": "ix_parent_id_1",
            "type": "index"
        }
    ],
    "table": "category_public"
}