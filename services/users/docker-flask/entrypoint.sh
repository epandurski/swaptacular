#!/bin/sh
#
# This file is used by "Dockerfile-flask".

logging_conf='/logging.conf'
gunicorn_conf='/gunicorn.conf'
alembic_conf='migrations/alembic.ini'


# This function should be called with a message and a filename. It
# logs the message and the contents of the file as a JSON-formated
# message.
py_log_error() {
    python - <<EOF
import logging
import logging.config
logging.config.fileConfig('$logging_conf')
logger = logging.getLogger('alembic.runtime.migration')
logger.error('$1', extra={'info': open('$2').read()})
EOF
}


# This function should be called with the filename of the respective
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
logger = logging.getLogger('alembic')
config = configparser.ConfigParser()
try:
    with open(FILE_NAME) as configfile:
        config.read_file(configfile)
except FileNotFoundError:
    logger.error('set_json_log_handler: config file not found (%s).', FILE_NAME)
    sys.exit(1)
try:
    handlers_keys = config['handlers']['keys']
except KeyError:
    handlers_keys = 'None'
if  handlers_keys != 'console':
    logger.error('set_json_log_handler: wrong logging handlers keys (%s).', handlers_keys)
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
    local error_file='/perform-db-connect.error'
    while [[ $retry_after -lt ${DB_CONNECT_QUIT_DELAY-8} ]]; do
        flask db current &>$error_file
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
    py_log_error "perform_db_connect: can not connect to the database." $error_file
    return 1
}


# This function tries to perform alembic database schema upgrade.
perform_db_upgrade() {
    perform_db_connect
    case $? in
        0)
            # The database is up and running, so we try to upgrade.
            local error_file='/perform-db-upgrade.error'
            if !flask db upgrade 2>$error_file; then
                py_log_error "perform_db_upgrade: can not upgrade the schema." $error_file
                return 1
            fi
            ;;
        2)
            # `flask-migrate` is not installed, so upgrade is not needed.
            ;;
        *)
            return 1
            ;;
    esac
    return 0
}


set +e
export PYTHONDONTWRITEBYTECODE=1
case $1 in
    develop)
        shift;
        export FLASK_ENV=development
        flask run --host=0.0.0.0 --port $PORT "$@"
        ;;
    debug)
        shift;
        export FLASK_ENV=development
        python -u run.py "$@"
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
                -b :$PORT $FLASK_APP:app
        ;;
    *)
        "$@"
        ;;
esac
