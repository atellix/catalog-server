#!/bin/sh

FLASK_APP=catalog.py flask db migrate -d schema/migrations
