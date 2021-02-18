Software for managing syndicated digital currencies
===================================================

TODO: Explain what it is.


Overal architecture
-------------------

```
+-----------+                                      +-----------+
| Currency  |                                      | Currency  |
| Holders   |                                      | Issuers   |
+-----------+                                      +-----------+
(order payments)                                   (create money)

+-----------+          +----------------+          +-----------+
|  Web API  |          |                |          |  Web API  |
+-----------+          |   Accounting   |          +-----------+
| Creditors |<-------->|   Authority    |<-------->|  Debtors  |
|   Agent   |          |                |          |   Agent   |
+-----------+          +----------------+          +-----------+
+--------------------------------------------------------------+
|                Swaptacular Messaging Protocol                |
+--------------------------------------------------------------+
```

```
             +--------+   +--------+
             |Currency|   |Currency|
             | Issuer |   | Issuer |
             +--------+   +--------+
                    |          |
                    | Web API  |
                +-----------------+          +-----------------+
                | Debtors Agent X |          | Debtors Agent Y |
                +-----------------+          +-----------------+
                              ||                ||
                              ||                ||
                              ||                ||
                            +----------------------+
                            |     Accounting       |
                            |     Authority 1      |
                            +----------------------+
          +--------+          ||                ||
          |Currency|          ||                ||
          | Holder |          ||  Swaptacular   ||
          +--------+          ||   Messaging    ||
                 |            ||   Protocol     ||
                 |            ||                ||
+--------+     +-------------------+        +-------------------+
|Currency|-----| Creditors Agent A |        | Creditors Agent B |
| Holder |     +-------------------+        +-------------------+
+--------+       |            ||                ||
                 |            ||                ||
         Web API |            ||                ||
                 |            ||                ||
          +--------+          ||                ||
          |Currency|        +----------------------+
          | Holder |        |     Accounting       |
          +--------+        |     Authority 2      |
                            +----------------------+

```


Sub-projects
------------

* [Service that manages user account balances](https://github.com/epandurski/swpt_accounts)
* [Service that manages debtors](https://github.com/epandurski/swpt_debtors)
* [Service that manages creditors](https://github.com/epandurski/swpt_creditors)
* [Service that manages OAuth2 login and consent](https://github.com/epandurski/swpt_login)
