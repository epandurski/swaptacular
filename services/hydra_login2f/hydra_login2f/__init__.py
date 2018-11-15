import logging
from flask import Flask, request, current_app
from flask_babel import Babel
from flask_migrate import Migrate
from .config import Configuration
from .models import db
from .emails import mail
from .redis import redis_store
from .routes import login, consent


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

babel = Babel()
migrate = Migrate()


@babel.localeselector
def select_locale():
    # Try to guess the language from the language cookie and the
    # accept header the browser transmits.
    language = request.cookies.get(current_app.config['LANGUAGE_COOKE_NAME'])
    language_choices = [l[0] for l in current_app.config['LANGUAGE_CHOICES']]
    if language in language_choices:
        return language
    return request.accept_languages.best_match(language_choices)


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
    app.register_blueprint(login, url_prefix=app.config['LOGIN_PATH'])
    app.register_blueprint(consent, url_prefix=app.config['CONSENT_PATH'])
    return app
