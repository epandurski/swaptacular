from urllib.parse import urljoin
from flask import request, redirect, url_for, flash, send_from_directory, render_template
from flask_babel import gettext
from flask_mail import Message
from sqlalchemy.exc import IntegrityError
from users import app, logger, redis_users, mail, captcha, db
from users.utils import is_invalid_email, generate_password_salt, calc_crypt_hash, generate_random_secret
from users.models import User


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
        # Verify captcha.
        if app.config['SHOW_CAPTCHA_ON_SIGNUP']:
            captcha_response = request.form.get(app.config['CAPTCHA_RESPONSE_FIELD_NAME'], '')
            captcha_solution = captcha.verify(captcha_response, request.remote_addr)
            captcha_passed = captcha_solution.is_valid
            captcha_error_message = captcha_solution.error_message
        else:
            captcha_passed = True
            captcha_error_message = None

        # Validate the submitted form.
        is_valid = False
        email = request.form['email']
        password = request.form['password']
        min_length = app.config['PASSWORD_MIN_LENGTH']
        max_length = app.config['PASSWORD_MAX_LENGTH']
        if is_invalid_email(email):
            flash(gettext('The email address is invalid.'))
        elif not captcha_passed:
            flash(captcha_error_message or gettext('Incorrect captcha solution.'))
        elif len(password) < min_length:
            flash(gettext('The password should have least %(num)s characters.', num=min_length))
        elif len(password) > max_length:
            flash(gettext('The password should have at most %(num)s characters.', num=max_length))
        elif password != request.form['confirm']:
            flash(gettext('Passwords do not match.'))
        else:
            is_valid = True

        # Send an email address verification message.
        if is_valid:
            if User.query.filter_by(email=email).one_or_none():
                site = app.config['SITE_TITLE']
                msg = Message(
                    subject=gettext('%(site)s: Duplicate registration', site=site),
                    recipients=[email],
                    body=render_template('signup_email_duplicate.txt', site=site, email=email),
                )
            else:
                secret = generate_random_secret()
                password_salt = generate_password_salt(app.config['PASSWORD_HASHING_METHOD'])
                password_hash = calc_crypt_hash(password_salt, password)
                register_link = urljoin(request.host_url, url_for('report_signup_success', secret=secret))
                key = 'signup:' + secret
                with redis_users.pipeline() as p:
                    p.hmset(key, {
                        'email': email,
                        'salt': password_salt,
                        'hash': password_hash,
                    })
                    p.expire(key, app.config['SIGNUP_REQUEST_EXPIRATION_SECONDS'])
                    p.execute()
                msg = Message(
                    subject=gettext('%(site)s: Please confirm your registration', site=app.config['SITE_TITLE']),
                    recipients=[email],
                    body=render_template('signup_email.txt', email=email, register_link=register_link),
                )
            mail.send(msg)
            return redirect(url_for('report_sent_signup_email', email=request.form['email']))

    return render_template('signup.html', display_captcha=captcha.display_html)


@app.route('/users/signup/email')
def report_sent_signup_email():
    email = request.args['email']
    return render_template('report_sent_signup_email.html', email=email)


@app.route('/users/register/<secret>')
def report_signup_success(secret):
    key = 'signup:' + secret
    email, salt, password_hash = redis_users.hmget(key, ['email', 'salt', 'hash'])
    if email:
        redis_users.delete(key)
        recovery_code = generate_random_secret()
        user = User(
            email=email,
            salt=salt,
            password_hash=password_hash,
            recovery_code_hash=calc_crypt_hash(salt, recovery_code),
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            pass
        else:
            return recovery_code
    return render_template('report_signup_expired.html')


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
