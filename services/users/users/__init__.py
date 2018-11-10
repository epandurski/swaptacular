import logging
from flask import Flask
from .config import Configuration
from . import models, emails, redis, routes


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Configuration)
    models.init_app(app)
    emails.init_app(app)
    redis.init_app(app)
    routes.init_app(app)
    return app
