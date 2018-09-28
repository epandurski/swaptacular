from flask import render_template
from flask_babel import gettext
from flask_mail import Message
from users import app, mail


site = app.config['SITE_TITLE']


def send_duplicate_registration_email(email):
    msg = Message(
        subject=gettext('%(site)s: Duplicate registration', site=site),
        recipients=[email],
        body=render_template(
            'duplicate_registration.txt',
            email=email,
            site=site,
        ),
    )
    mail.send(msg)


def send_change_password_email(email, change_password_link):
    msg = Message(
        subject=gettext('%(site)s: Proceed with changing your password', site=site),
        recipients=[email],
        body=render_template(
            'change_password.txt',
            email=email,
            change_password_link=change_password_link,
        ),
    )
    mail.send(msg)


def send_confirm_registration_email(email, register_link):
    msg = Message(
        subject=gettext('%(site)s: Proceed with your registration', site=site),
        recipients=[email],
        body=render_template(
            'confirm_registration.txt',
            email=email,
            register_link=register_link,
        ),
    )
    mail.send(msg)


def send_verification_code_email(email, verification_code, change_password_page):
    msg = Message(
        subject=gettext('%(site)s: Login verification code', site=site),
        recipients=[email],
        body=render_template(
            'verification_code.txt',
            verification_code=verification_code,
            change_password_page=change_password_page,
        ),
    )
    mail.send(msg)
