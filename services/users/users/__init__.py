import logging
from flask import Flask, request
from flask_env import MetaFlaskEnv
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from flask_migrate import Migrate
from flask_babel import Babel, get_locale


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Configuration(metaclass=MetaFlaskEnv):
    PORT = 8000
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = ''
    REDIS_URL = 'redis://localhost:6379/0'
    SECRET_KEY = 'dummy-secret'
    SUPPORTED_LANGUAGES = {'en': 'English', 'bg': 'Български'}
    LANGUAGE_COOKE_NAME = 'users_lang'
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    HTTP_HEAD_TITLE = 'Swaptacular'
    STYLE_URL = ''
    PASSWORD_MIN_LENGTH = 10
    PASSWORD_MAX_LENGTH = 64
    MESSAGE = 'Hello, World!'


app = Flask(__name__)
app.config.from_object(Configuration)


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


redis_users = FlaskRedis(app)


import users.models  # noqa: F401,E402
import users.routes  # noqa: F401,E402
