#!/usr/bin/env bash
export DS='$'
envsubst < /etc/nginx/conf.d/site.template > /etc/nginx/conf.d/default.conf
nginx -g "daemon off;"

