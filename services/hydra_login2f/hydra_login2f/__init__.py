import logging
from flask import Flask
from .config import Configuration
from .routes import login, consent
from . import extensions

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Configuration)
    extensions.init_app(app)
    app.register_blueprint(login, url_prefix=app.config['LOGIN_PATH'])
    app.register_blueprint(consent, url_prefix=app.config['CONSENT_PATH'])
    return app
