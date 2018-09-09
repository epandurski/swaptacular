# hydra

Ory's "hydra" Oauth2 authentication server.

## How to add a new client

Add a new client description file in `./clients`, then run:

```
$ docker-compose run hydra clients import /clients/filename.json
```
