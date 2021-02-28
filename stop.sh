#!/bin/sh
set -e
cd "$(dirname $0)"
. ./export-vars.sh

for filename in $ADDITIONAL_COMPOSE_FILES
do
   ADDITIONAL_OPTIONS="$ADDITIONAL_OPTIONS -f $filename"
done

docker-compose -f docker-compose.yml $ADDITIONAL_OPTIONS down
