#!/bin/sh
set -e

# swpt_accounts
# -------------
#
# Everything published to the "accounts_in" exchange will be queued to
# the "swpt_accounts" queue, and processed by the swpt_accounts
# service. The service itself publishes to the "to_creditors",
# "to_debtors", and "to_coordinators" exchanges, depending on the
# intended receiver. All messages posted to these exchanges will be
# routed to either "creditors_in" or "debtors_in" exchanges.
rabbitmqadmin declare exchange name=accounts_in type=topic auto_delete=false durable=true internal=false
rabbitmqadmin declare exchange name=to_creditors type=topic auto_delete=false durable=true internal=false
rabbitmqadmin declare exchange name=to_debtors type=topic auto_delete=false durable=true internal=false
rabbitmqadmin declare exchange name=to_coordinators type=headers auto_delete=false durable=true internal=false
rabbitmqadmin declare queue name=swpt_accounts.XQ durable=true auto_delete=false\
 'arguments={"x-message-ttl":604800000}'
rabbitmqadmin declare queue name=swpt_accounts durable=true auto_delete=false\
 'arguments={"x-dead-letter-exchange":"", "x-dead-letter-routing-key":"swpt_accounts.XQ"}'

# swpt_creditors
# --------------
#
# Everything published to the "creditors_in" exchange will be queued
# to the "swpt_creditors" queue, and processed by the swpt_creditors
# service. The service itself publishes to the "creditors_out"
# exchange. All messages posted to this exchange will be routed to the
# "accounts_in" exchange.
rabbitmqadmin declare exchange name=creditors_in type=topic auto_delete=false durable=true internal=false
rabbitmqadmin declare exchange name=creditors_out type=topic auto_delete=false durable=true internal=false
rabbitmqadmin declare queue name=swpt_creditors.XQ durable=true auto_delete=false\
 'arguments={"x-message-ttl":604800000}'
rabbitmqadmin declare queue name=swpt_creditors durable=true auto_delete=false\
 'arguments={"x-dead-letter-exchange":"", "x-dead-letter-routing-key":"swpt_creditors.XQ"}'

# swpt_debtors
# ------------
#
# Everything published to the "debtors_in" exchange will be queued to
# the "swpt_debtors" queue, and processed by the swpt_debtors
# service. The service itself publishes to the "debtors_out"
# exchange. All messages posted to this exchange will be routed to the
# "accounts_in" exchange.
rabbitmqadmin declare exchange name=debtors_in type=topic auto_delete=false durable=true internal=false
rabbitmqadmin declare exchange name=debtors_out type=fanout auto_delete=false durable=true internal=false
rabbitmqadmin declare queue name=swpt_debtors.XQ durable=true auto_delete=false\
 'arguments={"x-message-ttl":604800000}'
rabbitmqadmin declare queue name=swpt_debtors durable=true auto_delete=false\
 'arguments={"x-dead-letter-exchange":"", "x-dead-letter-routing-key":"swpt_debtors.XQ"}'


# Declare the bindings that implement the logic described above.
rabbitmqadmin declare binding source="to_creditors" destination_type="exchange"\
 destination="creditors_in" routing_key="#"
rabbitmqadmin declare binding source="to_debtors" destination_type="exchange"\
 destination="debtors_in" routing_key="#"
rabbitmqadmin declare binding source="to_coordinators" destination_type="exchange"\
 destination="to_creditors" routing_key="" 'arguments={"x-match":"all","coordinator-type":"direct"}'
rabbitmqadmin declare binding source="to_coordinators" destination_type="exchange"\
 destination="to_debtors" routing_key="" 'arguments={"x-match":"all","coordinator-type":"issuing"}'
rabbitmqadmin declare binding source="creditors_out" destination_type="exchange"\
 destination="accounts_in" routing_key="#"
rabbitmqadmin declare binding source="debtors_out" destination_type="exchange"\
 destination="accounts_in" routing_key=""
rabbitmqadmin declare binding source="accounts_in" destination_type="queue"\
 destination="swpt_accounts" routing_key="#"
rabbitmqadmin declare binding source="creditors_in" destination_type="queue"\
 destination="swpt_creditors" routing_key="#"
rabbitmqadmin declare binding source="debtors_in" destination_type="queue"\
 destination="swpt_debtors" routing_key="#"
