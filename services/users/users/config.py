from flask_env import MetaFlaskEnv
from os import environ


def _get_default_password_min_length(fallback):
    return 10 if environ.get('USE_RECOVERY_CODE', str(bool(fallback))).lower() == 'true' else 6


class Configuration(metaclass=MetaFlaskEnv):
    VERSION = '0.98.1'
    PORT = 8000
    SECRET_KEY = 'dummy-secret'
    HYDRA_ADMIN_URL = 'http://hydra:4445'
    SITE_TITLE = 'Swaptacular'
    USE_RECOVERY_CODE = True
    ABOUT_URL = 'https://github.com/epandurski'
    STYLE_URL = ''

    SHOW_CAPTCHA_ON_SIGNUP = True
    CAPTCHA_RESPONSE_FIELD_NAME = 'g-recaptcha-response'
    LOGIN_VERIFIED_DEVICES_MAX_COUNT = 10
    LOGIN_VERIFICATION_CODE_EXPIRATION_SECONDS = 60 * 60
    MAX_LOGINS_PER_MONTH = 10000
    SECRET_CODE_MAX_ATTEMPTS = 10
    SIGNUP_REQUEST_EXPIRATION_SECONDS = 24 * 60 * 60
    CHANGE_EMAIL_REQUEST_EXPIRATION_SECONDS = 24 * 60 * 60
    CHANGE_RECOVERY_CODE_REQUEST_EXPIRATION_SECONDS = 60 * 60
    HYDRA_REQUEST_TIMEOUT_SECONDS = 5

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
    LOGIN_VERIFICATION_COOKE_NAME = 'users_lv'
    PASSWORD_HASHING_METHOD = '6'
    PASSWORD_MIN_LENGTH = _get_default_password_min_length(USE_RECOVERY_CODE)
    PASSWORD_MAX_LENGTH = 64
    MESSAGE = 'Hello, World!'

    SEND_FILE_MAX_AGE_DEFAULT = 12096000
    MAX_CONTENT_LENGTH = 1024
