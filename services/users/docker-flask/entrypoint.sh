#!/bin/sh
#
# This file is used by "Dockerfile-flask".

LOGGING_CONF='/logging.conf'
GUNICORN_CONF='/gunicorn.conf'

py_log_error() {
    python - <<EOF
import logging
import logging.config
logging.config.fileConfig('$LOGGING_CONF')
logging.error(open('$1').read())
EOF
}

flask_db_upgrade() {
    N_ERRORS_TO_IGNORE=6
    RETRY_AFTER=1
    ERROR_FILE='/flask-db-upgrade.error'
    echo -n "Running flask db upgrade ... "
    while true; do
        set +e
        flask db upgrade 2>$ERROR_FILE
        ERROR_CODE=$?
        set -e
        case $ERROR_CODE in
            0)
                echo "ok"
                return 0
                ;;
            1)
                TIME_LIMIT=$((1 << N_ERRORS_TO_IGNORE))
                [[ $RETRY_AFTER -eq $TIME_LIMIT ]] && echo "retrying"
                [[ $RETRY_AFTER -ge $TIME_LIMIT ]] && py_log_error "$ERROR_FILE"
                sleep $RETRY_AFTER
                RETRY_AFTER=$((2 * RETRY_AFTER))
                ;;
            2)
                echo "not installed"
                return 0
                ;;
            *)
                echo "error"
                return $ERROR_CODE
                ;;
        esac
    done
}

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
    '')
        export -n PYTHONDONTWRITEBYTECODE
        flask_db_upgrade
        gunicorn --config "$GUNICORN_CONF" \
                 --log-config "$LOGGING_CONF" \
                 -b :80 wsgi:app
        ;;
    *)
        "$@"
        ;;
esac
