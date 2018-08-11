#!/bin/sh
#
# This file is used by "Dockerfile-flask".

logging_conf='/logging.conf'
gunicorn_conf='/gunicorn.conf'

py_log_error() {
    python - <<EOF
import logging
import logging.config
logging.config.fileConfig('$logging_conf')
logging.error(open('$1').read())
EOF
}

flask_db_upgrade() {
    error_file='/flask-db-upgrade.error'
    n_errors_to_ignore=6
    retry_after=1
    threshold=$((1 << n_errors_to_ignore))
    echo -n "Running flask db upgrade ... "
    while true; do
        set +e
        flask db upgrade 2>$error_file
        error_code=$?
        set -e
        case $error_code in
            0)
                echo "ok"
                return 0
                ;;
            1)
                [[ $retry_after -eq $threshold ]] && echo "retrying"
                [[ $retry_after -ge $threshold ]] && py_log_error "$error_file"
                sleep $retry_after
                retry_after=$((2 * retry_after))
                ;;
            2)
                echo "not installed"
                return 0
                ;;
            *)
                echo "error"
                return $error_code
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
        gunicorn --config "$gunicorn_conf" \
                 --log-config "$logging_conf" \
                 -b :80 wsgi:app
        ;;
    *)
        "$@"
        ;;
esac
