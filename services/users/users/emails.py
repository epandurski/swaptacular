from flask import render_template
from flask_babel import gettext
from flask_mail import Message
from users import app, mail


def send_duplicate_registration_email(email):
    msg = Message(
        subject=gettext('Duplicate Registration'),
        recipients=[email],
        body=render_template(
            'duplicate_registration.txt',
            email=email,
            site=app.config['SITE_TITLE'],
        ),
    )
    mail.send(msg)


def send_change_password_email(email, change_password_link):
    msg = Message(
        subject=gettext('Change Account Password'),
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
        subject=gettext('Create a New Account'),
        recipients=[email],
        body=render_template(
            'confirm_registration.txt',
            email=email,
            register_link=register_link,
        ),
    )
    mail.send(msg)


def send_verification_code_email(email, verification_code, user_agent, change_password_page):
    msg = Message(
        subject=gettext('New login from %(user_agent)s', user_agent=user_agent),
        recipients=[email],
        body=render_template(
            'verification_code.txt',
            verification_code=verification_code,
            user_agent=user_agent,
            change_password_page=change_password_page,
        ),
    )
    mail.send(msg)
