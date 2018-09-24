import os
import re
import random
import string
import base64
from crypt import crypt


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
