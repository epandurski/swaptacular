#!/bin/sh
#
# This file is used by "Dockerfile-flask".

logging_conf='/logging.conf'
gunicorn_conf='/gunicorn.conf'
alembic_conf='migrations/alembic.ini'


# This function should be called with a file name. It logs the
# contents of the file as a JSON-formated message.
py_log_error() {
    python - <<EOF
import logging
import logging.config
logging.config.fileConfig('$logging_conf')
logging.error(open('$1').read())
EOF
}


# This function should be called with the file name of the respective
# alembic configuration file. It modifies the file, so that alembic
# will use JSON formatter for its logging messages. The function
# returns `0` or `1`.
set_json_log_handler() {
    python - <<EOF
import sys
import logging
import logging.config
import configparser
FILE_NAME = '$1'
logging.config.fileConfig('$logging_conf')
config = configparser.ConfigParser()
try:
    with open(FILE_NAME) as configfile:
        config.read_file(configfile)
except FileNotFoundError:
    logging.error('set_json_log_handler: config file not found (%s).',
                  FILE_NAME)
    sys.exit(1)
try:
    handlers_keys = config['handlers']['keys']
except KeyError:
    handlers_keys = 'None'
if  handlers_keys != 'console':
    logging.error('set_json_log_handler: wrong logging handler keys (%s).',
                  handlers_keys)
    sys.exit(1)
config['formatter_json'] = { 'class': 'jsonlogging.JSONFormatter' }
formatters = config.setdefault('formatters', {})
formatters_keys = [k.strip() for k in formatters.get('keys', '').split(',')]
if 'json' not in formatters_keys:
    formatters_keys.append('json')
    formatters['keys'] = ','.join(formatters_keys)
handler_console = config.setdefault('handler_console', {})
handler_console.update({
    'class': 'StreamHandler',
    'args': '(sys.stdout,)',
    'formatter': 'json',
})
with open(FILE_NAME, 'w') as configfile:
    config.write(configfile)
EOF
}


# This function tries to connect to the database, retrying if
# necessary for around a minute. It returns `0` if the connection is
# successful, `1` if the connection has failed, and `2` if
# `flask-migrate` is not installed.
perform_db_connect() {
    local retry_after=1
    while [[ $retry_after -lt ${DB_CONNECT_QUIT_DELAY-8} ]]; do
        flask db current &>/dev/null
        case $? in
            0)
                set_json_log_handler "$alembic_conf"
                return $?
                ;;
            1)
                sleep $retry_after
                retry_after=$((2 * retry_after))
                ;;
            2)
                return 2;
                ;;
            *)
                break
                ;;
        esac
    done
    local error_file='/db-connect.error'
    echo -n "perform_db_connect: can not connect to the database." >$error_file
    py_log_error $error_file
    return 1
}


# This function tries to perform alembic database schema upgrade.
perform_db_upgrade() {
    perform_db_connect
    case $? in
        0)
            # The database is up and running, so we try to upgrade.
            local error_file='/db-upgrade.error'
            flask db upgrade 2>$error_file
            local error_code=$?
            [[ -s $error_file ]] && py_log_error $error_file
            return $error_code
            ;;
        2)
            # `flask-migrate` is not installed, so upgrade is not needed.
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}


set +e
export PYTHONDONTWRITEBYTECODE=1
case $1 in
    develop)
        shift;
        export FLASK_ENV=development
        flask run --host=0.0.0.0 --port 80 "$@"
        ;;
    debug)
        shift;
        export FLASK_ENV=development
        python -m pudb wsgi.py "$@"
        ;;
    db)
        shift;
        flask db "$@"
        ;;
    perform-db-upgrade)
        perform_db_upgrade
        ;;
    '')
        export -n PYTHONDONTWRITEBYTECODE
        ([[ $DO_NOT_UPGRADE_DB ]] || perform_db_upgrade) && gunicorn \
                --config "$gunicorn_conf" \
                --log-config "$logging_conf" \
                -b :80 wsgi:app
        ;;
    *)
        "$@"
        ;;
esac
