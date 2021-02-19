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
connect currency holders to many different *accounting authorities*
(this is true for debtors agents as well).

The following diagram tries to illustrate the connections that exist
between different the types of nodes:

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

Interoperability protocols
--------------------------

* [Swaptacular Messaging
  Protocol](https://github.com/epandurski/swpt_accounts/blob/master/protocol.rst)
  specification
* OpenAPI specification for the [Payments Web
  API](https://epandurski.github.io/swaptacular/swpt_creditors/redoc.html)
* OpenAPI specification for the [Issuing Web
  API](https://epandurski.github.io/swaptacular/swpt_debtors/redoc.html)


Reference implementations
-------------------------

* [Accounting Authority](https://github.com/epandurski/swpt_accounts)
* [Debtors Agent](https://github.com/epandurski/swpt_debtors)
* [Creditors Agent](https://github.com/epandurski/swpt_creditors)
* [Service that manages OAuth2 login and consent](https://github.com/epandurski/swpt_login)
