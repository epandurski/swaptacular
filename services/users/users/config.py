from flask_env import MetaFlaskEnv


class Configuration(metaclass=MetaFlaskEnv):
    PORT = 8000
    SECRET_KEY = 'dummy-secret'

    HYDRA_ADMIN_URL = 'http://hydra:4445'
    SITE_TITLE = 'Swaptacular'
    USE_RECOVERY_CODE = True
    SHOW_CAPTCHA_ON_SIGNUP = True
    CAPTCHA_RESPONSE_FIELD_NAME = 'g-recaptcha-response'
    SIGNUP_REQUEST_EXPIRATION_SECONDS = 24 * 60 * 60
    LOGIN_VERIFICATION_CODE_EXPIRATION_SECONDS = 60 * 60
    SECRET_CODE_MAX_ATTEMPTS = 10
    HYDRA_REQUEST_TIMEOUT_SECONDS = 5
    LOGIN_VERIFIED_DEVICES_MAX_COUNT = 10

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
    COMPUTER_CODE_COOKE_NAME = 'users_cc'
    STYLE_URL = ''
    PASSWORD_HASHING_METHOD = '6'
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 64
    MESSAGE = 'Hello, World!'
