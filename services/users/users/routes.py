from urllib.parse import urljoin
from flask import request, redirect, url_for, flash, send_from_directory, render_template, abort
from flask_babel import gettext
from users import app, logger, redis_users
from users import captcha
from users import emails
from users.models import User
from users.utils import (
    is_invalid_email, calc_crypt_hash, generate_random_secret,
    HydraLoginRequest, HydraConsentRequest, SignUpRequest, LoginVerificationRequest,
)


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


def _get_choose_password_link(signup_request):
    return urljoin(request.host_url, url_for('choose_password', secret=signup_request.secret))


@app.route('/users/hello_world')
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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    email = request.args.get('email', '')
    is_new_user = 'recover' not in request.args
    if request.method == 'POST':
        captcha_passed, captcha_error_message = _verify_captcha(app.config['SHOW_CAPTCHA_ON_SIGNUP'])
        email = request.form['email']
        if is_invalid_email(email):
            flash(gettext('The email address is invalid.'))
        elif not captcha_passed:
            flash(captcha_error_message)
        else:
            computer_code = generate_random_secret()  # to be sent to the user as a login cookie
            user = User.query.filter_by(email=email).one_or_none()
            if user:
                if is_new_user:
                    emails.send_duplicate_registration_email(email)
                else:
                    r = SignUpRequest.create(email=email, cc=computer_code, recover='yes')
                    emails.send_change_password_email(email, _get_choose_password_link(r))
            else:
                if is_new_user:
                    r = SignUpRequest.create(email=email, cc=computer_code)
                    emails.send_confirm_registration_email(email, _get_choose_password_link(r))
                else:
                    # We are asked to change the password of a non-existing user. In this case
                    # we fail silently, so as not to reveal if the email is registered or not.
                    pass
            response = redirect(url_for(
                'report_sent_email',
                email=email,
                login_challenge=request.args.get('login_challenge'),
            ))
            response.set_cookie(app.config['COMPUTER_CODE_COOKE_NAME'], computer_code)
            return response

    return render_template(
        'signup.html',
        email=email,
        is_new_user=is_new_user,
        display_captcha=captcha.display_html,
    )


@app.route('/signup/email')
def report_sent_email():
    email = request.args['email']
    return render_template('report_sent_email.html', email=email)


@app.route('/password/<secret>', methods=['GET', 'POST'])
def choose_password(secret):
    signup_request = SignUpRequest.from_secret(secret)
    if not signup_request:
        abort(404)
    require_recovery_code = signup_request.recover and app.config['USE_RECOVERY_CODE']

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
        elif require_recovery_code and not signup_request.verify_recovery_code(recovery_code):
            flash(gettext('Incorrect recovery code.'))
        else:
            recovery_code = signup_request.accept(password)
            redis_users.sadd('cc:' + str(signup_request.user_id), signup_request.cc)  # TODO: use a function
            return recovery_code or 'ok'

    return render_template('choose_password.html', require_recovery_code=require_recovery_code)


@app.route('/signup/success')
def report_signup_success():
    return "/signup/success"


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_request = HydraLoginRequest(request.args['login_challenge'])
    subject = login_request.fetch()
    if subject:
        return redirect(login_request.accept(subject))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).one_or_none()
        if user and user.password_hash == calc_crypt_hash(user.salt, password):
            user_id = user.user_id
            subject = 'user:{}'.format(user_id)
            computer_code = request.cookies.get(app.config['COMPUTER_CODE_COOKE_NAME'], '*')
            if redis_users.sismember('cc:' + str(user_id), computer_code):
                return redirect(login_request.accept(subject))
            else:
                verification_code = generate_random_secret(5)
                login_verification_request = LoginVerificationRequest.create(
                    user_id=user_id,
                    code=verification_code,
                    challenge_id=login_request.challenge_id,
                )
                change_password_page = urljoin(request.host_url, url_for('signup', email=email, recover='true'))
                emails.send_verification_code_email(email, verification_code, change_password_page)
                return redirect(
                    url_for('enter_verification_code',
                            secret=login_verification_request.secret,
                            login_challenge=login_request.challenge_id)
                )
        flash(gettext('Incorrect email or password.'))

    return render_template('login.html')


@app.route('/login/<secret>', methods=['GET', 'POST'])
def enter_verification_code(secret):
    verification_request = LoginVerificationRequest.from_secret(secret)
    if not verification_request:
        abort(404)

    if request.method == 'POST':
        if request.form['verification_code'] != verification_request.code:
            verification_request.register_code_failure()
            flash(gettext('Invalid verification code.'))
        else:
            user_id = int(verification_request.user_id)
            subject = 'user:{}'.format(user_id)
            computer_code = generate_random_secret()
            redis_users.sadd('cc:' + str(user_id), computer_code)  # TODO: use a function
            login_request = HydraLoginRequest(verification_request.challenge_id)
            response = redirect(login_request.accept(subject))
            response.set_cookie(app.config['COMPUTER_CODE_COOKE_NAME'], computer_code)
            return response

    return render_template('enter_verification_code.html')


@app.route('/consent', methods=['GET', 'POST'])
def consent():
    consent_request = HydraConsentRequest(request.args['consent_challenge'])
    requested_scope = consent_request.fetch()
    if not requested_scope:
        return redirect(consent_request.accept(requested_scope))

    # TODO: show UI.
    return redirect(consent_request.accept(requested_scope))
