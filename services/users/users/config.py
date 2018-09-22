from flask_env import MetaFlaskEnv


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
