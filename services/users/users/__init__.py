import logging
import redis
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_babel import Babel, get_locale
from flask_mail import Mail
from users.config import Configuration


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.config.from_object(Configuration)


@app.after_request
def set_response_headers(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-cache'
    return response


@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)


babel = Babel(app)


@babel.localeselector
def select_locale():
    # Try to guess the language from the language cookie and the
    # accept header the browser transmits.
    lang = request.cookies.get(app.config['LANGUAGE_COOKE_NAME'])
    return lang or request.accept_languages.best_match(app.config['SUPPORTED_LANGUAGES'].keys())


@babel.timezoneselector
def select_timezone():
    return None


class CustomAlchemy(SQLAlchemy):
    def apply_driver_hacks(self, app, info, options):
        if "isolation_level" not in options:
            options["isolation_level"] = "REPEATABLE_READ"
        return super().apply_driver_hacks(app, info, options)


db = CustomAlchemy(app)
migrate = Migrate(app, db)


mail = Mail(app)


redis_users = redis.StrictRedis.from_url(
    app.config['REDIS_URL'],
    socket_timeout=5,
    charset="utf-8",
    decode_responses=True,
)


import users.models  # noqa: F401,E402
import users.routes  # noqa: F401,E402
