# coordinator

Orchestrates the circular trading among users.

It sends messages that invites given companies to send a list of trade
commitments. (A commitment is a (user_id, company_id, contract_id,
value) tuple that declares that a given user wants to buy a given
value of a given company contract.) The invitation messages contain a
`turn_id` and a `value_multiplier` which defines the value of the
"trading quantum".

After sending the invitations, the coordinator waits for some time
(one hour for example), and then begins to analyze the resulting
directed graph of commitments so as to find cycles. A "trading cycle
message" is send to the participating companies for each found trading
cycle.  When the analysis of the graph is done, a message is send to
all the companies to which invitation messages have been sent that
declares the trading turn closed.

Although this service do not need to have its own database, on restart
it should remember to close all trading turns.


