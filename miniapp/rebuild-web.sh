#!/usr/bin/env bash
set -euo pipefail

docker-compose build --no-cache web
docker-compose stop web
docker-compose rm -f web
docker-compose up -d web
