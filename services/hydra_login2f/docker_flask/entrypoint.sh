#!/bin/sh
set -e

logging_conf='/usr/src/app/docker_flask/logging.conf'
gunicorn_conf='/usr/src/app/docker_flask/gunicorn.conf'

export PYTHONDONTWRITEBYTECODE=1
case $1 in
    develop)
        shift;
        export FLASK_ENV=development
        exec flask run --host=0.0.0.0 --port $PORT "$@"
        ;;
    debug)
        shift;
        export FLASK_ENV=development
        exec python -u run.py "$@"
        ;;
    db)
        shift;
        exec flask db "$@"
        ;;
    serve)
        export -n PYTHONDONTWRITEBYTECODE
        exec gunicorn --config "$gunicorn_conf" --log-config "$logging_conf" -b :$PORT run:app
        ;;
    *)
        exec "$@"
        ;;
esac
