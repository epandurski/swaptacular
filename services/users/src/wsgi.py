import logging
from flask import Flask
from flask import request
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
    PORT = 80
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = ''
    MESSAGE = 'Hello, World!'


logger = logging.getLogger('users.%s' % __name__)
app = Flask(__name__)
app.config.from_object(Configuration)


db = CustomAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    user_id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    password_salt = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    recovery_code_hash = db.Column(db.Text, nullable=False)


@app.route('/users/')
def hello_world():
    logger.debug('A debug message')
    logger.info('An info message')
    logger.warning('A warning message')
    body = app.config['MESSAGE'] + '\n\n' + '\n'.join('{}: {}'.format(*h) for h in request.headers)
    return body, 200, {'Content-Type': 'text/plain; charset=utf-8'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=True, use_reloader=False, threaded=False)
