# users

Handles sign up, sing in, and password recovery, manages user profile
info.


## How run a development server

```
$ docker-compose run -p 10001:10001 users develop
```


## How to debug

```
$ docker-compose run -p 10001:10001 users debug
```


## Hot to handle I18N messages

### Extract all messages to `messages.pot`:

```
$ pipenv run pybabel extract -F babel.cfg -o messages.pot .
```

or

```
$ pipenv run pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .
```

### Update all `.po` files from `messages.pot`

```
$ pipenv run pybabel update -i messages.pot -d translations
```

### Compile all `.po` files to `.mo` files

```
$ pipenv run pybabel compile -d translations
```

### Create translation for a new language:

```
pipenv run pybabel init -i messages.pot -d translations -l de
```
