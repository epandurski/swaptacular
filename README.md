Software for managing syndicated digital currencies
===================================================

Digital currencies are all around us. Nowadays, it is relatively easy
to become a holder of a digital currency, but it is not at all easy to
become an issuer of a digital currency. Swaptacular tries to make
creating and issuing new digital currencies possible for everyone. The
Swaptacular project consists of three things:

1. The overall network architecture
2. A set of interoperability protocols
3. Reference implementations for the interoperability protocols


The overal network architecture
-------------------------------

In Swaptacular's network architecture, there are five types of nodes:

1. **Accounting Authorities** manage user account balances. They form
   the backbone of the network.
2. **Currency Issuers** create currencies and issue money into
   existence. In Swaptacular, they are also called "debtors".
3. **Debtors Agents** are proxies that connect currency issuers to
   accounting authorities.
4. **Currency Holders** can make and receive payments. In Swaptacular,
   they are also called "creditors".
5. **Creditors Agents** are proxies that connect currency holders to
   accounting authorities.

```
+-----------+                                      +-----------+
| Currency  |                                      | Currency  |
|  Holder   |                                      |  Issuer   |
+-----------+                                      +-----------+
 Payments |                                          Issuing |
 Web API  |                                          Web API |
          |                                                  |
+-----------+          +----------------+          +-----------+
| Creditors |          |   Accounting   |          |  Debtors  |
|   Agent   |==========|   Authority    |==========|   Agent   |
+-----------+          +----------------+          +-----------+
                 Swaptacular Messaging Protocol
```

The diagram above shows the simplest possible Swaptacular
network. Real networks can consist of thousands of different
nodes. One important thing to note is that one *creditors agent* can
connect *currency holders* to many different *accounting authorities*
(the same is true for debtors agents). The following diagram tries to
illustrate the connections that exist between different types of
nodes:

```
                                          +--------+    +--------+
                                          |Currency|    |Currency|
                                          | Issuer |    | Issuer |
                                          +--------+    +--------+
                                                |  Issuing  |
                                                |  Web API  |
                                                |           |
                 +---------------+            +---------------+
                 |    Debtors    |            |    Debtors    |
                 |     Agent     |            |     Agent     |
                 +---------------+            +---------------+
                              ||                ||
                              ||                ||
                              ||                ||
                            +----------------------+
                            |      Accounting      |
                            |      Authority       |
          +--------+        +----------------------+
          |Currency|          ||                ||
          | Holder |          ||  Swaptacular   ||
          +--------+          ||   Messaging    ||
        Payments |            ||   Protocol     ||
        Web API  |            ||                ||
                 |            ||                ||
+--------+     +-----------------+            +-----------------+
|Currency|-----|    Creditors    |            |    Creditors    |
| Holder |     |      Agent      |            |      Agent      |
+--------+     +-----------------+            +-----------------+
                 |            ||                ||
                 |            ||                ||
          +--------+          ||                ||
          |Currency|          ||                ||
          | Holder |        +----------------------+
          +--------+        |      Accounting      |
                            |      Authority       |
                            +----------------------+
```

The above diagram shows a *creditors agent* that connects three
*currency holders* to two different *accounting authorities*. It also
shows two *debtors agents* being connected to the same accounting
authority.

Another important thing to note is that different network nodes
(accounting authorities, creditors agents, debtors agents) can be
operated by different organizations or individuals. Thus, very much
like Internet, Swaptacular's network is decentralized by its nature.


Interoperability protocols
--------------------------

At the core of Swaptacular's network architecture is the [Swaptacular
Messaging
Protocol](https://github.com/epandurski/swpt_accounts/blob/master/protocol.rst),
which governs the communication between accounting authorities and
debtors/creditors agents. The protocol uses a [two-phase
commit](https://en.wikipedia.org/wiki/Two-phase_commit_protocol)
schema, which allows for the implementation of currency exchanges in
the spirit of [Circular Multilateral
Barter](https://epandurski.github.io/swaptacular/cmb/cmb-general.pdf).

In order to allow currency holders to use a client application of
their choice, Swaptacular recommends the following OpenAPI
specification for the [Payments Web
API](https://epandurski.github.io/swaptacular/swpt_creditors/redoc.html).

Since interchangeability of client applications for currency issuing
is not of critical importance, Swaptacular does not make
recommendations about the *Issuing Web API*. The current reference
implementation uses a [Simple Issuing Web
API](https://epandurski.github.io/swaptacular/swpt_debtors/redoc.html).


Reference implementations
-------------------------

* [Accounting Authority](https://github.com/epandurski/swpt_accounts)
* [Debtors Agent](https://github.com/epandurski/swpt_debtors)
* [Creditors Agent](https://github.com/epandurski/swpt_creditors)
* [Service that manages OAuth2 login and consent](https://github.com/epandurski/swpt_login)
* [Currency Issuer UI](https://github.com/epandurski/swpt_debtors_ui)
* [Currency Holder UI](https://github.com/epandurski/swpt_creditors_ui)

All the above implementations try to:

1. Be correct.
2. Be as simple as possible.
3. Be useful in the real world.
4. Demonstrate that an implementation that does scale very well
   horizontally, is indeed possible.

A **fully functional demo deployment** from this source code
repository can be found here:
* [Currency Issuer UI](https://demo.swaptacular.org/debtors-webapp/)
* [Currency Holder UI](https://demo.swaptacular.org/creditors-webapp/)
* [Debtors Agent Swagger
  UI](https://demo.swaptacular.org/debtors-swagger-ui/) (client_id:
  `swagger-ui`, client_secret: `swagger-ui`)
* [Creditors Agent Swagger
  UI](https://demo.swaptacular.org/creditors-swagger-ui/) (client_id:
  `swagger-ui`, client_secret: `swagger-ui`)


Remaining work
--------------

- [x] Add link to a demo server, running the reference implementation.
- [x] Implement a user friendly UI for currency issuing.
- [x] Implement a user friendly UI for making and receiving payments.
- [ ] Define and implement a standard binary serialization for the
  messaging protocol (using [Cap'n Proto](https://capnproto.org/)).
- [ ] Allow creditors/debtors agents to easily connect to multiple
  accounting authorities, using user friendly UI and/or configuration
  files.
- [ ] Implement currency exchanges in the spirit of [Circular
      Multilateral
      Barter](https://epandurski.github.io/swaptacular/cmb/cmb-general.pdf).
