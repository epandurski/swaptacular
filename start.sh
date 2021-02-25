#!/bin/sh
set -e
cd "$(dirname $0)"
. ./export-vars.sh

docker-compose up -d
