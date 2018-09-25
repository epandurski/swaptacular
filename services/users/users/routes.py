from urllib.parse import urljoin
from flask import request, redirect, url_for, flash, send_from_directory, render_template, abort
from flask_babel import gettext
from flask_mail import Message
from users import app, logger, redis_users, mail, captcha, db
from users.utils import is_invalid_email, generate_password_salt, calc_crypt_hash, generate_random_secret
from users.models import User


def _verify_captcha(captcha_is_required):
    """Verify captcha if required."""

    if captcha_is_required:
        captcha_response = request.form.get(app.config['CAPTCHA_RESPONSE_FIELD_NAME'], '')
        captcha_solution = captcha.verify(captcha_response, request.remote_addr)
        captcha_passed = captcha_solution.is_valid
        captcha_error_message = captcha_solution.error_message
        if not captcha_passed and captcha_error_message is None:
            captcha_error_message = gettext('Incorrect captcha solution.')
    else:
        captcha_passed = True
        captcha_error_message = None
    return captcha_passed, captcha_error_message


def _verify_recovery_code(signup_key, email, recovery_code):
    """Verify if given recovery code is correct for given email."""

    user = User.query.filter_by(email=email).one_or_none()
    if user and user.recovery_code_hash == calc_crypt_hash(user.salt, recovery_code):
        return True
    num_failures = int(redis_users.hincrby(signup_key, 'fails'))
    if num_failures >= app.config['RECOVERY_CODE_MAX_ATTEMPTS']:
        redis_users.delete(signup_key)
        abort(403)
    return False


def _create_choose_password_link(email, computer_code, new_user):
    """Return a temporary link for email verification."""

    secret = generate_random_secret()
    signup_key = 'signup:' + secret
    with redis_users.pipeline() as p:
        p.hmset(signup_key, {
            'email': email,
            'cookie': computer_code,
        })
        if new_user:
            p.hset(signup_key, 'new', '1')
        p.expire(signup_key, app.config['SIGNUP_REQUEST_EXPIRATION_SECONDS'])
        p.execute()
    return urljoin(request.host_url, url_for('choose_password', secret=secret))


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
    is_new_user = 'recover' not in request.args
    page_head = gettext('Sign Up') if is_new_user else gettext('Recover Your Account')
    if request.method == 'POST':
        captcha_passed, captcha_error_message = _verify_captcha(app.config['SHOW_CAPTCHA_ON_SIGNUP'])
        email = request.form['email']
        if is_invalid_email(email):
            flash(gettext('The email address is invalid.'))
        elif not captcha_passed:
            flash(captcha_error_message)
        else:
            computer_code = generate_random_secret()  # to be sent to the user as a cookie
            site = app.config['SITE_TITLE']
            user = User.query.filter_by(email=email).one_or_none()
            if user:
                if is_new_user:
                    msg = Message(
                        subject=gettext('%(site)s: Duplicate registration', site=site),
                        recipients=[email],
                        body=render_template(
                            'duplicate_registration.txt',
                            email=email,
                            site=site,
                        ),
                    )
                else:
                    account_recovery_link = _create_choose_password_link(email, computer_code, new_user=False)
                    msg = Message(
                        subject=gettext('%(site)s: Please confirm your email address', site=site),
                        recipients=[email],
                        body=render_template(
                            'confirm_account_recovery.txt',
                            email=email,
                            account_recovery_link=account_recovery_link,
                        ),
                    )
                mail.send(msg)
            elif is_new_user:
                register_link = _create_choose_password_link(email, computer_code, new_user=True)
                msg = Message(
                    subject=gettext('%(site)s: Please confirm your registration', site=site),
                    recipients=[email],
                    body=render_template(
                        'confirm_registration.txt',
                        email=email,
                        register_link=register_link,
                    ),
                )
                mail.send(msg)
            response = redirect(url_for('report_sent_signup_email', email=email))
            response.set_cookie(app.config['COMPUTER_CODE_COOKE_NAME'], computer_code)
            return response

    return render_template('signup.html', page_head=page_head, display_captcha=captcha.display_html)


@app.route('/users/signup/email')
def report_sent_signup_email():
    email = request.args['email']
    return render_template('report_sent_signup_email.html', email=email)


@app.route('/users/password/<secret>', methods=['GET', 'POST'])
def choose_password(secret):
    signup_key = 'signup:' + secret
    email, cookie, is_new_user = redis_users.hmget(signup_key, ['email', 'cookie', 'new'])
    if email is None:
        abort(404)  # invalid registration link
    require_recovery_code = not is_new_user and app.config['USE_RECOVERY_CODE']

    if request.method == 'POST':
        recovery_code = request.form.get('recovery_code', '')
        password = request.form['password']
        min_length = app.config['PASSWORD_MIN_LENGTH']
        max_length = app.config['PASSWORD_MAX_LENGTH']
        if len(password) < min_length:
            flash(gettext('The password should have least %(num)s characters.', num=min_length))
        elif len(password) > max_length:
            flash(gettext('The password should have at most %(num)s characters.', num=max_length))
        elif password != request.form['confirm']:
            flash(gettext('Passwords do not match.'))
        elif require_recovery_code and not _verify_recovery_code(signup_key, email, recovery_code):
            flash(gettext('Incorrect recovery code.'))
        else:
            redis_users.delete(signup_key)
            if is_new_user:
                salt = generate_password_salt(app.config['PASSWORD_HASHING_METHOD'])
                recovery_code = generate_random_secret()
                user = User(
                    email=email,
                    salt=salt,
                    password_hash=calc_crypt_hash(salt, password),
                    recovery_code_hash=calc_crypt_hash(salt, recovery_code),
                )
                db.session.add(user)
                response = recovery_code
            else:
                user = User.query.filter_by(email=email).one()
                user.password_hash = calc_crypt_hash(user.salt, password)
                response = 'ok'
            db.session.commit()
            redis_users.zadd('cc:' + str(user.user_id), 1, cookie)  # TODO: use a function
            return response

    return render_template('choose_password.html', require_recovery_code=require_recovery_code)


@app.route('/users/signup/success')
def report_signup_success():
    return "/users/signup/success"


@app.route('/users/login')
def login():
    challenge = request.args['login_challenge']
    return render_template('login.html')


@app.route('/users/login/verification-code')
def enter_verification_code():
    return "/login/code"


@app.route('/users/recover-password/email')
def report_sent_recover_password_email():
    return "/users/recover-password/email"


@app.route('/users/choose-password/success')
def report_choose_password_success():
    return "/users/choose-password/success"
