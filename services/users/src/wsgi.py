from flask import Flask
from flask_env import MetaFlaskEnv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


class Configuration(metaclass=MetaFlaskEnv):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = ''
    MESSAGE = 'Hello, World!'


app = Flask(__name__)
app.config.from_object(Configuration)


db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)


@app.route('/')
def hello_world():
    return app.config['MESSAGE']


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False, threaded=False)
