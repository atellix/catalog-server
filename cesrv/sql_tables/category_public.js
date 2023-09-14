{
    "column": [
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
        }
    ],
    "table": "category_public"
}