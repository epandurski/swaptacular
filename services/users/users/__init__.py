import logging
from flask import Flask
from flask import request, redirect, url_for, flash, send_from_directory
from flask import render_template
from flask_env import MetaFlaskEnv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_babel import Babel, gettext, get_locale
from users.utils import is_invalid_email


logging.basicConfig(level=logging.DEBUG)


class CustomAlchemy(SQLAlchemy):
    def apply_driver_hacks(self, app, info, options):
        if "isolation_level" not in options:
            options["isolation_level"] = "REPEATABLE_READ"
        return super().apply_driver_hacks(app, info, options)


class Configuration(metaclass=MetaFlaskEnv):
    PORT = 8000
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = ''
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


logger = logging.getLogger('users.%s' % __name__)
app = Flask(__name__)
app.config.from_object(Configuration)


babel = Babel(app)
db = CustomAlchemy(app)
migrate = Migrate(app, db)


@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)


@babel.localeselector
def select_locale():
    # Try to guess the language from the language cookie and the
    # accept header the browser transmits.
    lang = request.cookies.get(app.config['LANGUAGE_COOKE_NAME'])
    return lang or request.accept_languages.best_match(app.config['SUPPORTED_LANGUAGES'].keys())


@babel.timezoneselector
def select_timezone():
    return None


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


@app.route('/users/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@app.route('/users/language/<lang>')
def set_language(lang):
    response = redirect(request.args['to'])
    response.set_cookie(app.config['LANGUAGE_COOKE_NAME'], lang)
    return response


@app.route('/users/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        is_valid = False
        password_length = len(request.form['password'])
        min_length, max_length = app.config['PASSWORD_MIN_LENGTH'], app.config['PASSWORD_MAX_LENGTH']
        if is_invalid_email(request.form['email']):
            flash(gettext('The email address is invalid.'))
        elif password_length < min_length:
            flash(gettext('The password should have least %(num)s characters.', num=min_length))
        elif password_length > max_length:
            flash(gettext('The password should have at most %(num)s characters.', num=max_length))
        elif request.form['password'] != request.form['confirm']:
            flash(gettext('Passwords do not match.'))
        else:
            is_valid = True
        if is_valid:
            return redirect(url_for('report_sent_signup_email', email=request.form['email']))
    return render_template('signup.html')


@app.route('/users/signup/email')
def report_sent_signup_email():
    email = request.args['email']
    return render_template('report_sent_signup_email.html', email=email)


@app.route('/users/signup/success/<secret>')
def report_signup_success(secret):
    return "/users/signup/success/{}".format(secret)


@app.route('/users/login')
def login():
    challenge = request.args['login_challenge']
    return render_template('login.html')


@app.route('/users/login/verification-code')
def enter_verification_code():
    return "/login/code"


@app.route('/users/recover-password')
def recover_password():
    return "/users/recover-password"


@app.route('/users/recover-password/email')
def report_sent_recover_password_email():
    return "/users/recover-password/email"


@app.route('/users/choose-password/<secret>')
def choose_password(secret):
    return "/users/choose-password/{}".format(secret)


@app.route('/users/choose-password/success')
def report_choose_password_success():
    return "/users/choose-password/success"


if __name__ == '__main__':
    from pudb import set_trace
    set_trace(paused=False)
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=True, use_reloader=False, threaded=False)
