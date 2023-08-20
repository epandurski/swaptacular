# Improve debtors agent

It is important debtors agents to be able to act as guarantors for some of
the currencies issued by the debtors they are responsible for. To do this,
they need to be able to limit the total amount that the debtors can issue in
circulation.

Also, it may be useful the debtor itself to be able to reliably limit the
amount that he/she can issue in circulation. This would prevent possible
race conditions between currency issuing transactions.

To allow both scenarios, the accounting authority should be updated to:

1. Treat the `negligible_amount` filed of debtor's account (creditor ID = 0)
   as a limit for the total issued amount. This can set by the debtors
   agents.

2. Add a new configuration field, applicable only to debtors' accounts,
   which also acts as a limit for the total issued amount. This can set by
   the debtor (the currency issuer).

In addition to that, the debtors agent's "Simple Issuing Web API" should be
expanded to allow the debtor to configure debtor's issuing limits. Most
probably, only the `superuser` should be allowed to do this, but the debtors
should be able to see the issuing limits assigned to them. Eventually, some
UI should be implemented, for configuring debtor's issuing limits.

**This has been done, except there is no UI yet for setting debtor's
issuing limits.**

# Allow creditors to check their balances directly with the accounting authority

To prevent creditors agents to secretly practice "fractional reserve
banking", creditors must be able to verify their balances directly with the
accounting authority.

To allow this the accounting authority should be updated to:

1. Implement a web server that creditors can send "GET" requests to, so as
   to obtain their current balances. The balance should be revealed only if
   the requester has the proper credentials.

2. Add a new field to the `AccountUpdate` message in the Swaptacular
   Messaging Protocol. This field should contain a randomly generated (by
   the accounting authority) secret, which will be required for directly
   obtaining the account balance (point 1).

   **Note:** This probably is not a good idea, because the secret will have
   to change periodically, to protect against accidentally lost secrets
   (over which the user has no control). These changes will need to happen
   periodically: either automatically (requiring periodical updates in the
   verifying app's database), or be triggered by a change in a configuration
   field (see point 3). Given that convenient use of a dedicated verifying
   app is a must (the app supplied by the creditors agent may not be
   trustworthy); and that it is impossible for the user to know when the
   secret has been lost; it seems that the approach in point 3 is the only
   viable one.

3. A new configuration field may be added as well, in which the owner of the
   account can provide an alternative identification method when obtaining
   the account balance. For example: a public key, a public key fingerprint,
   or a password hash.

# Central registry for accounting authorities

Debtor IDs are a global resource that should be managed transparently by a
central authority. The following things are needed:

1. A "single source of truth" defining the debtor IDs for well-known
   currencies, like USD, EUR, gold etc. (Those debtor IDs are in the
   interval 0 and 0xFFFFFFFF.)

2. A "single source of truth" mapping `accounting authority prefix` (a
   32-bit integer) to public key fingerprint.

3. A database with multiple "mirrors", that contain the latest info-bundle
   files for all Swaptacular network nodes. (Or at least for the accounting
   authorities).
