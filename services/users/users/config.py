from flask_env import MetaFlaskEnv


class Configuration(metaclass=MetaFlaskEnv):
    PORT = 8000
    SECRET_KEY = 'dummy-secret'

    REDIS_URL = 'redis://localhost:6379/0'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = ''

    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'

    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = None
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False

    SUPPORTED_LANGUAGES = {'en': 'English', 'bg': 'Български'}
    LANGUAGE_COOKE_NAME = 'users_lang'
    HTTP_HEAD_TITLE = 'Swaptacular'
    STYLE_URL = ''
    PASSWORD_MIN_LENGTH = 10
    PASSWORD_MAX_LENGTH = 64
    MESSAGE = 'Hello, World!'
