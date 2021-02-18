Software for managing syndicated digital currencies
===================================================

TODO: Explain what it is.


Overal architecture
-------------------

```
+-----------+                                      +-----------+
| Currency  |                                      | Currency  |
|  Holder   |                                      |  Issuer   |
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
             +--------+    +--------+
             |Currency|    |Currency|
             | Issuer |    | Issuer |
             +--------+    +--------+
                    |           |
                    |  Web API  |
                    |           |
                  +---------------+          +---------------+
                  | Debtors Agent |          | Debtors Agent |
                  +---------------+          +---------------+
                              ||                ||
                              ||                ||
                              ||                ||
                            +----------------------+
                            |      Accounting      |
                            |      Authority       |
                            +----------------------+
          +--------+          ||                ||
          |Currency|          ||  Swaptacular   ||
          | Holder |          ||   Messaging    ||
          +--------+          ||   Protocol     ||
                 |            ||                ||
                 |            ||                ||
+--------+     +-----------------+            +-----------------+
|Currency|-----| Creditors Agent |            | Creditors Agent |
| Holder |     +-----------------+            +-----------------+
+--------+       |            ||                ||
                 |            ||                ||
         Web API |            ||                ||
                 |            ||                ||
          +--------+          ||                ||
          |Currency|        +----------------------+
          | Holder |        |      Accounting      |
          +--------+        |      Authority       |
                            +----------------------+
```


Sub-projects
------------

* [Service that manages user account balances](https://github.com/epandurski/swpt_accounts)
* [Service that manages debtors](https://github.com/epandurski/swpt_debtors)
* [Service that manages creditors](https://github.com/epandurski/swpt_creditors)
* [Service that manages OAuth2 login and consent](https://github.com/epandurski/swpt_login)
