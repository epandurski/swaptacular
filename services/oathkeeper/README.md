# hydra

Ory's "oathkeeper" proxy server.

## How to add a new rule

Add a new rule description file in `./rules`, then run:

```
$ docker-compose run oathkeeper-api rules import --endpoint http://oathkeeper-api:4456 /rules/filename.json
```
