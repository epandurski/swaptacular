#!/bin/sh
set -e
if [ -z "$1" ]; then
    echo "Usage: add-debtors-client.sh FILE"
    echo
    echo "Creates a new OAuth2 debtors client from a JSON description file."
    exit 2
fi

cleanup() {
    rm "$filepath"
}

filepath=$(mktemp --tmpdir="$(pwd)")
trap cleanup EXIT INT TERM

chmod a+r "$filepath"
envsubst '$PUBLIC_HOST $DEBTORS_SUPERVISOR_CLIENT_SECRET' < "$1" > "$filepath"
cd "$(dirname $0)"
. ./export-vars.sh
echo "Creating an Oauth2 debtors client from $1 ..."
docker-compose run --volume="$filepath:/client.json" debtors-login hydra clients import /client.json --fake-tls-termination
