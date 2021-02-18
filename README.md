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

Related documents
-----------------

* OpenAPI specication for the [Payments Web
  API](https://epandurski.github.io/swaptacular/swpt_creditors/redoc.html)
* OpenAPI specication for the [Issuing Web
  API](https://epandurski.github.io/swaptacular/swpt_debtors/redoc.html)


Sub-projects
------------

* [Accounting Authority](https://github.com/epandurski/swpt_accounts)
* [Debtors Agent](https://github.com/epandurski/swpt_debtors)
* [Creditors Agent](https://github.com/epandurski/swpt_creditors)
* [Service that manages OAuth2 login and consent](https://github.com/epandurski/swpt_login)
