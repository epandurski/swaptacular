import os
import re
import random
import string
import base64
import struct
import time
import hashlib
from urllib.parse import urljoin, quote_plus
from crypt import crypt
import requests
from sqlalchemy.exc import IntegrityError
from users import app, db, redis_users
from users.models import User, UserUpdateSignal


EMAIL_REGEX = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
PASSWORD_SALT_CHARS = string.digits + string.ascii_letters + './'
LOGIN_CODE_FAILURE_EXPIRATION_SECONDS = max(app.config['LOGIN_VERIFICATION_CODE_EXPIRATION_SECONDS'], 24 * 60 * 60)
HYDRA_CONSENTS_BASE_URL = urljoin(app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/sessions/consent/')
HYDRA_LOGINS_BASE_URL = urljoin(app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/sessions/login/')


def generate_random_secret(num_bytes=15):
    return base64.urlsafe_b64encode(os.urandom(num_bytes)).decode('ascii')


def generate_recovery_code(num_bytes=10):
    return base64.b32encode(os.urandom(num_bytes)).decode('ascii')


def normalize_recovery_code(recovery_code):
    return recovery_code.strip().replace(' ', '').replace('0', 'O').replace('1', 'I').upper()


def generate_verification_code(num_digits=6):
    assert 1 <= num_digits < 10
    random_number = struct.unpack('<L', os.urandom(4))[0] % (10 ** num_digits)
    return str(random_number).zfill(num_digits)


def generate_password_salt(method):
    salt = '$%s$' % method if method else ''
    salt += ''.join(random.choice(PASSWORD_SALT_CHARS) for _ in range(16))
    return salt


def format_recovery_code(recovery_code, block_size=4):
    if recovery_code is None:
        return ''
    N = block_size
    block_count = (len(recovery_code) + N - 1) // N
    blocks = [recovery_code[N * i:N * i + 4] for i in range(block_count)]
    return ' '.join(blocks)


def calc_crypt_hash(salt, message):
    return crypt(message, salt)


def is_invalid_email(email):
    if len(email) >= 255:
        return True
    return not EMAIL_REGEX.match(email)


def get_user_verification_code_failures_redis_key(user_id):
    return 'vcfails:' + str(user_id)


def clear_user_verification_code_failures(user_id):
    redis_users.delete(get_user_verification_code_failures_redis_key(user_id))


def register_user_verification_code_failure(user_id):
    key = get_user_verification_code_failures_redis_key(user_id)
    with redis_users.pipeline() as p:
        p.incrby(key)
        p.expire(key, LOGIN_CODE_FAILURE_EXPIRATION_SECONDS)
        num_failures = int(p.execute()[0] or '0')
    return num_failures


def get_hydra_subject(user_id):
    return str(user_id)


def invalidate_hydra_credentials(user_id):
    UserLoginsHistory(user_id).clear()
    subject = quote_plus(get_hydra_subject(user_id))
    timeout = app.config['HYDRA_REQUEST_TIMEOUT_SECONDS']
    requests.delete(HYDRA_CONSENTS_BASE_URL + subject, timeout=timeout)
    requests.delete(HYDRA_LOGINS_BASE_URL + subject, timeout=timeout)


class UserLoginsHistory:
    """Contain identification codes from the last logins of a given user."""

    REDIS_PREFIX = 'cc:'
    MAX_COUNT = app.config['LOGIN_VERIFIED_DEVICES_MAX_COUNT']

    def __init__(self, user_id):
        self.key = self.REDIS_PREFIX + str(user_id)

    @staticmethod
    def calc_hash(s):
        return hashlib.sha224(s.encode('ascii')).hexdigest()

    def contains(self, element):
        emement_hash = self.calc_hash(element)
        return emement_hash in redis_users.zrevrange(self.key, 0, self.MAX_COUNT - 1)

    def add(self, element):
        emement_hash = self.calc_hash(element)
        with redis_users.pipeline() as p:
            p.zremrangebyrank(self.key, 0, -self.MAX_COUNT)
            p.zadd(self.key, time.time(), emement_hash)
            p.execute()

    def clear(self):
        redis_users.delete(self.key)


class RedisSecretHashRecord:
    class ExceededMaxAttempts(Exception):
        """Too many failed attempts to enter the correct code."""

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

    def delete(self):
        redis_users.delete(self.key)

    def __getattr__(self, name):
        return self._data[name]


class LoginVerificationRequest(RedisSecretHashRecord):
    EXPIRATION_SECONDS = app.config['LOGIN_VERIFICATION_CODE_EXPIRATION_SECONDS']
    REDIS_PREFIX = 'vcode:'
    ENTRIES = ['user_id', 'code', 'challenge_id', 'email', 'remember_me']

    @classmethod
    def create(cls, **data):
        # We register a "code failure" after the creation of each
        # login verification request. This prevents maliciously
        # creating huge numbers of them.
        instance = super().create(**data)
        instance.register_code_failure()
        return instance

    def is_correct_recovery_code(self, recovery_code):
        user = User.query.filter_by(user_id=int(self.user_id)).one()
        normalized_recovery_code = normalize_recovery_code(recovery_code)
        return user.recovery_code_hash == calc_crypt_hash(user.salt, normalized_recovery_code)

    def register_code_failure(self):
        num_failures = register_user_verification_code_failure(self.user_id)
        if num_failures > app.config['SECRET_CODE_MAX_ATTEMPTS']:
            self.delete()
            raise self.ExceededMaxAttempts()

    def accept(self, clear_failures=False):
        if clear_failures:
            clear_user_verification_code_failures(self.user_id)
        self.delete()


class SignUpRequest(RedisSecretHashRecord):
    EXPIRATION_SECONDS = app.config['SIGNUP_REQUEST_EXPIRATION_SECONDS']
    REDIS_PREFIX = 'signup:'
    ENTRIES = ['email', 'cc', 'recover', 'has_rc']

    def is_correct_recovery_code(self, recovery_code):
        user = User.query.filter_by(email=self.email).one()
        normalized_recovery_code = normalize_recovery_code(recovery_code)
        return user.recovery_code_hash == calc_crypt_hash(user.salt, normalized_recovery_code)

    def register_code_failure(self):
        num_failures = int(redis_users.hincrby(self.key, 'fails'))
        if num_failures >= app.config['SECRET_CODE_MAX_ATTEMPTS']:
            self.delete()
            raise self.ExceededMaxAttempts()

    def accept(self, password):
        self.delete()
        if self.recover:
            recovery_code = None
            user = User.query.filter_by(email=self.email).one()
            user.password_hash = calc_crypt_hash(user.salt, password)

            # After changing the password, we "forget" past login
            # verification failures, thus guaranteeing that the user
            # will be able to log in immediately.
            clear_user_verification_code_failures(user.user_id)
        else:
            salt = generate_password_salt(app.config['PASSWORD_HASHING_METHOD'])
            if app.config['USE_RECOVERY_CODE']:
                recovery_code = generate_recovery_code()
                recovery_code_hash = calc_crypt_hash(salt, recovery_code)
            else:
                recovery_code = None
                recovery_code_hash = None
            user = User(
                email=self.email,
                salt=salt,
                password_hash=calc_crypt_hash(salt, password),
                recovery_code_hash=recovery_code_hash,
                two_factor_login=True,
            )
            db.session.add(user)
        db.session.commit()
        self.user_id = user.user_id
        return recovery_code


class ChangeEmailRequest(RedisSecretHashRecord):
    EXPIRATION_SECONDS = app.config['CHANGE_EMAIL_REQUEST_EXPIRATION_SECONDS']
    REDIS_PREFIX = 'setemail:'
    ENTRIES = ['email', 'old_email', 'user_id']

    class EmailAlredyRegistered(Exception):
        """The new email is already registered."""

    def accept(self):
        self.delete()
        user_id = int(self.user_id)
        user = User.query.filter_by(user_id=user_id, email=self.old_email).one()
        db.session.add(UserUpdateSignal(user_id=user_id, old_email=user.email, new_email=self.email))
        user.email = self.email
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise self.EmailAlredyRegistered()


class ChangeRecoveryCodeRequest(RedisSecretHashRecord):
    EXPIRATION_SECONDS = app.config['CHANGE_RECOVERY_CODE_REQUEST_EXPIRATION_SECONDS']
    REDIS_PREFIX = 'changerc:'
    ENTRIES = ['email']

    def accept(self):
        self.delete()
        recovery_code = generate_recovery_code()
        user = User.query.filter_by(email=self.email).one()
        user.recovery_code_hash = calc_crypt_hash(user.salt, recovery_code)
        db.session.commit()
        return recovery_code


class HydraLoginRequest:
    BASE_URL = urljoin(app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/requests/login/')
    TIMEOUT = app.config['HYDRA_REQUEST_TIMEOUT_SECONDS']
    REDIS_PREFIX = 'logins:'

    class TooManyLogins(Exception):
        """Too many login attempts."""

    def __init__(self, challenge_id):
        self.challenge_id = challenge_id
        self.request_url = self.BASE_URL + challenge_id

    def register_successful_login(self, subject):
        key = self.REDIS_PREFIX + subject
        if redis_users.ttl(key) < 0:
            redis_users.set(key, '1', ex=2600000)
            num_logins = 1
        else:
            num_logins = redis_users.incrby(key)
        if num_logins > app.config['MAX_LOGINS_PER_MONTH']:
            raise self.TooManyLogins()

    def fetch(self):
        """Return the subject if already logged, `None` otherwise."""

        r = requests.get(self.request_url, timeout=self.TIMEOUT)
        r.raise_for_status()
        fetched_data = r.json()
        return fetched_data['subject'] if fetched_data['skip'] else None

    def accept(self, subject, remember=False, remember_for=1000000000):
        """Accept the request unless the limit is reached, return an URL to redirect to."""

        try:
            self.register_successful_login(subject)
        except self.TooManyLogins:
            return self.reject()
        r = requests.put(self.request_url + '/accept', timeout=self.TIMEOUT, json={
            'subject': subject,
            'remember': remember,
            'remember_for': remember_for,
        })
        r.raise_for_status()
        return r.json()['redirect_to']

    def reject(self):
        """Reject the request, return an URL to redirect to."""

        r = requests.put(self.request_url + '/reject', timeout=self.TIMEOUT, json={
            'error': 'too_many_logins',
            'error_description': 'Too many login attempts have been made in a given period of time.',
            'error_hint': 'Try again later.',
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
