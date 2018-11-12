import logging
from flask import Flask, request, current_app
from flask_babel import Babel
from flask_migrate import Migrate
from .config import Configuration
from .models import db
from .emails import mail
from .redis import redis_store
from . import routes


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

babel = Babel()
migrate = Migrate()


@babel.localeselector
def select_locale():
    # Try to guess the language from the language cookie and the
    # accept header the browser transmits.
    lang = request.cookies.get(current_app.config['LANGUAGE_COOKE_NAME'])
    return lang or request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys())


@babel.timezoneselector
def select_timezone():
    return None


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Configuration)
    db.init_app(app)
    babel.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    redis_store.init_app(app)
    app.register_blueprint(routes.login, url_prefix=app.config['LOGIN_URL'])
    app.register_blueprint(routes.consent, url_prefix=app.config['CONSENT_URL'])
    return app
