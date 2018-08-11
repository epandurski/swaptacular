#!/bin/sh
#
# This file is used by "Dockerfile-flask".

export PYTHONDONTWRITEBYTECODE=1

case $1 in
    develop)
        shift;
        export FLASK_ENV=development
        exec flask run --host=0.0.0.0 --port 80 "$@"
        ;;
    debug)
        shift;
        export FLASK_ENV=development
        exec python -m pudb wsgi.py "$@"
        ;;
    db)
        shift;
        exec flask db "$@"
        ;;
    '')
        export -n PYTHONDONTWRITEBYTECODE
        exec gunicorn --config /gunicorn.conf --log-config /logging.conf -b :80 wsgi:app
        ;;
    *)
        exec "$@"
        ;;
esac
