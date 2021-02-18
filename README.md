Software for managing syndicated digital currencies
===================================================

TODO: Explain what it is.


Overal architecture
-------------------


```
+----------------+ +----------------+ +----------------+
|   Web-client   | |   Mobile app   | |  Desktop app   |
+----------------+ +----------------+ +----------------+

+------------------------------------------------------+
|                   Gateway Web API                    |
+------------------------------------------------------+

+----------------+ +----------------+ +----------------+
| Microservice 1 | | Microservice 2 | | Microservice 3 |
+----------------+ +----------------+ +----------------+

+------------------------------------------------------+
|                 Message Bus (RabbitMQ)               |
+------------------------------------------------------+
```


```
           +---------+   +---------+
           |Issuer X1|   |Issuer X2|
           +---------+   +---------+
                   |          |
                   |          |
                 +---------------+          +---------------+
                 |Debtors Agent X|          |Debtors Agent Y|
                 +---------------+          +---------------+
                             ||                ||
                             ||                ||
                           +----------------------+
                           |     Accounting       |
                           |     Authority 1      |
                           +----------------------+
         +---------+         ||                ||
         |Holder A1|         ||                ||
         +---------+         ||                ||
                 |           ||                ||
                 |           ||                ||
+---------+    +-----------------+          +-----------------+
|Holder A2|----|Creditors Agent A|          |Creditors Agent B|
+---------+    +-----------------+          +-----------------+
                 |           ||                ||
         Web API |           ||                ||
                 |           ||  Swaptacular   ||
         +---------+         ||   messaging    ||
         |Holder A3|         ||   protocol     ||
         +---------+         ||                ||
                             ||                ||
                           +----------------------+
                           |     Accounting       |
                           |     Authority 2      |
                           +----------------------+
```


Sub-projects
------------

* [Service that manages user account balances](https://github.com/epandurski/swpt_accounts)
* [Service that manages debtors](https://github.com/epandurski/swpt_debtors)
* [Service that manages creditors](https://github.com/epandurski/swpt_creditors)
* [Service that manages OAuth2 login and consent](https://github.com/epandurski/swpt_login)
