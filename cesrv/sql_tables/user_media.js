{
    "column": [
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_cloud_path_1"
            ],
            "length": "specify",
            "length_specify": 255,
            "name": "cloud_path",
            "nullable": false,
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "0",
            "length": "default",
            "length_specify": 255,
            "name": "deleted",
            "nullable": false,
            "type": "boolean"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_media_cksum_1"
            ],
            "length": "specify",
            "length_specify": "128",
            "name": "media_cksum",
            "nullable": false,
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_media_url_1",
                "ix_user_id_1"
            ],
            "length": "specify",
            "length_specify": 255,
            "name": "media_url",
            "nullable": "",
            "type": "string"
        },
        {
            "default": "none",
            "default_value": "",
            "length": "specify",
            "length_specify": "10",
            "name": "public_key",
            "nullable": "",
            "type": "binary"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_ts_created_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "ts_created",
            "nullable": false,
            "type": "datetime"
        },
        {
            "default": "null",
            "default_value": "",
            "indexes": [
                "ix_ts_deleted_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "ts_deleted",
            "nullable": true,
            "type": "datetime"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_ts_updated_1"
            ],
            "length": "default",
            "length_specify": 255,
            "name": "ts_updated",
            "nullable": false,
            "type": "datetime"
        },
        {
            "default": "none",
            "default_value": "",
            "indexes": [
                "ix_user_id_1"
            ],
            "length": "long",
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
                    "column": "cloud_path"
                }
            ],
            "name": "ix_cloud_path_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "media_cksum"
                }
            ],
            "name": "ix_media_cksum_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "media_url"
                }
            ],
            "name": "ix_media_url_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "public_key"
                }
            ],
            "name": "ix_public_key_1",
            "type": "unique"
        },
        {
            "columns": [
                {
                    "column": "ts_created"
                }
            ],
            "name": "ix_ts_created_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "ts_deleted"
                }
            ],
            "name": "ix_ts_deleted_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "ts_updated"
                }
            ],
            "name": "ix_ts_updated_1",
            "type": "index"
        },
        {
            "columns": [
                {
                    "column": "user_id"
                },
                {
                    "column": "media_url"
                }
            ],
            "name": "ix_user_id_1",
            "type": "unique"
        }
    ],
    "table": "user_media"
}