#!/bin/sh
set -e
. ./export_vars.sh

filepath="$(cd "$(dirname "$1")"; pwd)/$(basename "$1")"
docker-compose run --volume="$filepath:/client.json" creditors-login hydra clients import /client.json --fake-tls-termination
