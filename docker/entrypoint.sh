#!/bin/sh
set -e

# During development, we should be able to connect to services
# installed on "localhost" from the container. To allow this, we find
# the IP address of the docker host, and then for each variable name
# $SUBSTITUTE_LOCALHOST_IN_VARS, we substitute "localhost" with that
# IP address.
host_ip=$(ip route show | awk '/default/ {print $3}')
for envvar_name in $SUBSTITUTE_LOCALHOST_IN_VARS; do
    eval envvar_value=\$$envvar_name
    if [[ -n "$envvar_value" ]]; then
        eval export $envvar_name=$(echo "$envvar_value" | sed -E "s/(.*@|.*\/\/)localhost\b/\1$host_ip/")
    fi
done

# The WEBSERVER_* variables should be used instead of the GUNICORN_*
# variables, because we do not want to tie the public interface to the
# "gunicorn" server, which we may, or may not use in the future.
export GUNICORN_WORKERS=${WEBSERVER_WORKERS:-1}
export GUNICORN_THREADS=${WEBSERVER_THREADS:-3}

# This function tries to upgrade the database schema with exponential
# backoff. This is necessary during development, because the database
# might not be running yet when this script executes.
perform_db_upgrade() {
    local retry_after=1
    local time_limit=$(($retry_after << 5))
    local error_file="$APP_ROOT_DIR/flask-db-upgrade.error"
    echo -n 'Running database schema upgrade ...'
    while [[ $retry_after -lt $time_limit ]]; do
        if flask db upgrade &>$error_file; then
            perform_db_initialization
            echo ' done.'
            return 0
        fi
        sleep $retry_after
        retry_after=$((2 * retry_after))
    done
    echo
    cat "$error_file"
    return 1
}

# This function tries to set up the needed RabbitMQ objects (queues,
# exchanges, bindings) with exponential backoff. This is necessary
# during development, because the RabbitMQ server might not be running
# yet when this script executes.
setup_rabbitmq_bindings() {
    local retry_after=1
    local time_limit=$(($retry_after << 5))
    local error_file="$APP_ROOT_DIR/flask-db-upgrade.error"
    echo -n 'Setting up message broker objects ...'
    while [[ $retry_after -lt $time_limit ]]; do
        if flask swpt_accounts subscribe swpt_accounts &>$error_file; then
            echo ' done.'
            return 0
        fi
        sleep $retry_after
        retry_after=$((2 * retry_after))
    done
    echo
    cat "$error_file"
    return 1
}

# This function is intended to perform additional one-time database
# initialization. Make sure that it is idempotent.
# (https://en.wikipedia.org/wiki/Idempotence)
perform_db_initialization() {
    return 0
}

case $1 in
    develop-run-flask)
        shift
        exec flask run --host=0.0.0.0 --port $PORT --without-threads "$@"
        ;;
    test)
        perform_db_upgrade
        exec pytest
        ;;
    configure)
        perform_db_upgrade
        setup_rabbitmq_bindings
        ;;
    webserver)
        exec gunicorn --config "$APP_ROOT_DIR/gunicorn.conf.py" -b :$PORT wsgi:app
        ;;
    protocol)
        exec dramatiq --processes ${PROTOCOL_PROCESSES-1} --threads ${PROTOCOL_THREADS-3} tasks:protocol_broker
        ;;
    process_chores)
        exec dramatiq --processes ${CHORES_PROCESSES-1} --threads ${CHORES_THREADS-3} tasks:chores_broker
        ;;
    process_balance_changes |process_transfer_requests | process_finalization_requests | scan_accounts \
        | scan_prepared_transfers | scan_registered_balance_changes)
        exec flask swpt_accounts "$@"
        ;;
    flush_rejected_transfers | flush_prepared_transfers | flush_finalized_transfers \
        | flush_account_transfers | flush_account_updates | flush_account_purges \
        | flush_rejected_configs | flush_pending_balance_changes)

        flush_rejected_transfers=RejectedTransferSignal
        flush_prepared_transfers=PreparedTransferSignal
        flush_finalized_transfers=FinalizedTransferSignal
        flush_account_transfers=AccountTransferSignal
        flush_account_updates=AccountUpdateSignal
        flush_account_purges=AccountPurgeSignal
        flush_rejected_configs=RejectedConfigSignal
        flush_pending_balance_changes=PendingBalanceChangeSignal

        # For example: if `$1` is "flush_rejected_transfers",
        # `signal_name` will be "RejectedTransferSignal".
        eval signal_name=\$$1

        # For example: if `$1` is "flush_rejected_transfers", `wait`
        # will get the value of the APP_FLUSH_REJECTED_TRANSFERS_WAIT
        # environment variable, defaulting to 5 if it is not defined.
        eval wait=\${APP_$(echo "$1" | tr [:lower:] [:upper:])_WAIT-5}

        exec flask signalbus flushmany --repeat=$wait $signal_name
        ;;
    all)
        # Spawns all the necessary processes in one container.
        exec supervisord -c "$APP_ROOT_DIR/supervisord.conf"
        ;;
    *)
        exec "$@"
        ;;
esac
