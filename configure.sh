#!/bin/sh
set -e

for envvar_name in CREDITORS_PIN_PROTECTION_SECRET \
                       CREDITORS_LOGIN_COOKIE_SECRET \
                       CREDITORS_LOGIN_SYSTEM_SECRET \
                       DEBTORS_LOGIN_COOKIE_SECRET \
                       DEBTORS_LOGIN_SYSTEM_SECRET \
                       
do
    eval envvar_value=\$$envvar_name
    if [ -z "$envvar_value" ]; then
        echo "Error: The $envvar_name variable is not set."
        exit 1
    fi
done

docker-compose up -d pg
docker-compose up -d rabbitmq
docker-compose up -d redis
echo "Waiting for services to become operational ..."
sleep 30
docker-compose run accounts-server configure
docker-compose run creditors-server configure
docker-compose run creditors-login configure
docker-compose run debtors-server configure
docker-compose run debtors-login configure
docker-compose down
