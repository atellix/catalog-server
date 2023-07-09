{
    "column": [
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_public_id_brand_1"
            ],
            "length": "specify",
            "length_specify": "64",
            "name": "brand",
            "nullable": true,
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_entry_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "entry_id",
            "nullable": false,
            "type": "record"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_public_id_name_1",
                "ix_public_id_user_id_1"
            ],
            "length": "specify",
            "length_specify": "64",
            "name": "name",
            "nullable": true,
            "type": "string"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_public_id_price_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "price",
            "nullable": true,
            "type": "currency"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_entry_id_1",
                "ix_public_id_brand_1",
                "ix_public_id_name_1",
                "ix_public_id_price_1",
                "ix_public_id_user_id_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "public_id",
            "nullable": false,
            "type": "record"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_public_id_user_id_1"
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
                    "column": "entry_id"
                },
                {
                    "column": "public_id"
                }
            ],
            "name": "ix_entry_id_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "public_id"
                },
                {
                    "column": "brand"
                }
            ],
            "name": "ix_public_id_brand_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "public_id"
                },
                {
                    "column": "name"
                }
            ],
            "name": "ix_public_id_name_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "public_id"
                },
                {
                    "column": "user_id"
                },
                {
                    "column": "name"
                }
            ],
            "name": "ix_public_id_user_id_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "public_id"
                },
                {
                    "column": "price"
                }
            ],
            "name": "ix_public_id_price_1",
            "type": "index"
        }
    ],
    "table": "entry_category"
}