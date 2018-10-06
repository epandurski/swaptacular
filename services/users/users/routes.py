from urllib.parse import urljoin
from flask import request, redirect, url_for, flash, send_from_directory, render_template, abort, make_response
from flask_babel import gettext
import user_agents
from users import app, logger
from users import captcha
from users import emails
from users.models import User
from users.utils import (
    is_invalid_email, calc_crypt_hash, generate_random_secret, generate_verification_code,
    HydraLoginRequest, HydraConsentRequest, SignUpRequest, LoginVerificationRequest,
    UserLoginsHistory, ChangeEmailRequest, format_recovery_code,
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


def _get_change_email_address_link(change_email_request):
    return urljoin(request.host_url, url_for('change_email_address', secret=change_email_request.secret))


def _set_computer_code_cookie(response, computer_code):
    response.set_cookie(
        app.config['COMPUTER_CODE_COOKE_NAME'],
        computer_code,
        max_age=1000000000,
        httponly=True,
        secure=not app.config['DEBUG'],
    )


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


@app.route('/signup/language/<lang>')
def set_language(lang):
    response = redirect(request.args['to'])
    response.set_cookie(app.config['LANGUAGE_COOKE_NAME'], lang, max_age=1000000000)
    return response


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    email = request.args.get('email', '')
    is_new_user = 'recover' not in request.args
    if request.method == 'POST':
        captcha_passed, captcha_error_message = _verify_captcha(app.config['SHOW_CAPTCHA_ON_SIGNUP'])
        email = request.form['email'].strip()
        if is_invalid_email(email):
            flash(gettext('The email address is invalid.'))
        elif not captcha_passed:
            flash(captcha_error_message)
        else:
            computer_code = generate_random_secret()  # will be sent to the user as a login cookie
            user = User.query.filter_by(email=email).one_or_none()
            if user:
                if is_new_user:
                    emails.send_duplicate_registration_email(email)
                else:
                    r = SignUpRequest.create(
                        email=email,
                        cc=computer_code,
                        recover='yes',
                        has_rc='yes' if user.recovery_code_hash else 'no',
                    )
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
            _set_computer_code_cookie(response, computer_code)
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


@app.route('/signup/password/<secret>', methods=['GET', 'POST'])
def choose_password(secret):
    signup_request = SignUpRequest.from_secret(secret)
    if not signup_request:
        abort(404)
    is_password_recovery = signup_request.recover == 'yes'
    require_recovery_code = (is_password_recovery and
                             signup_request.has_rc == 'yes' and
                             app.config['USE_RECOVERY_CODE'])

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
        elif require_recovery_code and not signup_request.is_correct_recovery_code(recovery_code):
            try:
                signup_request.register_code_failure()
            except signup_request.ExceededMaxAttempts:
                abort(404)
            flash(gettext('Incorrect recovery code.'))
        else:
            new_recovery_code = signup_request.accept(password)
            UserLoginsHistory(signup_request.user_id).add(signup_request.cc)
            if is_password_recovery:
                return render_template(
                    'report_recovery_success.html',
                    email=signup_request.email,
                )
            else:
                response = make_response(render_template(
                    'report_signup_success.html',
                    email=signup_request.email,
                    recovery_code=format_recovery_code(new_recovery_code),
                ))
                response.headers['Cache-Control'] = 'no-store'
                return response

    return render_template('choose_password.html', require_recovery_code=require_recovery_code)


@app.route('/signup/choose-email/<secret>', methods=['GET', 'POST'])
def choose_new_email(secret):
    verification_request = LoginVerificationRequest.from_secret(secret)
    if not verification_request:
        abort(404)
    user = User.query.filter_by(user_id=int(verification_request.user_id)).one()
    require_recovery_code = user.recovery_code_hash and app.config['USE_RECOVERY_CODE']

    if request.method == 'POST':
        email = request.form['email'].strip()
        recovery_code = request.form.get('recovery_code', '')
        if is_invalid_email(email):
            flash(gettext('The email address is invalid.'))
        elif require_recovery_code and not verification_request.is_correct_recovery_code(recovery_code):
            try:
                verification_request.register_code_failure()
            except verification_request.ExceededMaxAttempts:
                abort(404)
            flash(gettext('Incorrect recovery code.'))
        else:
            verification_request.accept()
            r = ChangeEmailRequest.create(user_id=user.user_id, email=email)
            emails.send_change_email_address_email(email, _get_change_email_address_link(r))
            return redirect(url_for(
                'report_sent_email',
                email=email,
                login_challenge=request.args.get('login_challenge'),
            ))

    response = make_response(render_template('choose_new_email.html', require_recovery_code=require_recovery_code))
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.route('/signup/change-email/<secret>', methods=['GET'])
def change_email_address(secret):
    change_email_request = ChangeEmailRequest.from_secret(secret)
    if not change_email_request:
        abort(404)
    try:
        old_email = change_email_request.accept()
    except change_email_request.EmailAlredyRegistered:
        return redirect(url_for('report_email_change_failure', new_email=change_email_request.email))
    else:
        return redirect(url_for(
            'report_email_change_success',
            new_email=change_email_request.email,
            old_email=old_email,
        ))


@app.route('/signup/change-email-failure')
def report_email_change_failure():
    return render_template('report_email_change_failure.html', new_email=request.args['new_email'])


@app.route('/signup/change-email-success')
def report_email_change_success():
    return render_template(
        'report_email_change_success.html',
        old_email=request.args['old_email'],
        new_email=request.args['new_email'],
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_request = HydraLoginRequest(request.args['login_challenge'])
    subject = login_request.fetch()
    if subject:
        return redirect(login_request.accept(subject))

    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        user = User.query.filter_by(email=email).one_or_none()
        if user and user.password_hash == calc_crypt_hash(user.salt, password):
            user_id = user.user_id
            subject = 'user:{}'.format(user_id)
            if not user.two_factor_login:
                return redirect(login_request.accept(subject))

            # Two factor login: require a cookie containing a secret
            # "computer code" as well. The cookie proves that there
            # was a previous successful login attempt from this computer.
            computer_code = request.cookies.get(app.config['COMPUTER_CODE_COOKE_NAME'])
            if computer_code:
                user_logins_history = UserLoginsHistory(user_id)
                if user_logins_history.contains(computer_code):
                    user_logins_history.add(computer_code)
                    return redirect(login_request.accept(subject))

            # A two factor login verification code is required.
            verification_code = generate_verification_code()
            try:
                login_verification_request = LoginVerificationRequest.create(
                    user_id=user_id,
                    code=verification_code,
                    challenge_id=login_request.challenge_id,
                )
            except LoginVerificationRequest.ExceededMaxAttempts:
                abort(403)
            user_agent = str(user_agents.parse(request.headers.get('User-Agent', '')))
            change_password_page = urljoin(request.host_url, url_for('signup', email=email, recover='true'))
            emails.send_verification_code_email(email, verification_code, user_agent, change_password_page)
            response = redirect(url_for('enter_verification_code'))
            _set_computer_code_cookie(response, login_verification_request.secret)
            return response
        flash(gettext('Incorrect email or password.'))

    return render_template('login.html')


@app.route('/login/verify', methods=['GET', 'POST'])
def enter_verification_code():
    computer_code = request.cookies.get(app.config['COMPUTER_CODE_COOKE_NAME'], '*')
    verification_request = LoginVerificationRequest.from_secret(computer_code)
    if not verification_request:
        abort(403)

    if request.method == 'POST':
        if request.form['verification_code'].strip() == verification_request.code:
            login_request = HydraLoginRequest(verification_request.challenge_id)
            user_id = int(verification_request.user_id)
            subject = 'user:{}'.format(user_id)
            verification_request.accept()
            UserLoginsHistory(user_id).add(computer_code)
            return redirect(login_request.accept(subject))
        try:
            verification_request.register_code_failure()
        except verification_request.ExceededMaxAttempts:
            abort(403)
        flash(gettext('Invalid verification code.'))

    return render_template('enter_verification_code.html', computer_code=computer_code)


@app.route('/consent', methods=['GET', 'POST'])
def consent():
    consent_request = HydraConsentRequest(request.args['consent_challenge'])
    requested_scope = consent_request.fetch()
    if not requested_scope:
        return redirect(consent_request.accept(requested_scope))

    # TODO: show UI.
    return redirect(consent_request.accept(requested_scope))
