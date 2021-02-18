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
 Payments |                                          Issuing |
 Web API  |                                          Web API |
          |                                                  |
+-----------+          +----------------+          +-----------+
| Creditors |          |   Accounting   |          |  Debtors  |
|   Agent   |==========|   Authority    |==========|   Agent   |
+-----------+          +----------------+          +-----------+
                 Swaptacular Messaging Protocol
```

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


Sub-projects
------------

* [Service that manages user account balances](https://github.com/epandurski/swpt_accounts)
* [Service that manages debtors](https://github.com/epandurski/swpt_debtors)
* [Service that manages creditors](https://github.com/epandurski/swpt_creditors)
* [Service that manages OAuth2 login and consent](https://github.com/epandurski/swpt_login)
