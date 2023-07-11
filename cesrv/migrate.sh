#!/bin/sh

PYTHONPATH=. FLASK_APP=app flask db migrate -d schema/migrations
