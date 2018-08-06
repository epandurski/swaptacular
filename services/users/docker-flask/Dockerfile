FROM python:3.5.3-alpine
WORKDIR /usr/src/app
EXPOSE 80

# add files and install requirements
COPY Pipfile* ./
COPY docker-flask/gunicorn.conf /gunicorn.conf
COPY docker-flask/logging.conf /logging.conf
COPY docker-flask/entrypoint.sh /usr/local/bin/
RUN pip install pipenv gunicorn json-logging-py pudb
RUN pipenv install --system

# configure pudb not to show a welcome screen
RUN sed 's/seen_welcome = a/seen_welcome = e034/g' ~/.config/pudb/pudb.cfg -i

# add the app
COPY src ./

ENTRYPOINT ["entrypoint.sh"]

################################################################################

# Set this to the desired granularity of log outputs. Valid level
# names are: debug, info, warning, error, critical
ENV GUNICORN_LOGLEVEL=warning

# Set this to the type of workers to use with gunicorn.
ENV GUNICORN_WORKER_CLASS=sync

# Set this to the number of worker processes for handling requests --
# a positive integer generally in the 2-4 * $NUM_CORES range. You may
# want to vary this a bit to find the best for your particular
# workload.
ENV GUNICORN_WORKERS=1

# Set this to the number of worker threads for handling
# requests. (Runs each worker with the specified number of threads.)
# This setting only affects the "gthread" and "sync" worker types.
ENV GUNICORN_THREADS=1
