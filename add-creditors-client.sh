#!/bin/sh
set -e
. ./export_vars.sh

if [ -z "$1" ]; then
    echo "Usage: add-creditors-client.sh FILE"
    echo
    echo "Creates a new OAuth2 creditors client from a JSON description file."
    exit 2
fi

cleanup() {
    rm "$filepath"
}

filepath=$(mktemp --tmpdir="$(pwd)")
trap cleanup EXIT INT

chmod a+r "$filepath"
envsubst '$PUBLIC_HOST $CREDITORS_SUPERVISOR_CLIENT_SECRET' < "$1" > "$filepath"
echo "Creating an Oauth2 creditors client from $1 ..."
docker-compose run --volume="$filepath:/client.json" creditors-login hydra clients import /client.json --fake-tls-termination
