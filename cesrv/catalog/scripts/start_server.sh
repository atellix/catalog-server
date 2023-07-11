#!/bin/bash

flask --app catalog_server run --host qmkt1.atellix.net --port 9500 --cert=ssl/fullchain.pem --key=ssl/privkey.pem
