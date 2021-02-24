#!/bin/sh
set -e
. ./export_vars.sh

if [ -z "$1" ]; then
    echo "Usage: add-debtors-client.sh FILE"
    echo
    echo "Creates a new OAuth2 debtors client from a JSON description file."
    exit 2
fi

filepath="$(cd "$(dirname "$1")"; pwd)/$(basename "$1")"
docker-compose run --volume="$filepath:/client.json" debtors-login hydra clients import /client.json --fake-tls-termination
