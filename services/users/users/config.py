from flask_env import MetaFlaskEnv


class Configuration(metaclass=MetaFlaskEnv):
    PORT = 8000
    SECRET_KEY = 'dummy-secret'
    SHOW_CAPTCHA_ON_SIGNUP = True
    CAPTCHA_RESPONSE_FIELD_NAME = 'g-recaptcha-response'

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

    RECAPTCHA_PUBLIC_KEY = '6Lc902MUAAAAAJL22lcbpY3fvg3j4LSERDDQYe37'
    RECAPTCHA_PIVATE_KEY = '6Lc902MUAAAAAN--r4vUr8Vr7MU1PF16D9k2Ds9Q'
    RECAPTCHA_CHALLENGE_URL = 'https://www.google.com/recaptcha/api.js'
    RECAPTCHA_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'

    SUPPORTED_LANGUAGES = {'en': 'English', 'bg': 'Български'}
    LANGUAGE_COOKE_NAME = 'users_lang'
    HTTP_HEAD_TITLE = 'Swaptacular'
    STYLE_URL = ''
    PASSWORD_HASHING_METHOD = '6'
    PASSWORD_MIN_LENGTH = 10
    PASSWORD_MAX_LENGTH = 64
    MESSAGE = 'Hello, World!'
