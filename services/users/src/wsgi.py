import logging
from flask import Flask
from flask_env import MetaFlaskEnv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


logging.basicConfig(level=logging.DEBUG)


class CustomAlchemy(SQLAlchemy):
    def apply_driver_hacks(self, app, info, options):
        if "isolation_level" not in options:
            options["isolation_level"] = "REPEATABLE_READ"
        return super().apply_driver_hacks(app, info, options)


class Configuration(metaclass=MetaFlaskEnv):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = ''
    MESSAGE = 'Hello, World!'


logger = logging.getLogger('users.%s' % __name__)
app = Flask(__name__)
app.config.from_object(Configuration)


db = CustomAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)


@app.route('/')
def hello_world():
    logger.debug('A debug message')
    logger.info('An info message')
    logger.warning('A warning message')
    return app.config['MESSAGE']


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False, threaded=False)
