#!/bin/sh
set -e
. ./export_vars.sh

for envvar_name in CREDITORS_PIN_PROTECTION_SECRET \
                       CREDITORS_SUPERVISOR_CLIENT_SECRET \
                       CREDITORS_LOGIN_COOKIE_SECRET \
                       CREDITORS_LOGIN_SYSTEM_SECRET \
                       DEBTORS_SUPERVISOR_CLIENT_SECRET \
                       DEBTORS_LOGIN_COOKIE_SECRET \
                       DEBTORS_LOGIN_SYSTEM_SECRET \
                       RECAPTCHA_PUBLIC_KEY \
                       RECAPTCHA_PIVATE_KEY \
                       PUBLIC_HOST \
                       PUBLIC_PORT
do
    eval envvar_value=\$$envvar_name
    if [ -z "$envvar_value" ]; then
        echo "Error: The $envvar_name variable is not set."
        exit 1
    fi
done

cleanup() {
    docker-compose down
}

trap cleanup EXIT INT
docker-compose up -d pg
docker-compose up -d rabbitmq
docker-compose up -d redis
echo -n "Waiting for services to become operational ..."; sleep 30; echo " done."

docker-compose run accounts-server configure
docker-compose run creditors-server configure
docker-compose run creditors-login configure
docker-compose run debtors-server configure
docker-compose run debtors-login configure
docker-compose up -d creditors-login
docker-compose up -d debtors-login
echo -n "Waiting for services to become operational ..."; sleep 30; echo " done."

./add-creditors-client.sh oauth2-clients/creditors-swagger-ui.json || true
./add-creditors-client.sh oauth2-clients/creditors-supervisor.json || true
./add-debtors-client.sh oauth2-clients/debtors-swagger-ui.json || true
./add-debtors-client.sh oauth2-clients/debtors-supervisor.json || true
