import os
import re
import random
import string
import base64
from urllib.parse import urljoin
from crypt import crypt
import requests
from flask import abort
from users import app, db, redis_users
from users.models import User


EMAIL_REGEX = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
PASSWORD_SALT_CHARS = string.digits + string.ascii_letters + './'


def generate_random_secret(num_bytes=15):
    return base64.urlsafe_b64encode(os.urandom(num_bytes)).decode('ascii')


def generate_password_salt(method):
    salt = '$%s$' % method if method else ''
    salt += ''.join(random.choice(PASSWORD_SALT_CHARS) for _ in range(16))
    return salt


def calc_crypt_hash(salt, message):
    return crypt(message, salt)


def is_invalid_email(email):
    return not EMAIL_REGEX.match(email)


class RedisSecretHashRecord:
    @property
    def key(self):
        return self.REDIS_PREFIX + self.secret

    @classmethod
    def create(cls, **data):
        instance = cls()
        instance.secret = generate_random_secret()
        instance._data = data
        with redis_users.pipeline() as p:
            p.hmset(instance.key, data)
            p.expire(instance.key, cls.EXPIRATION_SECONDS)
            p.execute()
        return instance

    @classmethod
    def from_secret(cls, secret):
        instance = cls()
        instance.secret = secret
        instance._data = dict(zip(cls.ENTRIES, redis_users.hmget(instance.key, cls.ENTRIES)))
        return instance if instance._data.get(cls.ENTRIES[0]) is not None else None

    def register_code_failure(self):
        num_failures = int(redis_users.hincrby(self.key, 'fails'))
        if num_failures >= app.config['SECRET_CODE_MAX_ATTEMPTS']:
            self._delete()
            abort(403)

    def __getattr__(self, name):
        return self._data[name]

    def _delete(self):
        redis_users.delete(self.key)


class LoginVerificationRequest(RedisSecretHashRecord):
    EXPIRATION_SECONDS = app.config['LOGIN_VERIFICATION_CODE_EXPIRATION_SECONDS']
    REDIS_PREFIX = 'vcode:'
    ENTRIES = ['user_id', 'code', 'challenge_id']


class SignUpRequest(RedisSecretHashRecord):
    EXPIRATION_SECONDS = app.config['SIGNUP_REQUEST_EXPIRATION_SECONDS']
    REDIS_PREFIX = 'signup:'
    ENTRIES = ['email', 'cc', 'recover']

    def verify_recovery_code(self, recovery_code):
        user = User.query.filter_by(email=self.email).one_or_none()
        if user and user.recovery_code_hash == calc_crypt_hash(user.salt, recovery_code):
            return True
        self.register_code_failure()
        return False

    def accept(self, password):
        self._delete()
        if self.recover:
            recovery_code = None
            user = User.query.filter_by(email=self.email).one()
            user.password_hash = calc_crypt_hash(user.salt, password)
        else:
            recovery_code = generate_random_secret()
            salt = generate_password_salt(app.config['PASSWORD_HASHING_METHOD'])
            user = User(
                email=self.email,
                salt=salt,
                password_hash=calc_crypt_hash(salt, password),
                recovery_code_hash=calc_crypt_hash(salt, recovery_code),
            )
            db.session.add(user)
        db.session.commit()
        self.user_id = user.user_id
        return recovery_code


class HydraLoginRequest:
    BASE_URL = urljoin(app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/requests/login/')
    TIMEOUT = app.config['HYDRA_REQUEST_TIMEOUT_SECONDS']

    def __init__(self, challenge_id):
        self.challenge_id = challenge_id
        self.request_url = self.BASE_URL + challenge_id

    def fetch(self):
        """Return the subject if already logged, `None` otherwise."""

        r = requests.get(self.request_url, timeout=self.TIMEOUT)
        r.raise_for_status()
        fetched_data = r.json()
        return fetched_data['subject'] if fetched_data['skip'] else None

    def accept(self, subject, remember=False, remember_for=0):
        """Approve the request, return an URL to redirect to."""

        r = requests.put(self.request_url + '/accept', timeout=self.TIMEOUT, json={
            'subject': subject,
            'remember': remember,
            'remember_for': remember_for,
        })
        r.raise_for_status()
        return r.json()['redirect_to']


class HydraConsentRequest:
    BASE_URL = urljoin(app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/requests/consent/')
    TIMEOUT = app.config['HYDRA_REQUEST_TIMEOUT_SECONDS']

    def __init__(self, challenge_id):
        self.challenge_id = challenge_id
        self.request_url = self.BASE_URL + challenge_id

    def fetch(self):
        """Return the list of requested scopes, or an empty list if no consent is required."""

        r = requests.get(self.request_url, timeout=self.TIMEOUT)
        r.raise_for_status()
        fetched_data = r.json()
        return [] if fetched_data['skip'] else fetched_data['requested_scope']

    def accept(self, grant_scope, remember=False, remember_for=0):
        """Approve the request, return an URL to redirect to."""

        r = requests.put(self.request_url + '/accept', timeout=self.TIMEOUT, json={
            'grant_scope': grant_scope,
            'remember': remember,
            'remember_for': remember_for,
        })
        r.raise_for_status()
        return r.json()['redirect_to']
