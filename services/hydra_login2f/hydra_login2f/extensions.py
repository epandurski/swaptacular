from flask_babel import Babel
from flask_migrate import Migrate
from .models import db
from .emails import mail
from .redis import redis_store

babel = Babel()
migrate = Migrate()


def init_app(app):
    db.init_app(app)
    babel.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    redis_store.init_app(app)
